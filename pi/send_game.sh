#!/bin/bash
# send_game.sh NETDIMM_IP IMAGE.bin.gz
#
# Runs ON the netbooter Raspberry (WiPi Netbooter). Sends an image to the NetDIMM and then keeps the
# "time hack" running, which the board needs: if timehack.py is left dead, the NAOMI restarts a few minutes later
# with "error 33 gateway is not found".
#
# It never returns (timehack.py loops forever): start it in the background, e.g.
#     nohup ./send_game.sh 10.0.0.4 /root/game.bin.gz >/dev/null 2>&1 &
# and read the result in /tmp/send_game.log.
#
# For dc2naomi games (Dreamcast on NAOMI) it uses dc2naomi_send.py, which puts the game's Visual Memory into the
# image on the fly; with plain NAOMI/homebrew images it is the same call as netdimm_send --disable-crc.
IP=${1:?NetDIMM IP}
IMG=${2:?image .bin.gz}
LOG=/tmp/send_game.log

# stop the Visual Memory watcher of the previous dc2naomi game (it brings back the saves) and the time hack.
# "[t]imehack.py" keeps pkill from matching its own command line.
[ -f /sbin/piforce/dc2naomi_vmu.py ] && python3 /sbin/piforce/dc2naomi_vmu.py stop "$IP"
pkill -f "[t]imehack.py"

if [ -f /sbin/piforce/dc2naomi_send.py ]; then
    python3 /sbin/piforce/dc2naomi_send.py "$IP" "$IMG" > "$LOG" 2>&1
else
    python3 /sbin/piforce/dm_netboot/netdimm_send "$IP" "$IMG" --disable-crc > "$LOG" 2>&1
fi

python3 /sbin/piforce/timehack.py "$IP"
