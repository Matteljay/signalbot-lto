import logging
import json
import os

class Commander:
  def __init__(self, signalHook, watcher):
    self.ACCOUNTS_FILE = signalHook.getSignalPath() + '/watchdog-contacts.json'
    self.COMMANDS = [
      'help,h,list',
      'unsubscribe,unsub',
      'contacts,cont,subs',
      # 'trustall',
      'status,stat,st']
    self.WELCOME = 'Welcome, you are now subscribed to the LTO watchdog and will receive messages when crypto connectivity is lost. Type \'help\' for a list of commands'
    self.contactDict = {}
    self.replyTo = None
    self.signalHook = signalHook
    self.watcher = watcher

  def loadAccountsFile(self):
    try:
      with open(self.ACCOUNTS_FILE, 'r+') as fd:
        self.contactDict = json.load(fd)
      logging.info('Loaded accounts from file: ' + self.ACCOUNTS_FILE)
    except FileNotFoundError:
      logging.info('Account info file will be created: ' + self.ACCOUNTS_FILE)

  def getAllSubscribed(self):
    subscribed = []
    for k, v in self.contactDict.items():
      if 'subscribed' in v and v['subscribed'] == True:
        subscribed.append(k)
    if not len(subscribed):
      logging.warning('No subscribers found')
    return subscribed

  def writeAccountsFile(self):
    try:
      os.makedirs(os.path.dirname(self.ACCOUNTS_FILE), exist_ok=True)
      with open(self.ACCOUNTS_FILE, 'w') as fd:
        json.dump(self.contactDict, fd)
      logging.debug('Wrote to accounts file: ' + self.ACCOUNTS_FILE)
    except Exception as e:
      logging.error(e)

  def handleMessages(self, timestamp, source, groupID, message, attachments):
    logging.debug(f'Message: {timestamp}, {source}, {groupID}, {message}, {attachments}')
    self.replyTo = source
    self.checkWelcome() # any message triggers subscribe action
    self.command = self.matchCmds(message)
    self.parseCommand()
  
  def checkWelcome(self):
    if self.isSubscribed(self.replyTo):
      return
    self.updateAccount({ 'subscribed' : True })
    self.writeAccountsFile()
    logging.info('Subscribed: ' + self.replyTo)
    self.signalHook.sendMessage([self.replyTo], self.WELCOME)

  def matchCmds(self, testCmd):
    lowerCmd = testCmd.strip().lower().split()
    if not len(lowerCmd):
      logging.debug(f'ignoring empty command')
      return
    for cmd in self.COMMANDS:
      aliasList = cmd.split(',')
      ret = aliasList[0]
      for alias in aliasList:
        if alias == lowerCmd[0]:
          return ret
    logging.warn(f'ignoring command: {testCmd}')
    return None

  def parseCommand(self):
    command = self.command
    if command == 'help':
      msg = 'List of commands:\n' + self.prettyPrint(self.COMMANDS)
    elif command == 'unsubscribe':
      self.updateAccount({ 'subscribed' : False })
      self.writeAccountsFile()
      msg = 'You were unsubscribed. Send me any message if you want to subscribe again. Bye!'
    elif command == 'contacts':
      msg = 'Subscribed contacts to LTO-dog are:\n' + '\n'.join(self.getAllSubscribed())
    # elif command == 'trustall':
    #   msg = 'NOTICE: all contacts had their keys trusted and sessions updated!'
    #   subs = self.getAllSubscribed()
    #   sendObject = { 'trust' : { 'contacts' : subs }, 'endSession' : { 'contacts' : subs },
    #     'sendMessage': { 'contacts' : subs, 'message' : msg } }
    #   self.signalHook.send(json.dumps(sendObject))
    #   return
    elif command == 'status':
      msg = self.watcher.serverStatus
    else:
      return
    logging.info(f'Command {command} from {self.replyTo}')
    self.signalHook.sendMessage([self.replyTo], msg)

  def prettyPrint(self, commandsList):
    output = []
    for cmd in commandsList:
      aliasList = cmd.split(',')
      line = aliasList[0]
      if len(aliasList) > 1:
        del aliasList[0]
        line += ' (' + ', '.join(aliasList) + ')'
      output.append(line)
    return '\n'.join(output)

  def updateAccount(self, patchObject):
    number = self.replyTo
    if not number in self.contactDict:
      self.contactDict[number] = patchObject
      return
    self.contactDict[number].update(patchObject)

  def isSubscribed(self, number):
    try:
      return self.contactDict[number]['subscribed'] == True
    except Exception:
      return False

# EOF
