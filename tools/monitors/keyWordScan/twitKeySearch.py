# -*- coding: UTF-8 -*-
from TwitterAPI import TwitterAPI
import sqlite3
import json
import sys
import codecs

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
OAUTH_TOKEN = ''
OAUTH_TOKEN_SECRET = ''

sqlite_file = 'twitter.db'
conn = sqlite3.connect(sqlite_file)
# Create the table if not existing
#c.execute('CREATE TABLE IF NOT EXISTS tweets')

c = conn.cursor()

conn.commit()
conn.close()

api = TwitterAPI(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

r = api.request('search/tweets', {'q':'심상정'})
for item in r:
    print json.dumps(item, indent=1)

