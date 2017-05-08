# -*- coding: UTF-8 -*-
# IMPORTANT: Do not run with tor, site will throw CAPTCHA
from boardCrawler import boardCrawler
import requests
import shutil
import os


def carveAndCut(context, start, stop):
    index1 = context.find(start)
    if index1 == -1:
        return('', '')
    else:
        index1 += len(start)
    contextSlice = context[index1:index1 + len(start) + 150]
    index2 = contextSlice.find(stop)
    if index2 == -1:
        print(contextSlice)
        return('', context[index1:])
    else:
        url = contextSlice[:index2]
        newContext = context[index1 + len(url):]
        print(url)
        return(url, newContext)


def imageCarver(content, innerId):
    imgs = content.count('''src="https://ncache.ilbe.com''')
    print("number of images : " + str(imgs))
    i = 0
    contentcopy = content[:]
    while i < imgs:
        i += 1
        imgurl, contentcopy = carveAndCut(contentcopy, '''src="''',
                                          '''"''')
        response = requests.get(imgurl, stream=True)
        filename = "ilbe/images/" + innerId + '/img' + str(i) + '.png'
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response


ilbeCrawler = boardCrawler("ilbe", imageCarver)
ilbeCrawler.main()
