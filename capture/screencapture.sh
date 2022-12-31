#!/bin/bash
while :
do
    screencapture -l $1 $2$(gdate +%Y.%m.%d.%H.%M.%S.%3N).png
done