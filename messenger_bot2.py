#!/usr/bin/python2
# -*- coding: utf-8 -*-

from messenger_api.MessengerAPI.Messenger import Messenger
from messenger_api.MessengerAPI.Message import Message
from messenger_api.MessengerAPI.Thread import GroupThread
from messenger_api.MessengerAPI import Actions
from messenger_api.MessengerAPI.base.Exceptions import MessengerException
from pyxmpp.jid import JID
from pyxmpp.jabber.client import Client
from pyxmpp.presence import Presence
from pyxmpp.message import Message as XMPPMessage
from getpass import getpass
from threading import Thread
import traceback
import sys
import os
import StringIO
import ConfigParser
import argparse
import logging


class ClientThread(Thread, Client):
    def __init__(self, jid=None, password=None, server=None, port=5222,
                 auth_methods=("sasl:DIGEST-MD5",),
                 tls_settings=None, keepalive=0):
        logging.basicConfig()
        super(ClientThread, self).__init__(None, None, None, (), None, None)
        Client.__init__(self, jid, password, server, port, auth_methods, tls_settings, keepalive)

    def run(self):
        self.loop(1)

client = None


def read_properties_file(file_path):
    with open(file_path) as f:
        c = StringIO.StringIO()
        c.write('[dummy_section]\n')
        c.write(f.read().replace('%', '%%'))
        c.seek(0, os.SEEK_SET)
        cp = ConfigParser.SafeConfigParser()
        cp.readfp(c)
        return dict(cp.items('dummy_section'))


def handler(message):
    if msg.me.fbid == message.author.fbid:
        return

    xmpp_message = u''

    if not isinstance(message.thread, GroupThread):
        msg.get_thread(message.author.fbid).send_message(automessage)
        print('Incoming message from ' + message.author.name)
    else:
        xmpp_message = u'Group thread: ' + message.thread.get_name(True) + u'\n'
        print('Incoming message from ' + message.author.name + " in group thread " + message.thread.get_name(True))

    xmpp_message += u'Message from ' + message.author.name + ':\n' + message.time.strftime("%d/%m/%Y %H:%M")\
                   + '\n' + message.body
    client.get_stream().send(XMPPMessage(to_jid=xmpp_target, body=xmpp_message))

# WTF Actions
wtfactions = [Actions.Action, Actions.MessagingAction, Actions.MercuryAction, Actions.LogMessageAction,
              Actions.GenericAdminTextAction, Actions.DeltaAction]


def wtfactions_handler(action):
    if action in wtfactions:
        print('Unknown Action: ' + action.name + '\n  ' + action.data)

try:
    # Arguments
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument('--config', help="Configuration file", default='messenger_bot.conf')
    args = argumentParser.parse_args()

    # Config
    config_file = os.path.expanduser(args.config)

    if not os.path.isfile(config_file):
        print('Invalid config file')
        exit()

    if args.config is not "messenger_bot.conf":
        print('Using config file: ' + config_file)

    config = read_properties_file(config_file)
    fb_id = config.get('fbid')
    fb_password = config.get('fbpass')
    bot_jid = JID(config.get('jid'))
    xmpp_password = config.get('xmpp_password')
    xmpp_target = config.get('xmpp_target')
    automessage = config.get('automessage').replace('\\n', '\n')

    if not fb_password:
        fb_password = getpass('Facebook password: ')

    while True:
        try:
            # XMPP
            client = ClientThread(bot_jid, xmpp_password)
            client.connect()
            presence = Presence()
            presence.set_to(xmpp_target)
            client.get_stream().send(presence)
            client.start()
            print 'Connected to XMPP'

            # Messenger
            msg = Messenger(fb_id, fb_password)
            msg.register_action_handler(Message, handler)
            msg.register_action_handler(Actions.Action, wtfactions_handler)
            print 'Connected to Facebook Messenger as ' + fb_id

            while True:
                try:
                    msg.pull()
                except MessengerException:
                    traceback.print_exc(file=sys.stdout)
        except KeyboardInterrupt:
            raise
        except BaseException:
            traceback.print_exc(file=sys.stdout)
except KeyboardInterrupt:
    client.disconnect()
    print '\nStopping MessengerBOT'
    exit()
