# -*- coding: UTF-8 -*-
import baseCrawler

try:
    joongangCrawler = baseCrawler.baseCrawler('joongang')
    joongangCrawler.main()
    joongangCrawler.tempfile.close()
    exit()
except:
    try:
        tempfile.close()
        exit()
    except NameError:
        exit()
