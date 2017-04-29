# -*- coding: UTF-8 -*-
import os
import sys
import json
import tempfile
import requests
import hashlib
import datetime
import sqlite3
import random
from random import randint
from time import sleep
from stem import Signal
from stem.control import Controller
import getopt


class newsCrawler():
    # Generic sequential news crawler object
    def __init__(self, name):
        # load variables from json array of strings
        jsonVars = []
        self.name = name
        # change working directory to script location and find json file
        if not os.path.dirname(sys.argv[0]) == '':
            os.chdir(os.path.dirname(sys.argv[0]))
        jsonFile = "json/" + self.name + ".json"
        with open(jsonFile, encoding='utf-8') as varLines:
            for line in varLines:
                jsonVars.append(json.loads(line))
        crawlVars = jsonVars[0]
        # there should be a better way to do this
        self.name = crawlVars[0]
        self.urlStart = crawlVars[1]
        self.urlEnd = crawlVars[2]
        self.urlToGet = crawlVars[3]
        self.dateStart = crawlVars[4]
        self.dateEnd = crawlVars[5]
        self.titleStart = crawlVars[6]
        self.titleEnd = crawlVars[7]
        self.bodyStart = crawlVars[8]
        self.bodyEnd = crawlVars[9]
        self.authorStart = crawlVars[10]
        self.authorEnd = crawlVars[11]
        self.defaultTitleHash = crawlVars[12]
        # log file that contains ID, title, body, hashes, etc
        self.logPath = "news/log/"
        if not os.path.exists(self.logPath):
            os.makedirs(self.logPath)
        self.log = sqlite3.connect(self.logPath + "log.db")

        self.tempfile = self.makeTemp()
        self.userAgents = self.loadUserAgent("user_agents.txt")

        if not os.path.exists(self.name + "/changed_body/"):
            os.makedirs(self.name + "/changed_body/")
        self.changeDir = self.name + "/changed_body/"

        self.usage = """
        Running without options, newsCrawler will start fetching articles
        sequentially, starting from 0. After running newsCrawler with '-i' or
        '-idstart' once, it can subsequently be run without '-i' to start from
        it's last starting id automatically.
        -h, --help                : show usage
        -i <int>, --idstart <int> : start crawling at specific inner id
        -t, --tor                 : use tor to make requests (default off)
        """

        # get arguments and options
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hti:",
                                       ["help", "tor", "idstart="])
        except getopt.GetoptError as err:
            print(err)
            print(self.usage)
            sys.exit(2)
        self.startingId = 0
        self.manualStart = False
        self.useTor = False
        for o, a in opts:
            if o in ("-h", "--help"):
                print(self.usage)
                sys.exit()
            elif o in ("-t", "--tor"):
                self.useTor = True
                print("Using tor...")
            elif o in ("-i", "--idstart"):
                self.startingId = a
                self.manualStart = True
                print("Starting sequential crawl at id " + str(a))
            else:
                assert False, "unhandled option"

        self.lastEnd = self.getLastEnd()
        self.startDb = self.createStartDb()
        self.lastStart = self.getLastStart()

        # initialize tor session
        if self.useTor:
            self.renewConnection()

    def main(self):
        if not self.manualStart:
            self.autoStartLoop()
        else:
            self.manualStartLoop()

    def manualStartLoop(self):
        c = self.log.cursor()
        innerId = int(self.startingId)
        emptyCount = 0

        while emptyCount < 25:
            now = datetime.datetime.now()
            # if innerId in log, hash and compare
            check = self.checkLog(innerId)
            if check:
                newBody = self.compareArticle(innerId)
                if newBody:
                    changePath = self.changeDir + str(innerId) + ".html"
                    with open(changePath, 'w+') as bodyFile:
                        bodyFile.write(newBody)
                innerId += 1
                emptyCount = 0
                continue
            # title, body, date, author, title hash, body hash
            t, b, d, a, tH, bH = self.getArticle(innerId,
                                                 self.defaultTitleHash)
            if not t:
                innerId += 1
                emptyCount += 1
                continue
            logInfo = (self.name, innerId, str(now), d, b, bH, t, tH, a)
            c.execute('INSERT INTO log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      logInfo)
            self.log.commit()
            # write body content to HTML file.
            # seems to be encoding issue with joongang (EUC-KR, not UTF-8)
            # (FIX THIS)

            # sleep random 0 to 60 seconds
            sleep(randint(0, 60))
            if self.useTor:
                self.renewConnection()

            innerId += 1
            emptyCount = 0

    def autoStartLoop(self):
        c = self.log.cursor()
        innerId = int(self.lastStart)
        repetition = self.updateLastStart()
        lastEnd = int(self.lastEnd)

        while innerId < lastEnd + 25 + 25 * repetition:
            now = datetime.datetime.now()
            # if innerId in log, hash and compare
            check = self.checkLog(innerId)
            if check:
                newBody = self.compareArticle(innerId)
                if newBody:
                    changePath = self.changeDir + str(innerId) + ".html"
                    with open(changePath, 'w+') as bodyFile:
                        bodyFile.write(newBody)
                innerId += 1
                continue
            # title, body, date, author, title hash, body hash
            t, b, d, a, tH, bH = self.getArticle(innerId,
                                                 self.defaultTitleHash)
            if not t:
                innerId += 1
                continue
            logInfo = (self.name, innerId, str(now), d, b, bH, t, tH, a)
            c.execute('INSERT INTO log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      logInfo)
            self.log.commit()
            # write body content to HTML file.
            # seems to be encoding issue with joongang (EUC-KR, not UTF-8)
            # (FIX THIS)

            # sleep random 0 to 60 seconds
            # sleep(randint(0, 60))
            if self.useTor:
                self.renewConnection()

            innerId += 1
            lastEnd = int(self.getLastEnd())

    def renewConnection(self):
        self.session = requests.session()
        self.session.proxies = {'http':  'socks5://127.0.0.1:9050',
                                'https': 'socks5://127.0.0.1:9050'}
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="password")
            controller.signal(Signal.NEWNYM)
        userAgent = random.choice(self.userAgents)
        self.session.headers = {"User-Agent": userAgent}
        print("Current Tor Session IP : \n" +
              self.session.get("http://httpbin.org/ip").text + "\n" +
              "Current User Agent : \n" +
              str(userAgent))

    def loadUserAgent(self, uafile):
        userAgents = []
        with open(uafile, 'rb') as uaf:
            for ua in uaf.readlines():
                if ua:
                    userAgents.append(ua.strip()[1:-1-1])
        random.shuffle(userAgents)
        return(userAgents)

    def createStartDb(self):
        startDir = self.name + "/start/"
        if not os.path.exists(startDir):
            os.makedirs(startDir)
        startDb = sqlite3.connect(startDir + "start.db")
        return startDb

    def getLastStart(self):
        c = self.startDb.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS start (lastStart int,
                     repetition int)''')
        self.startDb.commit()

        c.execute('SELECT max(lastStart) FROM start')
        lastStart = c.fetchone()[0]
        if lastStart:
            return(int(lastStart))
        else:
            if not self.manualStart:
                startVals = (0, 0)
            else:
                startVals = (self.startingId, 0)
            c.execute('INSERT INTO start VALUES(?, ?)', startVals)
            self.startDb.commit()
            return(0)

    def updateLastStart(self):
        c = self.log.cursor()
        c.execute('SELECT * FROM log ORDER BY id DESC LIMIT 1')
        maxId = c.fetchone()

        d = self.startDb.cursor()
        d.execute('''SELECT * FROM start ORDER BY lastStart DESC,
                  repetition DESC LIMIT 1''')
        lastStart = d.fetchone()

        if maxId and lastStart:
            if maxId[1] > lastStart[0]:
                newLastStart = (maxId[1], 0)
                d.execute('INSERT INTO start VALUES(?, ?)', newLastStart)
                self.startDb.commit()
            elif maxId[0] == lastStart[0]:
                newLastStart = (maxId[1], lastStart[1] + 1)
                d.execute('INSERT INTO start VALUES(?, ?)', newLastStart)
                self.startDb.commit()
            return(lastStart[1])
        else:
            return(0)

    # Function for creating temp file for detection by controller script
    # If exists and open, crawler is running
    # if exists and closed, crawler has crashed
    def makeTemp(self):
        tempdir = self.name + "/temp/"
        if not os.path.exists(tempdir):
            os.makedirs(tempdir)
        f = tempfile.NamedTemporaryFile(delete=True, encoding='utf-8',
                                        dir=tempdir, mode='w')
        return(f)

    # Function for creating log file containing ID, title, body, and hashes
    # If already exists, get most recent articleId
    def getLastEnd(self):
        c = self.log.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS log (website text, id int,
                  dateObserved text, datePublished text, body text,
                  bodyHash text, title text, titleHash text, author text)''')
        self.log.commit()

        c.execute('SELECT max(id) FROM log')
        try:
            maxId = c.fetchone()[0]
            if maxId:
                return(str(maxId))
            else:
                return("0")
        except TypeError:
            return("0")

    def checkLog(self, innerId):
        c = self.log.cursor()
        c.execute('SELECT id FROM log WHERE id = ?', (innerId,))
        id = c.fetchone()
        if id is None:
            return False
        else:
            return True

    # carve text between xxxStart and xxxEnd delimiters
    def carveText(self, context, start, stop):
        index1 = context.find(start)
        if index1 == -1:
            return ''
        else:
            index1 += len(start)
        index2 = context.find(stop)
        if index2 == -1:
            return ''
        else:
            return(context[index1:index2])

    # getArticle carves title and body text
    def getArticle(self, innerId, defaultTitleHash):
        urlToGet = self.urlStart + "/" + str(innerId) + self.urlEnd
        print("Processing : " + urlToGet)
        if self.useTor:
            r = self.session.get(urlToGet)
        else:
            r = requests.get(urlToGet)
        with open("test.txt", "w+") as test:
            test.write(r.text)
        artAuthor = self.carveText(r.text, self.authorStart, self.authorEnd)
        artDate = self.carveText(r.text, self.dateStart, self.dateEnd)
        artTitle = self.carveText(r.text, self.titleStart, self.titleEnd)
        artBody = self.carveText(r.text, self.bodyStart, self.bodyEnd)
        # hash title and compare to default hash
        m = hashlib.sha1()
        m.update(artTitle.encode('utf-8'))
        n = hashlib.sha1()
        n.update(artBody.encode('utf-8'))
        if m.hexdigest() == defaultTitleHash:
            return('', '', '', '', '', '')
        else:
            print("Success!")
            return(artTitle, artBody, artDate, artAuthor, m.hexdigest(),
                   n.hexdigest())

    # gets and hashes title and body, compares to default hashes
    def compareArticle(self, innerId):
        urlToGet = self.urlStart + "/" + str(innerId) + self.urlEnd
        print("Processing : " + urlToGet)
        if self.useTor:
            r = self.session.get(urlToGet)
        else:
            r = requests.get(urlToGet)
        artTitle = self.carveText(r.text, self.titleStart, self.titleEnd)
        artBody = self.carveText(r.text, self.bodyStart, self.bodyEnd)
        # hash title and compare to default hash
        m = hashlib.sha1()
        m.update(artTitle.encode('utf-8'))
        n = hashlib.sha1()
        n.update(artBody.encode('utf-8'))
        newTHash = m.hexdigest()
        newBHash = n.hexdigest()

        # retrieve record of id "innerId"
        # get the body hash and title hash
        # make a changelog db if it doesn't exist yet
        # check if the new hashes and the old hashes match

        c = self.log.cursor()
        c.execute('SELECT bodyHash FROM log WHERE id = ?', (innerId,))
        # this might be wrong.. could be c.fetchone()[5]
        oldBHash = c.fetchone()[0]

        c.execute('SELECT titleHash FROM log WHERE id = ?', (innerId,))
        # this might be wrong.. could be c.fetchone()[7]
        oldTHash = c.fetchone()[0]

        if not os.path.exists(self.name + "/changelog/"):
            os.makedirs(self.name + "/changelog/")
        with open(self.name + "/changelog/changelog", 'a+') as cl:
            if not newTHash == oldTHash:
                print("Title change detected in article " + str(innerId))
                cl.write(str(datetime.datetime.now()) + "|" + "title_change" +
                         "|" + str(innerId) + "|" + newBHash + "|" + artTitle +
                         "|" + newTHash + "\n")
            if not newBHash == oldBHash:
                print("Content change detected in article " + str(innerId))
                cl.write(str(datetime.datetime.now()) + "|" + "content_change"
                         + "|" + str(innerId) + "|" + newBHash + "|" + artTitle
                         + "|" + newTHash + "\n")
                return(artBody)
            return None
