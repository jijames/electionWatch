#!/bin/bash

# Main functions for processing.

# Parser for article timestamps
function getDate(){
    case $NAME in
        hani)
           echo $(cat $1 | grep -o -P '(?<=:<\/em>).*(?=<\/span>)' | awk '{print $1"T"$2":00+09:00"}')
           ;;
        joongang)
           echo $(cat $1 | grep -o -P '(?<=입력 ).*(?=</em>)' | awk '{print $1"T"$2"+09:00"}' | tr "." "-")
           ;;
        joongang-en)
           echo $(cat $1 | grep -o -P '(?<=sServiceDate = ").*(?=";)' | awk '{print $1" " $3$2}' | sed 's/오후/PM/' | sed 's/오전/AM/' | tr -d \n | xargs -0 date --iso-8601=seconds -d )
           ;;
        joongang-jp)
           echo $(cat $1 | grep -o -P '(?<=class=\"date\">).*(?= <br \/>)' | sed "s/[年|月]/-/g; s/日/T/g; s/時/:/g; s/分/:00+09:00/g")
           ;;
        kotimes)
           echo $(cat $1 | grep -o -P "(?<=Posted\s:\s).*(?=<\/span>)" | sed 's/&nbsp;/T/' | awk '{print $1":00+09:00"}')
           ;;
        *)
           echo "0"
     esac
}

function processArticle(){
    if [ -e $TEMPDIR$1 ]; then
        UUID=$(uuid)
        DT=$(date --iso-8601=seconds)
        title=$(awk 'BEGIN{IGNORECASE=1;FS="<title>|</title>";RS=EOF} {print $2}' $TEMPDIR$1 | tr -d "|" | tr -d "\n")
        thash=$(echo $title | sha1sum | awk '{print $1}')
        bFN="$BODYDIR$1-$UUID.html"
        cat $TEMPDIR$1 | sed "1,/${CARVESTART}/d" | sed "/${CARVEEND}/q" > $bFN
        if [ ! "$(ls -l $bFN | awk '{print $5}')" == "0" ]; then   # Check if the file size is 0
          # Check for non-existing ID
          if [ ! "$(cat $LOGFILE | awk -F'|' '{print $2}' | grep -w $ID)" ]; then
          #if [ ! "sqlite3 $DB 'select * from news where id=$ID'" ]; then
              bdate=$(getDate $TEMPDIR$1)
              bhash=$(sha1sum $bFN | awk '{print $1}')
              if [ "$bhash" == "$DEFAULTBHASH" ] || [ "$thash" == "$DEFAULTTHASH" ]; then     # Check the hash of default pages that are not empty
                   rm -r $bFN
              else
                  echo "$DT|$1|$bFN|$bhash|$title|$thash|$bdate" >> $LOGFILE
              fi
          fi
        else
            rm -r $bFN
        fi
        rm -r ${TEMPDIR}*
    fi
}

# TODO - some articles may have the same title (different ID & body)
function compareArticle(){
    if [ -e $TEMPDIR$1 ]; then
        DT=$(date --iso-8601=seconds)
        newtitle=$(awk 'BEGIN{IGNORECASE=1;FS="<title>|</title>";RS=EOF} {print $2}' $TEMPDIR$1 | tr -d "|" | tr -d "\n")
        newthash=$(echo $newtitle | sha1sum | awk '{print $1}')
        cat $TEMPDIR$1 | sed "1,/${CARVESTART}/d" | sed "/${CARVEEND}/q" > ${TEMPDIR}test
        newbhash=$(sha1sum ${TEMPDIR}test | awk '{print $1}')
        fileSize=$(ls -l ${TEMPDIR}test | awk '{print $5}')    #If file size is 0, the article was removed
        if [ ! "$(cat $LOGFILE | awk -F"|" '{print $6}' | grep -w $newthash)" ]; then
            echo "[I] Title change detected in $1"
            echo "$DT|title_change|$1|$newbhash|$newtitle|$newthash" >> $CHANGELOG
        fi
        if [ ! "$(cat $LOGFILE | awk -F"|" '{print $4}' | grep -w $newbhash)" ]; then
            echo "[I] Content change detected in $1"
            echo "$DT|content_change|$1|$newbhash|$newtitle|$newthash" >> $CHANGELOG
            uuid=$(uuid)
            cp -a ${TEMPDIR}test ${HOLDDIR}${1}-${uuid}
        fi
        if [ "$fileSize" == "0" ]; then
            echo "[I] Article $1 has been removed"
            echo "$DT|deleted|$1|x|x|x" >> $CHANGELOG
        fi
        rm -r ${TEMPDIR}*
    else
        echo "[I] Article $1 has been removed"
        echo "$DT|deleted|$1|x|x|x" >> $CHANGELOG
    fi
}


function getArticle(){
    USERAGENT=$(shuf -n 1 user-agents.txt)
    torsocks wget --quiet --force-html --user-agent='${USERAGENT}' -O $TEMPDIR$1 -P $TEMPDIR "$CRAWLURL$1$CRAWLURLEND"
}
