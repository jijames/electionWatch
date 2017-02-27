#!/bin/bash
cd newsCrawl
sessionID=$(uuidgen)
echo "$(date --iso-8601=seconds) $0 $sessionID started" >> xrun.log

# News Watch is a controller for news collection
# This script gets variables from different files, and runs newsProcess.sh

# TODO
# Convert resources.db flat file to sqlite3 db
# Implement change detection to sqlite3 db
# Implement full scan option
# Implement strange URL generator
# Move last start to sqlite3 table


# Variables
NAME=""
URLSTART=""
URLEND=""
BSTART=""
BEND=""
REMTHASH=""
REMBHASH=""
LASTSTART=""
LASTEND=""
DATESEARCH=""
SEARCHTYPE="hr"

function setVariables() {
    NAME=$(echo "$1" | awk -F"," '{print $1}')
    URLSTART=$(echo "$1" | awk -F"," '{print $2}')
    URLEND=$(echo "$1" | awk -F"," '{print $3}')
    BSTART=$(echo "$1" | awk -F"," '{print $4}')
    BEND=$(echo "$1" | awk -F"," '{print $5}')
    REMTHASH=$(echo "$1" | awk -F"," '{print $6}')
    REMBHASH=$(echo "$1" | awk -F"," '{print $7}')
}

# Only applies to sequential URLs
function getLastStart() {
    startFN=""
    case $1 in
        day)
            startFN="$1/startDay.db"
            SEARCHTYPE="day"
            ;;
        week)
            startFN="$1/startWeek.db"
            SEARCHTYPE="week"
            ;;
        month)
            startFN="$1/startMonth.db"
            SEARCHTYPE="month"
            ;;
        all)
            startFN="$1/startAll.db"
            SEARCHTYPE="all"
            ;;
        *)
            startFN="$1/startHR.db"
            SEARCHTYPE="hr"
    esac
    if [ -f "$startFN" ]; then
        LASTSTART=$(cat "$startFN" | tail -n1)
    else
        LASTSTART=0
    fi
}

function getLastEnd() {
    if [ -f "$1/resources.db" ]; then
        LASTEND=$(cat $1/resources.db | awk -F"|" '{print $2}' | sort -n | tail -n1 )
    else
        LASTEND=0
    fi
}

function checkTor(){
    IP=$(torsocks curl 'https://api.ipify.org' 2> /dev/null)
    if [ "$IP" == "checkIP" ] || [ ! "$IP" ]  || [ $? -eq 6 ]; then
        echo "[I] Tor not connectied... exiting"
        #/usr/sbin/tor &
        exit 1
    else
        echo "[I] Tor connected... IP address $IP"
    fi
}

intexit() {
    kill -HUP -$$
}

hupexit() {
    echo
    echo "Interrupted"
    exit
}

trap hupexit HUP
trap intexit INT

checkTor
# Read each of the websites two crawl
SITEINFO="site.info"
if [ -f $SITEINFO ]; then
    #echo -e 'AUTHENTICATE "PASSWORD"\r\nsignal NEWNYM\r\nQUIT' | nc 127.0.0.1 9051
    #sleep 10
    while read -r line; do
        [[ $line = \#* ]] && continue
        [[ -z $line ]] && continue
        setVariables $line
        # Last start makes us do a staggard read. Check prior adds then detect new.
        getLastStart $NAME
        getLastEnd $NAME
        # There has to be a better way to call newsProcessor
        source newsProcessor.sh "$NAME" "$URLSTART" "$URLEND" "$BSTART" "$BEND" "$REMTHASH" "$REMBHASH" "$LASTSTART" "$LASTEND" "$SEARCHTYPE" &
        echo "$NAME executed with PID $!"
    done < "$SITEINFO"
fi

bash_pid=$$
children=$(ps -eo ppid | grep -w $bash_pid | wc -l)
while [ $children -gt 1 ]; do
    # Change the IP address sometimes
    if (( RANDOM % 10000 == 0 )); then
        echo -e 'AUTHENTICATE "PASSWORD"\r\nsignal NEWNYM\r\nQUIT' | nc 127.0.0.1 9051
    fi
    sleep 60
    children=$(ps -eo ppid | grep -w $bash_pid | wc -l)
done
echo "$(date --iso-8601=seconds) $0 $sessionID finished" >> xrun.log
