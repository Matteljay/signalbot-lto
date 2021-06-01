#!/bin/bash
# This file is executed from inside the Docker container
export DBUS_SESSION_BUS_ADDRESS="unix:path=/tmp/sigsock"
dbus-daemon --session --fork --address="$DBUS_SESSION_BUS_ADDRESS" --print-address
signal-cli --config=/home/user/signal-cli-config daemon >/dev/null &
disown
echo "Waiting for signal-cli to settle..."
sleep 12s
cd "/home/user/worker"
echo "Starting main.py..."
exec python3 main.py
