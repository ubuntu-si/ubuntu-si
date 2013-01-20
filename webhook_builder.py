#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import threading
import logging
import signal
import sys

from datetime import datetime
from pastebin import PastebinAPI
from Queue import Queue

import irc.bot
import irc.strings

try:
    from flask import Flask, request
except Exception, e:
    print "pip install flask"

try:
    import envoy
except Exception, e:
    print "pip install envoy"

try:
    import json
    json_decode = json.loads
except ImportError:
    import simplejson
    json_decode = simplejson.loads


logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )
app = Flask(__name__)
zaposlitve = Queue()


class Jobber(threading.Thread):

    aktivno = None

    def koncaj(self):
        zaposlitve.task_done()
        self.aktivno = None

    def run(self):
        while True:
            if self.aktivno is None:
                delo = zaposlitve.get()
                delo.handler = self
                self.aktivno = delo
                delo.start()
job_queue = Jobber()


class BuildBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        a = e.arguments[0]
        if len(a) > 1 and a.startswith("."):
            self.do_command(e, a.strip())
        return

    def sayall(self, msg):
        self.connection.privmsg(self.channel, msg)

    def do_command(self, e, cmd):
        nick = e.source.nick
        chan = e.target

        if '.isostatus' in cmd:
            if job_queue.aktivno is None:
                self.sayall('Mirujem')
                self.sayall('Prenos: (32bit) http://185.14.186.232/dist32/binary-hybrid.iso [.torent|.zsync]')
                self.sayall('Prenos: (64bit) http://185.14.186.232/dist/binary-hybrid.iso [.torent|.zsync]')
            else:
                self.sayall('Delam')
                for res in job_queue.aktivno.history:
                    self.sayall(res)
        if "dz0ny" == nick:
            if '.isobuild32' in cmd:
                new_build = Delo('32')
                zaposlitve.put(new_build)
                self.connection.privmsg(nick, u'Začel z izgradnjo 32bit iso')

            if '.isobuild64' in cmd:
                new_build = Delo('64')
                zaposlitve.put(new_build)
                self.connection.privmsg(nick, u'Začel z izgradnjo 64bit iso')

    def irc_notify(self, thread, point, text=""):
        url = ""
        if len(text) > 1:
            url = PastebinAPI().paste("94c4c6e3faf2271b9175bb7601738b79", text)

            if len(url) > 1:
                msg = "Napaka pri gradnji > {0}: {1} {2}".format(thread.encode("utf-8"), point.encode("utf-8"), url.encode("utf-8"))
            else:
                msg = "{0}: {1}".format(thread.encode("utf-8"), point.encode("utf-8"))
            print msg
            self.sayall(msg)
bot = BuildBot('#ubuntu-si', "Owcica", 'irc.freenode.net')


class Delo(threading.Thread):

    """Delo je abstrakcija make build zadeve"""
    def __init__(self, flavor):
        self.flavor = flavor
        self.history = []
        self.start_time = datetime.now()
        threading.Thread.__init__(self)
        self.name = "Delo-build-" + flavor

    def run(self):
        self.build_all()
        return

    def check_and_report(self, cmd):
        self.delta = datetime.now() - self.start_time
        if cmd.status_code is 0:
            self.history.append(u"Command: {0} ✓ ({1})".format(
                " ".join(cmd.command),
                str(self.delta)
            ))
            return True
        else:
            bot.irc_notify(self.getName(), " ".join(cmd.command), 'Napaka: {0}\nLog: {1}'.format(
                cmd.std_err,
                cmd.std_out
            ))
            self.history.append(u"Command: {0} ✗ ({1})".format(
                " ".join(cmd.command),
                str(self.delta)
            ))
            return False

    def build_all(self):

        git = envoy.run("git pull")
        if self.check_and_report(git):
            deb = envoy.run("make deb" + self.flavor)
            if self.check_and_report(deb):
                iso = envoy.run("make iso" + self.flavor)
                if self.check_and_report(iso):
                    dist = envoy.run("make dist" + self.flavor)
                    self.check_and_report(dist)

                    self.delta = datetime.now() - self.start_time
                    bot.irc_notify(self.getName(), "Izgradnja je trajala {0}".format(str(self.delta)))

                    if self.flavor is "32":
                        self.sayall('Prenos: (32bit) http://185.14.186.232/dist32/binary-hybrid.iso [.torent|.zsync]')
                    else:
                        self.sayall('Prenos: (64bit) http://185.14.186.232/dist/binary-hybrid.iso [.torent|.zsync]')
                    
        for res in self.history:
            bot.irc_notify(self.getName(), res)

        if self.handler:
            self.handler.koncaj()


@app.route("/web_hook/<flavor>", methods=['POST'])
def web_hook(flavor):
    if flavor in ["64", "32"]:
        logging.debug(flavor)
        if request.remote_addr in ["207.97.227.253", "50.57.128.197",
                                   "108.171.174.178", "50.57.231.61",
                                   "127.0.0.1"]:
            if request.form["payload"]:
                payload = request.form["payload"]
                payload = json_decode(payload)
                try:
                    msg = "Nov commit[" + flavor + "]: " + payload["head_commit"]["committer"]["username"] + u": " +  payload["head_commit"]["message"] + " " + payload["head_commit"]["url"]  + " @ " + payload["head_commit"]["timestamp"]
                    print msg
                    bot.sayall(msg)
                except Exception, e:
                    print e

                should_build = False
                try:
                    for x in payload["head_commit"]["modified"]:
                        if "si-ubuntu-defaults" in x:
                            should_build = True
                except Exception, e:
                    should_build = True
                    print e

                if should_build:
                    new_build = Delo(flavor)
                    zaposlitve.put(new_build)
                    return "OK"
    return "FAIL"


class BotThread(threading.Thread):
    def run(self):
        bot.start()

if __name__ == "__main__":
    
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    try:
        job_queue.start()
        BotThread().start()
        app.run(host='0.0.0.0')

    except KeyboardInterrupt:
        sys.exit(0)
