#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import threading
import logging
import simplejson
from pastebin import PastebinAPI
from Queue import Queue
from irc import Bot

try:
    from flask import Flask, render_template, request
except Exception, e:
    print "pip install flask"

try:
    import envoy
except Exception, e:
    print "pip install envoy"


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
job_queue.start()


class IRCBOT(Bot):

    def irc_notify(self, thread, point, text=""):
        url = ""
        if len(text) > 1:
            url = PastebinAPI().paste("94c4c6e3faf2271b9175bb7601738b79", text)
        for chan in self.channels:
            if len(url) > 1:
                msg = "Napaka pri gradnji > {0}: {1} {2}".format(thread.encode("utf-8"), point.encode("utf-8"), url.encode("utf-8"))
            else:
                msg = "{0}: {1}".format(thread.encode("utf-8"), point.encode("utf-8"))
            print msg
            self.msg(chan, msg)

    def dispatch(self, origin, args):
        cmd = "{0}".format(args[0]).encode("utf-8")
        if '.isostatus' in cmd:
            if job_queue.aktivno is None:
                self.msg(origin.sender, 'Mirujem')
            else:
                self.msg(origin.sender, 'Delam')
                for res in job_queue.aktivno.history:
                    self.msg(origin.sender, res)
        if '.isobuild32' in cmd and "dz0ny" in origin.nick:
            new_build = Delo('32')
            zaposlitve.put(new_build)
            self.msg(origin.sender, 'Začel z izgradnjo 32bit iso')
        if '.isobuild64' in cmd and "dz0ny" in origin.nick:
            new_build = Delo('64')
            zaposlitve.put(new_build)
            self.msg(origin.sender, 'Začel z izgradnjo 64bit iso')
bot = IRCBOT('UBBB-iso', "UBBB-iso", ['#ubuntu-si2'])


class BOTThread(threading.Thread):
    """BOTThread"""
    def run(self):
        bot.run('irc.freenode.net')
BOTThread().start()


class Delo(threading.Thread):

    """Delo je abstrakcija make build zadeve"""
    def __init__(self, flavor):
        self.flavor = flavor
        self.history = []
        threading.Thread.__init__(self)
        self.name = "Delo-build-" + flavor

    def run(self):
        self.build_all()
        return

    def check_and_report(self, cmd):
        if cmd.status_code is 0:
            self.history.append(u"Command: {0} ✓".format(" ".join(cmd.command)))
            return True
        else:
            bot.irc_notify(self.getName(), " ".join(cmd.command), 'Napaka: {0}\nLog: {1}'.format(cmd.std_err, cmd.std_out))
            self.history.append(u"Command: {0} ✗".format(" ".join(cmd.command)))
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

        for res in self.history:
            bot.irc_notify(self.getName(), res)

        if self.handler:
            self.handler.koncaj()

# @app.route("/")
# def status():
#     return render_template('status.html',
#                            status_amd64={
#                                "alive": build_amd64_handle.isAlive(),
#                                "history": build_amd64_handle.isAlive(),
#                                "checks": build_amd64_handle.isAlive(),
#                            },
#                            status_i386={
#                                "alive": build_i386_handle.isAlive(),
#                                "history": build_i386_handle.isAlive(),
#                                "checks": build_i386_handle.isAlive(),
#                            })


@app.route("/web_hook/<flavor>", methods=['GET', 'POST'])
def web_hook(flavor):
    if flavor in ["64", "32"]:
        logging.debug(flavor)
        if request.remote_addr in ["207.97.227.253", "50.57.128.197",
                                   "108.171.174.178", "50.57.231.61",
                                   "127.0.0.1"]:
            if request.form["payload"]:
                payload = simplejson.loads(request.form["payload"])

                for chan in bot.channels:
                    bot.msg(chan, "{{0}: {1}}".format(
                        payload["head_commit"]["committer"]["username"],
                        payload["head_commit"]["message"]))

                should_build = False
                for x in payload["head_commit"]["modified"]:
                    if "si-ubuntu-defaults" in x:
                        should_build = True

                if should_build:
                    new_build = Delo(flavor)
                    zaposlitve.put(new_build)
                    return "OK"
    return "FAIL"

if __name__ == "__main__":
    app.run(host='0.0.0.0')
