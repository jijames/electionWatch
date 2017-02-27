#!/bin/bash

# Convert add logs to a heatmap by hour

names=( hani joongang joongang-en joongang-jp kotimes )

for i in "${names[@]}"; do

name=$i
dir="newsCrawl"

if [ -f "/var/www/html/$name.all.tmp" ]; then
    rm -r "/var/www/html/$name.all.tmp"
fi

newDate=""
newDay=""
newHour=""
newNumber=""
oldDate=""
oldDay=""
oldHour=""
oldNumber=""

for line in $(cat "$dir/$name/adds.count"); do
  newDate=$(echo "$line" | cut -c 1-10)
  newDay=$(date -d "$newDate" +%w)
  newHour=$(echo "$line" | cut -c 12-13)
  newNumber=$(echo "$line" | awk -F"," '{print $2}')

  if [ "$oldHour" == "$newHour" ]; then
      oldNumber=$(($newNumber + $oldNumber))
  else
      if [ "$oldDay" == "0" ]; then oldDay=7; fi
      if [ "$oldHour" == "00" ]; then
          if [ "$oldDay" == "1" ]; then
              tempDay=7
          else
              tempDay=$(($oldDay-1))
          fi
          echo "$tempDay,24,$oldNumber" >> "/var/www/html/$name.all.tmp"
      elif [ "$oldHour" != "" ]; then
          echo "$oldDay,$oldHour,$oldNumber" >> "/var/www/html/$name.all.tmp"
      fi
      oldNumber=$newNumber
      oldHour=$newHour
      oldDay=$newDay
  fi
done
if [ "$oldDay" == "0" ]; then oldDay=7; fi
if [ "$oldHour" == "00" ]; then
    tempDay=$(($oldDay-1))
    echo "$tempDay,24,$oldNumber" >> "/var/www/html/$name.all.tmp"
elif [ "$oldHour" != "" ]; then
    echo "$oldDay,$oldHour,$oldNumber" >> "/var/www/html/$name.all.tmp"
fi

# Combine into one chart
echo "day,hour,value" > "/var/www/html/data/$name.all.log"
for line in $(cat "/var/www/html/$name.all.tmp" | cut -d',' -f1,2 | sort | uniq); do
    count=$(cat "/var/www/html/$name.all.tmp" | grep "$line" | cut -d ',' -f 3 | awk '{s+=$1} END {print s}')
    echo "$line,$count" >> "/var/www/html/data/$name.all.log"
done
rm -r "/var/www/html/$name.all.tmp"

done
