# -*- coding: UTF-8 -*-
import os
import sys
import json
import tempfile
import requests
import hashlib
import datetime
import sqlite3
from random import randint
from time import sleep


class baseCrawler():
    # Generic crawler object
    def __init__(self, name):
        # load variables from json array of strings
        jsonVars = []
        self.name = name
        # change working directory to script location and find json file
        os.chdir(os.path.dirname(sys.argv[0]))
        jsonFile = self.name + "/json/" + self.name + ".json"
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
        self.defaultTitleHash = crawlVars[10]
        # log file that contains ID, title, body, hashes, etc
        self.logPath = self.name + "/log/"
        if not os.path.exists(self.logPath):
            os.makedirs(self.logPath)
        self.log = sqlite3.connect(self.logPath + "log.db")

        self.tempfile = self.makeTemp()

        self.lastEnd = self.getLastEnd()
        self.startDb = self.createStartDb()
        self.lastStart = self.getLastStart()
        # create body directory for article texts
        if not os.path.exists(self.name + "/body/"):
            os.makedirs(self.name + "/body/")
        self.bodyDir = self.name + "/body/"

        if not os.path.exists(self.name + "/changed_body/"):
            os.makedirs(self.name + "/changed_body/")
        self.changeDir = self.name + "/changed_body/"

    def main(self):
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
            # title, body, date, title hash, body hash
            t, b, d, tH, bH = self.getArticle(innerId, self.defaultTitleHash)
            if not t:
                innerId += 1
                continue
            logInfo = (innerId, str(now), b, bH, t, tH)
            c.execute('INSERT INTO log VALUES (?, ?, ?, ?, ?, ?)', logInfo)
            print('executed')
            self.log.commit()
            # write body content to HTML file.
            # seems to be encoding issue with joongang (EUC-KR, not UTF-8)
            # (FIX THIS)

            # sleep random 0 to 60 seconds
            sleep(randint(0, 60))

            innerId += 1
            lastEnd = int(self.getLastEnd())

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
            startVals = (0, 0)
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
            if maxId[0] > lastStart[0]:
                newLastStart = (maxId[0], 0)
                d.execute('INSERT INTO start VALUES(?, ?)', newLastStart)
                self.startDb.commit()
            elif maxId[0] == lastStart[0]:
                newLastStart = (maxId[0], lastStart[1] + 1)
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
        c.execute('''CREATE TABLE IF NOT EXISTS log (id int, dateObserved text,
                  body text, bodyHash text, title text, titleHash text)''')
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
        r = requests.get(urlToGet)
        artDate = self.carveText(r.text, self.dateStart, self.dateEnd)
        artTitle = self.carveText(r.text, self.titleStart, self.titleEnd)
        artBody = self.carveText(r.text, self.bodyStart, self.bodyEnd)
        # hash title and compare to default hash
        m = hashlib.sha1()
        m.update(artTitle.encode('utf-8'))
        n = hashlib.sha1()
        n.update(artBody.encode('utf-8'))
        if m.hexdigest() == defaultTitleHash:
            return('', '', '', '', '')
        else:
            print("Success!")
            return(artTitle, artBody, artDate, m.hexdigest(), n.hexdigest())

    # gets and hashes title and body, compares to default hashes
    def compareArticle(self, innerId):
        urlToGet = self.urlStart + "/" + str(innerId) + self.urlEnd
        print("Processing : " + urlToGet)
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
        oldBHash = c.fetchone()[0]

        c.execute('SELECT titleHash FROM log WHERE id = ?', (innerId,))
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


class boardCrawler(baseCrawler):
    def __init__(self, name):
        baseCrawler.__init__(self, name)
