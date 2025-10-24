#!/bin/bash

DAY=$(date | awk '{print $1}')

musicplayer() {
        /home/user/scripts/musicplayer.py \
                /home/user/"$1" \
                -r \
                -vv \
                -p ffplay \
                -t "$2" "$3" \
                --no-controls \
                --fade 5 \
                --enable-log \
                --terminate $4
}

if   [[ $DAY == 'Tue' || $DAY == 'Thu' ]]; then
        musicplayer "Music/playlist1" "05:10" "09:30" "--wait"
        musicplayer "Music/playlist2" "05:10" "12:00" "--wait"
        musicplayer "Music/playlist1" "05:10" "22:00"
elif [[ $DAY == 'Wed' || $DAY == 'Fri' ]]; then
        musicplayer "Music/pop2024" "05:10" "11:00" "--wait"
        musicplayer "Music/playlist1" "05:10" "13:00" "--wait"
        musicplayer "Music/pop2024" "05:10" "19:00" "--wait"
        musicplayer "Music/playlist2" "05:10" "22:00"
elif [[ $DAY == 'Sat' ]]; then
        musicplayer "Music/playlist1" "05:10" "22:00"
elif [[ $DAY == 'Sun' ]]; then
        musicplayer "Music/2010s_hits" "05:10" "11:30" "--wait"
        musicplayer "Music/playlist1" "05:10" "22:00"
else
        musicplayer "Music/playlist1" "05:10" "10:00" "--wait"
        musicplayer "Music/2010s_hits" "05:10" "13:00" "--wait"
        musicplayer "Music/playlist1" "05:10" "22:00"
fi
