import logging
import requests
import time

class Watcher:
  def __init__(self, signalHook):
    self.signalHook = signalHook
    self.serverStatus = 'nothing yet'
    self.statusErroneous = False
    requests.packages.urllib3.disable_warnings()

  def worker(self):
    # return True to keep looping
    url = f'http://{self.signalHook.ltoIPport}/blocks/headers/last'
    try:
      jsonData = requests.get(url, verify=False, timeout=20).json()
      self.handleSuccess(jsonData)
    except Exception as e:
      errorName = type(e).__name__
      self.handleError(errorName)
    return True

  def handleSuccess(self, jsonData):
    nowSec = int(time.time())
    secPassed = nowSec - jsonData['timestamp'] // 1000
    blockHeight = jsonData['height']
    self.serverStatus = f'Block {blockHeight} time is {secPassed} sec'
    if self.statusErroneous:
      self.statusErroneous = False
      recoveredMsg = f'Recovered! {self.serverStatus}'
      logging.info(recoveredMsg)
      self.signalHook.sendMessageSubscribed(recoveredMsg)

  def handleError(self, errorName):
    self.serverStatus = f'Got error: {errorName}'
    if not self.statusErroneous:
      self.statusErroneous = True
      errorMsg = self.serverStatus
      logging.error(errorMsg)
      self.signalHook.sendMessageSubscribed(errorMsg)


# EOF
