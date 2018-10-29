# synapse-room-logger
A simple tool to extract a Matrix room history into flat files, for logging,
archiving, indexing purposes, or whatever.

It currently only works with Synapse configured with a PostgreSQL database as
backend.
Support is not currently planned for SQLite, but feel free to open an issue if
you need it.

## Configuration

A `config.yaml.example` file is provided and meant to be copied as
`config.yaml`, each line being pretty self-explanatory.

### Database user

**I strongly advise against using the same postgresql user as your production
synapse instance.**

This tool is only doing a `SELECT` query, but this is good practice to separate
this kind of stuff of your production by dedicating a read-only user to it.

## Usage

### Cron mode

This mode is meant to be used if you don't want the tool to be continuously
running and rather be started periodically as a cron job.

The tool stores the last timestamp logged, so each run is starting after the
position of the previous one.

```
$ python -m synapse-room-logger cron
2018-10-29 15:37:29,873 :: INFO :: Starting Matrix room logger.
2018-10-29 15:37:29,873 :: INFO :: Starting with the "cron" parameter, we will run once and then exit.
2018-10-29 15:37:29,873 :: INFO :: Reading last timestamp written from previous run.
2018-10-29 15:37:29,873 :: INFO :: Last timestamp from previous run is 1540665523034.
2018-10-29 15:37:29,873 :: INFO :: Connecting to database ...
2018-10-29 15:37:29,875 :: INFO :: Connected to database.
2018-10-29 15:37:29,879 :: INFO :: Message with timestamp 1540665523109 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,879 :: INFO :: Message with timestamp 1540665712294 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,880 :: INFO :: Message with timestamp 1540665717931 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,880 :: INFO :: Message with timestamp 1540666658690 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,880 :: INFO :: Message with timestamp 1540667455075 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,880 :: INFO :: Message with timestamp 1540670153634 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,880 :: INFO :: Message with timestamp 1540670217876 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,880 :: INFO :: Message with timestamp 1540670229760 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,880 :: INFO :: Message with timestamp 1540672238319 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,881 :: INFO :: Message with timestamp 1540675192562 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,881 :: INFO :: Message with timestamp 1540676933099 written to /tmp/test/2018-10-27.log
2018-10-29 15:37:29,881 :: INFO :: Message with timestamp 1540685524275 written to /tmp/test/2018-10-28.log
2018-10-29 15:37:29,881 :: INFO :: Message with timestamp 1540688545213 written to /tmp/test/2018-10-28.log
2018-10-29 15:37:29,881 :: INFO :: Message with timestamp 1540711681592 written to /tmp/test/2018-10-28.log
2018-10-29 15:37:29,897 :: INFO :: Writing last timestamp to state file.
2018-10-29 15:37:29,897 :: INFO :: Timestamp 1540711681592 written to state file.
2018-10-29 15:37:29,897 :: INFO :: Disconnecting from database ...
2018-10-29 15:37:29,898 :: INFO :: Disconnected from database.
2018-10-29 15:37:29,898 :: INFO :: Nothing more to be done, we will exit.
```

### Daemon mode

In this mode, the process is continuously running and is executing the same
extraction as if started in cron mode, but this time periodically and at a
configurable interval.

```
$ python -m synapse-room-logger daemon
2018-10-29 16:02:36,886 :: INFO :: Starting Matrix room logger.
2018-10-29 16:02:36,886 :: INFO :: Starting in daemon mode.
2018-10-29 16:02:36,886 :: INFO :: Starting a new iteration.
2018-10-29 16:02:36,886 :: INFO :: Reading last timestamp written from previous run.
2018-10-29 16:02:36,887 :: INFO :: Last timestamp from previous run is 1540758924934.
2018-10-29 16:02:36,887 :: INFO :: Connecting to database ...
[...]
```
