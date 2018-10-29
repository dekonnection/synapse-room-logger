"""
synapse-room-logger : a simple tool to export your Matrix rooms history to
plain-text logs.

Usage:
    roomlogger cron [options]
    roomlogger daemon [options]

Options:
    --help          This helper.
    --debug         Be more verbose.
"""

from docopt import docopt
import psycopg2
import yaml
import logging
import json
from datetime import datetime

with open("config.yaml", "r") as config_file:
    config = yaml.load(config_file)


class SynapseRoomLogger(object):
    def __init__(self, config):
        self.room_id = config["room_id"]
        self.db_host = config["db_host"]
        self.db_name = config["db_name"]
        self.db_user = config["db_user"]
        self.db_password = config["db_password"]
        self.output_directory = config["output_directory"]
        state_file_name = ".last_ts"
        self.state_file_path = "{}/{}".format(
            config["output_directory"], state_file_name
        )

    def db_connect(self):
        logging.info("Connecting to database ...")
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=5,
            )
            self.conn = conn
            self.cur = self.conn.cursor()
            logging.info("Connected to database.")
            return True
        except psycopg2.OperationalError as e:
            logging.error(
                'Could not connect to database : "{}"'.format(str(e).rstrip())
            )
            return False

    def db_disconnnect(self):
        logging.info("Disconnecting from database ...")
        self.cur.close()
        self.conn.close()
        logging.info("Disconnected from database.")

    def request_messages(self):
        base_query = "SELECT e.received_ts, j.json FROM events AS e INNER JOIN event_json AS j USING (event_id) WHERE e.room_id='{room_id}' AND e.received_ts>{after_ts} AND e.type='m.room.message' ORDER BY e.received_ts;"

        self.read_last_ts_written()

        if not self.db_connect():
            logging.info("We won't do anything this time")
            return False

        self.cur.execute(
            base_query.format(room_id=self.room_id, after_ts=self.last_ts_written)
        )

        for row in self.cur:
            # there is two fields : timestamp at reception, and json data
            line = self.process_message_row(row)
            file_path = self.ts_to_filepath(line["ts"])

            if self.append_line(file_path, json.dumps(line)):
                logging.info(
                    "Message with timestamp {} written to {}".format(
                        line["ts"], file_path
                    )
                )
                self.last_ts_written = line["ts"]
            else:
                logging.error(
                    "We couldn't write message {}, we will exit.".format(line["ts"])
                )
                return False
        self.write_last_ts_written()
        self.db_disconnnect()
        return True

    def process_message_row(self, message_row):
        msg_received_ts = message_row[0]
        msg_raw_data = json.loads(message_row[1])
        msg_data = {
            "ts": msg_received_ts,
            "origin_ts": msg_raw_data["origin_server_ts"],
            "origin": msg_raw_data["origin"],
            "sender": msg_raw_data["sender"],
            "event_id": msg_raw_data["event_id"],
            "message": msg_raw_data["content"]["body"],
            "url": msg_raw_data["content"].get("url", None),
        }
        return msg_data

    def ts_to_filepath(self, ts):
        path = "{output_directory}/{date}.log"
        date = datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        return path.format(output_directory=self.output_directory, date=date)

    def append_line(self, file_path, line):
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
            logging.warn(
                "No state file found at {}, setting last timestamp written to 0.".format(
                    self.state_file_path
                )
            )
            return False

    def write_last_ts_written(self):
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

    def cron(self):
        pass


def main():
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

    srl.request_messages()
    return True


if __name__ == "__main__":
    main()
