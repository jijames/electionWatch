# -*- coding: UTF-8 -*-
# IMPORTANT: Do not run with tor, site will throw CAPTCHA
from boardCrawler import boardCrawler
import requests
import shutil
import os


def carveAndCut(context, start, stop):
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


def imageCarver(content, innerId):
    imgs = content.count('''img src="http://thimg.todayhumor.co.kr/''')
    print("number of images : " + str(imgs))
    i = 0
    contentcopy = content[:]
    while i < imgs:
        i += 1
        imgurl, contentcopy = carveAndCut(contentcopy, '''img src="''',
                                          '''" width=''')
        response = requests.get(imgurl, stream=True)
        filename = "todayhumor/images/" + innerId + '/img' + str(i) + '.png'
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response


todayhumorCrawler = boardCrawler("todayhumor", imageCarver)
todayhumorCrawler.main()
