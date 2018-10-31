"""
synapse-room-logger : a simple tool to export your Matrix rooms history to
plain-text logs.

Usage:
    roomlogger cron [options]
    roomlogger daemon [options]

Options:
    --help          This helper
    --debug         Increase verbosity
"""

from docopt import docopt
import psycopg2
import yaml
import logging
import json
from datetime import datetime
from time import sleep
from sys import exit


class SynapseRoomLogger(object):
    """
        Everything the tool will run is wrapped in this object.
    """

    def __init__(self, config):
        self.rooms = config["rooms"]
        self.db_config = {
            "host": config["db_host"],
            "database": config["db_name"],
            "user": config["db_user"],
            "password": config["db_password"],
            "connect_timeout": 5,
        }
        self.output_directory = config["output_directory"]
        self.daemon_interval = config["daemon_interval"]
        state_file_name = ".last_ts"
        self.state_file_path = "{}/{}".format(
            config["output_directory"], state_file_name
        )

    def process_message_row(self, message_row):
        """
            Filter a row returned by the query, keeping and converting only the
            needed informations.
            Takes a 2-items list as parameter, returns a dict.
        """
        msg_received_ts = message_row[0]
        msg_raw_data = json.loads(message_row[1])
        msg_data = {
            "ts": msg_received_ts,
            "origin_ts": msg_raw_data["origin_server_ts"],
            "origin": msg_raw_data["origin"],
            "sender": msg_raw_data["sender"],
            "event_id": msg_raw_data["event_id"],
            "room_id": msg_raw_data["room_id"],
            "message": msg_raw_data["content"]["body"],
            "url": msg_raw_data["content"].get("url", None),
        }
        return msg_data

    def ts_to_filepath(self, timestamp, room_name):
        """
            Creates a filepath from timestamp and room name.
            (all logs are written in one file per day)
        """
        path = "{output_directory}/{room_name}_{date}.log"
        # synapse timestamps are in milliseconds
        date = datetime.utcfromtimestamp(timestamp / 1000).strftime("%Y%m%d")
        return path.format(
            output_directory=self.output_directory, room_name=room_name, date=date
        )

    def append_line(self, file_path, line):
        """
            Append a line to a file, creating it if doesn't exist.
            Returns True if the write went well, False in the other case.
        """
        try:
            with open(file_path, "a") as file:
                file.write(line + "\n")
                return True
        except FileNotFoundError:
            logging.error(
                "Could not write {}, maybe the parent directory is missing.".format(
                    file_path
                )
            )
            return False
        except PermissionError:
            logging.error(
                "Could not write {}, you don't have sufficient permissions to write here.".format(
                    file_path
                )
            )
            return False

    def read_last_ts_written(self):
        """
           Read the timestamp of the last record written from the state file,
           and set the corresponding attribute.
           Return True if ok, False if not.
        """
        try:
            logging.info("Reading last timestamp written from previous run.")
            with open(self.state_file_path, "r") as file:
                self.last_ts_written = int(file.read())
                logging.info(
                    "Last timestamp from previous run is {}.".format(
                        self.last_ts_written
                    )
                )
                return True
        except FileNotFoundError:
            self.last_ts_written = 0
            logging.warning(
                "No state file found at {}, setting last timestamp written to 0.".format(
                    self.state_file_path
                )
            )
            return False

    def write_last_ts_written(self):
        """
           Write the timestamp of the last record written to the state file.
           Return True if ok, False if not.
        """
        try:
            logging.info("Writing last timestamp to state file.")
            with open(self.state_file_path, "w") as file:
                file.write(str(self.last_ts_written))
                logging.info(
                    "Timestamp {} written to state file.".format(self.last_ts_written)
                )
                return True
        except FileNotFoundError:
            logging.error(
                "Could not write {}, maybe the parent directory is missing.".format(
                    file_path
                )
            )
            return False
        except PermissionError:
            logging.error(
                "Could not write {}, you don't have sufficient permissions to write here.".format(
                    file_path
                )
            )
            return False

    def request_messages(self):
        """
            The main method, here we launch the database connection, query the
            DB and write the files, then disconnects.
            Returns True if successful, False if not.
        """
        # we fetch messages from all rooms at the same time, we will route them at writing time
        base_query = (
            "SELECT e.received_ts, j.json "
            "FROM events AS e "
            "INNER JOIN event_json AS j "
            "USING (event_id) "
            "WHERE e.room_id IN %s "
            "AND e.received_ts>%s "
            "AND e.type='m.room.message' "
            "ORDER BY e.received_ts;"
        )

        self.read_last_ts_written()

        try:
            logging.info("Connecting to database ...")
            with psycopg2.connect(**self.db_config) as conn:
                logging.info("Connected to database.")
                with conn.cursor() as cur:
                    cur.execute(
                        base_query, (tuple(self.rooms.keys()), self.last_ts_written)
                    )

                    for row in cur:
                        # there are two fields per row : timestamp at reception, and json data
                        line = self.process_message_row(row)

                        # we get the room nickname in the config at the room_id key
                        room_name = self.rooms[line["room_id"]]
                        file_path = self.ts_to_filepath(
                            timestamp=line["ts"], room_name=room_name
                        )

                        if self.append_line(file_path, json.dumps(line)):
                            logging.info(
                                "Message with timestamp {} written to {}".format(
                                    line["ts"], file_path
                                )
                            )
                            self.last_ts_written = line["ts"]
                        else:
                            logging.error(
                                "We couldn't write message {}, we will exit.".format(
                                    line["ts"]
                                )
                            )
                            return False

                    self.write_last_ts_written()

            logging.info("Disconnecting from database ...")
            conn.close()
            logging.info("Disconnected from database.")
            return True

        except psycopg2.OperationalError as e:
            logging.error(
                'Could not connect to database : "{}"'.format(str(e).replace("\n", ""))
            )

            return False

        return True

    def run_cron(self):
        """
            Starts only one run, and then exit.
        """
        logging.info(
            'Starting with the "cron" parameter, we will run once and then exit.'
        )
        self.request_messages()
        logging.info("Nothing more to be done, we will exit.")
        exit(0)

    def run_daemon(self):
        """
            Starts a run every N seconds, sleeping between runs.
        """
        logging.info("Starting in daemon mode.")
        while True:
            logging.info("Starting a new iteration.")
            self.request_messages()
            logging.info("Iteration finished.")
            try:
                sleep(self.daemon_interval)
            except KeyboardInterrupt:
                logging.warning("Ctrl-C received, stopping daemon.")
                break
        logging.info("Nothing more to be done, we will exit.")
        exit(0)


def main():
    """
        The main function, executed if the module is called directly.
    """
    arguments = docopt(__doc__, version="0.1")

    if arguments["--debug"]:
        log_level = "DEBUG"
    else:
        log_level = config["log_level"]
    logging.basicConfig(
        format="%(asctime)s :: %(levelname)s :: %(message)s",
        level=logging.getLevelName(log_level),
    )

    logging.debug("Arguments : {}".format(json.dumps(arguments)))
    logging.info("Starting Matrix room logger.")

    srl = SynapseRoomLogger(config)

    if arguments["cron"]:
        srl.run_cron()
    elif arguments["daemon"]:
        srl.run_daemon()


with open("config.yaml", "r") as config_file:
    config = yaml.load(config_file)

if __name__ == "__main__":
    main()
