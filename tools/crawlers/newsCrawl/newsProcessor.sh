#!/bin/bash

# News watch v0.4
# Keep track of news websites additions and changes

# Requires tor running locally (torsocks)

. inc/processing.sh

SAVEDIR="$1"
TEMPDIR=$SAVEDIR/temp/
HOLDDIR=$SAVEDIR/CHANGED/
BODYDIR=$SAVEDIR/body/
LOGFILE=$SAVEDIR/resources.db
CHANGELOG=$SAVEDIR/change.db
DB=$SAVEDIR/newsInfo.db
CRAWLURL="$2"
CRAWLURLEND="$3"    # uses sequential numeric IDs after article/ (just add 1)
CARVESTART="$4"
CARVEEND="$5"
# Default page title hash or body hash to filter
DEFAULTTHASH="$6"
DEFAULTBHASH="$7"
PRIORSTART="$8"
PRIOREND="$9"
SEARCHTYPE="${10}"
ID=$PRIORSTART
bdate=""

if [ ! $ID ]; then
    ID=0
fi

install -d $SAVEDIR
install -d $TEMPDIR
install -d $HOLDDIR
install -d $BODYDIR

if [ ! -f $LOGFILE ]; then
    echo "Time|ID|body_loc|bhash|title|thash|btitle" > $LOGFILE
fi
if [ ! -f $CHANGELOG ]; then
    echo "Time|Action|ID|newbhash|title|newthash|btitle" > $CHANGELOG
fi

if [ ! -f $DB ]; then
    # Add tables change and old later
    sqlite3 $DB "create table news (time TEXT, id TEXT, body_loc TEXT, bhash TEXT, title TEXT, thash TEXT, btime TEXT);"
fi

# If search type is hourly loop
if [ "$SEARCHTYPE" == "hr" ]; then
# Save this start (PRIOREND) for next session
echo $PRIOREND >> $SAVEDIR/startHR.db

  GO="true"
  while [ "$GO" == "true" ]; do
    ((ID++))
    echo "[I] Processing $CRAWLURL$ID$CRAWLURLEND"
    # If the ID is not in the log file already, add it
    if [ ! $(cat $LOGFILE | awk -F"|" '{print $2}' | grep -w $ID) ]; then
        getArticle $ID
        processArticle $ID
    else
        echo "[I] ID already in DB... comparing"
        #getArticle $ID
        #compareArticle $ID
    fi
    # Random sleep between 0 and 60 seconds
    sleep .$[ ( $RANDOM % 60 ) + 1 ]s

    LASTADD=$(cat $LOGFILE | awk -F"|" '{print $2}' | sort -n | tail -n1 )
    if [ $ID -gt $(( $LASTADD + 25 )) ]; then # This could be a problem for day and week
        GO="false"
    fi
  done
else
 # Generate random ordered list and loop
 echo "Not hourly"
fi

# Move this to process article then don't have to count
if [ "$SEARCHTYPE" == "hr" ]; then
    # Get the number of articles added
    LASTADD=$(cat $LOGFILE | awk -F"|" '{print $2}' | sort -n | tail -n1)
    p=0
    for i in $(seq $PRIOREND $LASTADD); do
        if [ $(awk -F"|" '{print $2}' "$LOGFILE" | grep -w "$i") ]; then
            ((p++))
        fi
    done
    echo "$(date --iso-8601=seconds),$(expr $p - 1)" >> $SAVEDIR/adds.count
fi

