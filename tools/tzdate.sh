#!/bin/sh
#
tz() {
    printf "%-15s %-20s    " "$1" "$TZ"
    date
}

TZ=EST5EDT              tz "New York"
TZ=PST8PDT              tz "California"
TZ=GB                   tz "London"
TZ=Asia/Calcutta        tz "Hyderabad"
TZ=Japan                tz "Tokyo"
TZ=Hongkong             tz "Hong Kong"
TZ=Australia/Melbourne  tz "Melbourne"
