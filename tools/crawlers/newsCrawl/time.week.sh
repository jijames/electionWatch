#!/bin/bash

# Convert add logs to a heatmap by hour

names=( hani joongang joongang-en joongang-jp kotimes )

for i in "${names[@]}"; do
name=$i
dir="newsCrawl"

newDate=""
newDay=""
newHour=""
newNumber=""
oldDate=""
oldDay=""
oldHour=""
oldNumber=""

echo "day,hour,value" > "/var/www/html/data/$name.week.log"

for line in $(cat "$dir/$name/adds.count" | tail -n336); do
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
          echo "$tempDay,24,$oldNumber" >> "/var/www/html/data/$name.week.log"
    elif [ "$oldHour" != "" ] ;then
          echo "$oldDay,$oldHour,$oldNumber" >> "/var/www/html/data/$name.week.log"
    fi
    oldNumber=$newNumber
    oldHour=$newHour
    oldDay=$newDay
  fi
done
if [ "$oldDay" == "0" ]; then oldDay=7; fi
if [ "$oldHour" == "00" ]; then
    tempDay=$(($oldDay-1))
    echo "$tempDay,24,$oldNumber" >> "/var/www/html/data/$name.week.log"
elif [ "$oldHour" != "" ] ;then
    echo "$oldDay,$oldHour,$oldNumber" >> "/var/www/html/data/$name.week.log"
fi

# Extra stats and averages
# Ave last 24 hours
day=$(cat "$dir/$name/adds.count" | tail -n48 | cut -d ',' -f2 | grep -v 0 | awk -F"," '{ sum += $1; n++ } END { if (n > 0) print sum / n; }')
# Ave last week
week=$(cat "$dir/$name/adds.count" | tail -n336 | cut -d ',' -f2 | grep -v 0 | awk -F"," '{ sum += $1; n++ } END { if (n > 0) print sum / n; }')
# Ave last 30 days
month=$(cat "$dir/$name/adds.count" | tail -n1440 | cut -d ',' -f2 | grep -v 0 | awk -F"," '{ sum += $1; n++ } END { if (n > 0) print sum / n; }')
# Ave last 90 days
long=$(cat "$dir/$name/adds.count" | tail -n4320 | cut -d ',' -f2 | grep -v 0 | awk -F"," '{ sum += $1; n++ } END { if (n > 0) print sum / n; }')
# Out
echo "<td>$name</td><td>$day</td><td>$week</td><td>$month</td><td>$long</td>" > /var/www/html/data/$name.stats

done
