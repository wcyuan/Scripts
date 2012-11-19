#!/bin/sh
#
export TZ
ECHO="echo -e"

TZ=EST5EDT
$ECHO "New York\t$TZ\t\t\t\c"; date
TZ=PST8PDT
$ECHO "California\t$TZ\t\t\t\c"; date
TZ=GB
$ECHO "London\t\t$TZ\t\t\t\c"; date
TZ=Asia/Calcutta
$ECHO "Hyderabad\t$TZ\t\t\c"; date
TZ=Japan
$ECHO "Tokyo\t\t$TZ\t\t\t\c"; date
TZ=Hongkong
$ECHO "Hong Kong\t$TZ\t\t\c"; date
TZ=Australia/Melbourne
$ECHO "Melbourne\t$TZ\t\c"; date
