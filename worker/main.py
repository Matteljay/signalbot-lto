#!/usr/bin/python3
import logging
import os, sys
import time
import signal # for SIGINT (https://unix.stackexchange.com/a/251267)
import pydbus as dbus
from gi.repository import GLib

from Watcher import Watcher
from Commander import Commander

SIGNAL_PATH = os.path.expanduser('~/signal-cli-config')
DEFAULT_INTERVAL_SECONDS = 30

class SignalHook:
  def __init__(self):
    self.signalBus = None
    self.glibLoop = None
    self.ltoIPport = ''
    self.commander = None

  def die(self, err):
    sys.exit('ERROR: ' + err)

  def getSignalPath(self):
    return SIGNAL_PATH

  def sigHandler(self, sig, frame):
    self.glibLoop.quit()
    logging.info(f'Clean exit, received signal {sig}')
    sys.exit(0)

  def getOneSignalUser(self):
    usernames = [f for f in os.listdir(SIGNAL_PATH)
      if os.path.isfile(os.path.join(SIGNAL_PATH, f)) and f.startswith('+')]
    usercount = len(usernames)
    if usercount == 0:
      self.die(f'no users found in {SIGNAL_PATH}')
    elif usercount > 1:
      self.die(f'too many usernames found in {SIGNAL_PATH}')
    else: # usercount == 1
      return usernames[0]

  def sendMessage(self, to, msg):
    self.signalBus.sendMessage(msg, [], to)

  def sendMessageSubscribed(self, msg):
    subs = self.commander.getAllSubscribed()
    if subs:
      self.signalBus.sendMessage(msg, [], subs)
    else:
      info.warning(f'no subscribed users found')
  
  def main(self):
    logging.basicConfig(
      level=logging.INFO,
      stream=sys.stderr,
      datefmt='%Y-%m-%dT%H:%M:%S',
      format='%(asctime)s %(levelname)s: %(message)s'
    )
    # Handle signals more gracefully
    signal.signal(signal.SIGINT, self.sigHandler)
    signal.signal(signal.SIGTERM, self.sigHandler)
    signal.signal(signal.SIGHUP, self.sigHandler)

    self.ltoIPport = os.environ.get('LTO_SERVER_IPPORT')
    if not self.ltoIPport:
      self.die(f'Please set environment variable LTO_SERVER_IPPORT')
    logging.info(f'Will monitor LTO server {self.ltoIPport}')

    user = self.getOneSignalUser()
    logging.info(f'Using phone number {user}')
    dashUser = user.replace('+', '_')
    iface = f'/org/asamk/Signal/{dashUser}'

    intervalSec = int(os.environ.get('INTERVAL_SECONDS', DEFAULT_INTERVAL_SECONDS))
    logging.info(f'Watch delay is {intervalSec} seconds')

    #os.environ['DBUS_SESSION_BUS_ADDRESS'] = 'unix:abstract=/tmp/dbus-VaPC4GsoJP,guid=c98f80e83a6d8723b1322bd360af71e1'
    os.environ['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=/tmp/sigsock'
    os.environ['DISPLAY'] = ':0'
    bus = dbus.SessionBus()
    self.glibLoop = GLib.MainLoop()
    self.signalBus = bus.get('org.asamk.Signal', iface)
    watcher = Watcher(self)
    self.commander = Commander(self, watcher)
    self.commander.loadAccountsFile()
    self.signalBus.onMessageReceived = self.commander.handleMessages
    watcher.worker()
    GLib.timeout_add(intervalSec * 1000, watcher.worker)
    #GLib.io_add_watch(sys.stdin, GLib.IO_IN, self.readKeys, priority=GLib.PRIORITY_DEFAULT) # def readKeys(self, source, cb_condition):
    self.glibLoop.run()

if __name__ == '__main__':
  signalHook = SignalHook()
  signalHook.main()

# EOF
