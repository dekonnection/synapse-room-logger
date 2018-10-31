#! /bin/sh
srl_conf_file=/synapse-room-logger/config.yaml

if [ -f "$srl_conf_file" ]
then
    echo "OK : starting synapse-room-logger"
    /usr/local/bin/python -m synapse-room-logger daemon
else
    echo -e "ERROR : you need to mount a bind volume to expose \
$srl_conf_file to the container.\nWe will now exit."
    exit 1
fi
