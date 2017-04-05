#!/bin/bash

sqlite3 twitter.db 'create table tweets (pid integer primary key autoincrement, screen_name text, name text, followers_count int, friends_count int, created_at datetime, utc_offset int, location text, id text, lang text, text text, retweet_count int, rtscreen_name text, rtname text, rtfollowers_count int, rtfriends_count, rtcreated_at datetime, rtutc_offset int, rtlocation text, rtid text, rtlang text, rttext text, rtretweet_count int);'
sqlite3 twitter.db 'insert into tweets (screen_name) values ("default");'
