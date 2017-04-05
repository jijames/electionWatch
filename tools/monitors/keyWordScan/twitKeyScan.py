# -*- coding: UTF-8 -*-
from TwitterAPI import TwitterAPI
import sqlite3
import json
import sys
import codecs

################################################################
#
# TODO:
#    
#
################################################################

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
OAUTH_TOKEN = ''
OAUTH_TOKEN_SECRET = ''

sqlite_file = 'search.db'
db = sqlite3.connect(sqlite_file)
db.text_factory = str
keywords = db.execute("select keyword from searchTerms")

keyDict = []
for key in keywords:
    keyDict.append(key)

db.close()

def _search(name, obj):
    """Breadth-first search for name in the JSON response and return value."""
    q = []
    q.append(obj)
    while q:
        obj = q.pop(0)
        if hasattr(obj, '__iter__') and type(obj) is not str:
            isdict = isinstance(obj, dict)
            if isdict and name in obj:
                return obj[name]
            for k in obj:
                q.append(obj[k] if isdict else k)
    else:
        return None


sqlite_file = 'twitter.db'
db = sqlite3.connect(sqlite_file)
db.text_factory = str
idVal = db.execute("SELECT pid FROM tweets ORDER BY pid DESC LIMIT 1")
idVal = idVal.fetchone()
idVal = idVal[0]

api = TwitterAPI(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

r = api.request('statuses/filter', {'track': keyDict})
values = ['screen_name', 'name', 'followers_count', 'friends_count', 'created_at', 'utc_offset', 'location', 'id', 'lang', 'text', 'retweeted_status']
rtVals = ['screen_name', 'name', 'followers_count', 'friends_count', 'created_at', 'utc_offset', 'location', 'id', 'lang', 'text', 'retweet_count']
for item in r.get_iterator():
    idVal += 1
    db.execute("INSERT INTO tweets (id) VALUES (" + str(idVal) + ")")
    db.commit()
    for value in values:
        v = _search(value, item)
        if value == 'retweeted_status' and v:
            print("------------------Original Tweet---------------------")
            for rtVal in rtVals:
                t = _search(rtVal, v)
                db.execute("UPDATE tweets SET rt{} = ? WHERE pid = ? ".format(rtVal), (t, idVal))
                print('%s: %s' % (rtVal, t))
            
        else:
            if v:
                print(value)
                print(v)
                print(idVal)
                db.execute("UPDATE tweets SET {} = ? WHERE pid = ? ".format(value), (v, idVal))
                print('%s: %s' % (value, v))
            
        
    db.commit()
    print("==================================================")

