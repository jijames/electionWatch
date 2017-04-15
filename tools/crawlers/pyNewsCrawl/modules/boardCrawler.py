# -*- coding: UTF-8 -*-
# This crawler grabs all the links on the front page of a board and
# monitor for new links indefinitely until it is terminated manually.
# It grabs the innerId, the upload time, title, author, body content, and url
# boardCrawler needs to be initialized with a name and a function for getting
# images from post content

# Current issues:
#   - Comments do not 'bump' threads to the top of the front page. This means
#     there is no convenient way to monitor for new comments, only for new
#     posts.
#   - Cannot get comments correctly. Downloaded HTML always contains empty
#     div container without comments/cannot find comments for some reason.
#   - Main loop does not terminate on its own. Should it run for a specified
#     amount of time or run indefinitely?
#   - Able to get new IP's and random user agents using Tor, but keep getting
#     CAPTCHA page whenever making requests.

import os
import sys
import json
import sqlite3
import tempfile
import requests
import random
from time import sleep
from stem import Signal
from stem.control import Controller


class boardCrawler():
    # generic board crawler
    def __init__(self, name, method):
        self.name = name
        # set working directory to script path
        os.chdir(os.path.dirname(sys.argv[0]))
        # load json file
        jsonVars = []
        jsonPath = "json/" + self.name + ".json"
        with open(jsonPath, encoding="utf-8") as varLines:
            for line in varLines:
                jsonVars.append(json.loads(line))
        # create log db and directory
        if not os.path.exists("board/log/"):
            os.makedirs("board/log/")
        self.logDb = sqlite3.connect("board/log/log.db")
        self.c = self.logDb.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS log (id text, website text,
                       timedate text, title text, author text, body text,
                       url text)''')
        self.logDb.commit()
        # create image download directory
        if not os.path.exists(self.name + "/images/"):
            os.makedirs(self.name + "/images/")
        # set initial crawler variables
        crawlVars = jsonVars[0]
        self.baseURL = crawlVars[0]
        self.middleURL = crawlVars[1]
        self.pageCounter = 1
        self.pageURL = self.setPageURL()
        self.postStart = crawlVars[2]
        self.postEnd = crawlVars[3]
        self.maxPosts = crawlVars[4]
        self.contentStart = crawlVars[5]
        self.contentEnd = crawlVars[6]
        self.titleStart = crawlVars[7]
        self.titleEnd = crawlVars[8]
        self.authorStart = crawlVars[9]
        self.authorEnd = crawlVars[10]
        self.dateStart = crawlVars[11]
        self.dateEnd = crawlVars[12]
        self.commentStart = crawlVars[13]
        self.commentEnd = crawlVars[14]
        self.idStart = crawlVars[15]
        self.idEnd = crawlVars[16]
        self.tempfile = self.makeTemp()
        self.userAgents = self.loadUserAgent("user_agents.txt")
        self.imageCarver = method
        # initialize tor session
        # self.renewConnection()
        # print("Current Tor Session IP : \n" +
        #       self.session.get("http://httpbin.org/ip").text)

    def main(self):
        while True:
            i = 0
            urlList = []
            # to use tor:
            # self.session.get(self.pageURL).text
            # results in CAPTCHA page with todayhumor
            frontPage = requests.get(self.pageURL).text
            while i < self.maxPosts:
                i += 1
                url, frontPage = self.carveAndCut(frontPage, self.postStart,
                                                  self.postEnd)
                if url:
                    urlList.append(url)
            for each in urlList:
                print("Processing : " + each)
                postPage = requests.get(self.baseURL + each).text
                self.carvePost(postPage, each)
            sleep(random.randint(0, 60))
            # self.renewConnection()

    def carvePost(self, context, url):
        title = self.carveText(context, self.titleStart, self.titleEnd)
        content = self.carveText(context, self.contentStart,
                                 self.contentEnd)
        author = self.carveText(context, self.authorStart, self.authorEnd)
        date = self.carveText(context, self.dateStart, self.dateEnd)
        # comments = self.carveText(context, self.commentStart,
        #                           self.commentEnd)
        innerId = self.carveText(url, self.idStart, self.idEnd)
        info = (innerId, self.name, date, title, author, content,
                self.baseURL + url)
        if not self.checkLog(innerId):
            self.imageCarver(content, innerId)
            self.c.execute('INSERT INTO log VALUES (?, ?, ?, ?, ?, ?, ?)', info)
            self.logDb.commit()
            print("added to log")
        else:
            print("post already recorded, skipping...")

    def checkLog(self, innerId):
        self.c.execute('SELECT id FROM log WHERE id = ?', (innerId,))
        id = self.c.fetchone()
        if id is None:
            return False
        else:
            return True

    def loadUserAgent(self, uafile):
        userAgents = []
        with open(uafile, 'rb') as uaf:
            for ua in uaf.readlines():
                if ua:
                    userAgents.append(ua.strip()[1:-1-1])
        random.shuffle(userAgents)
        return(userAgents)

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

    def carveAndCut(self, context, start, stop):
        index1 = context.find(start)
        if index1 == -1:
            return ''
        else:
            index1 += len(start)
        index2 = context.find(stop)
        if index2 == -1:
            return ''
        else:
            return(context[index1:index2], context[index2+len(stop):])

    def renewConnection(self):
        self.session = requests.session()
        self.session.proxies = {'http':  'socks5://127.0.0.1:9050',
                                'https': 'socks5://127.0.0.1:9050'}
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="password")
            controller.signal(Signal.NEWNYM)
        userAgent = random.choice(self.userAgents)
        self.session.headers = {"User-Agent": userAgent}

    def setPageURL(self):
        return(self.baseURL + self.middleURL + str(self.pageCounter))

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
