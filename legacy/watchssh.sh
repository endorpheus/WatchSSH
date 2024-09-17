#!/bin/bash
# links:		https://delightlylinux.wordpress.com/2020/10/25/bash-show-notifications-from-scripts-using-notify-send/
#	

# tail -fn0 /var/log/auth.log |
# grep --line-buffered 'Accepted' |
# while read line
# do
#     notify-send 'SSH Login Detected' "$line"
# done

# !/bin/bash

tail -fn0 /var/log/auth.log |
grep --line-buffered 'Accepted' |
while read line
do
    user=$(echo "$line" | tr -s ' ' | cut -d' ' -f9)
    notify-send -i "/home/$user/.face" "$user Just Logged In"  "$line"
done