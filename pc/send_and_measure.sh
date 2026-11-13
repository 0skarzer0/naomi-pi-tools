#!/bin/bash
# send_and_measure.sh IMAGE.bin.gz LIVE_ADDR [SECONDS]
#
# Runs on the user's PC. Uploads a test image to the netbooter Raspberry, sends it to the NAOMI and reads the
# program's live figures (pi/live.py) for SECONDS (default 12). LIVE_ADDR is the address of the program's live block.
#
#   export PIHOST=192.168.x.y        # the Raspberry
#   export PIPASS=...                # never in a file
#   export NETDIMM=10.0.0.4          # the NetDIMM, as the Raspberry sees it (default)
#   ./send_and_measure.sh test.bin.gz 0x8c357fe8 12
#
# It waits 45 s for the transfer (a 1.3 MB homebrew image) and 25 s more for the program to start; with a big
# image (Dreamcast conversions are hundreds of MB) raise WAIT_SEND.
HERE=$(cd "$(dirname "$0")" && pwd)
IMG=${1:?image .bin.gz}
ADDR=${2:?live block address}
SECS=${3:-12}
NETDIMM=${NETDIMM:-10.0.0.4}
WAIT_SEND=${WAIT_SEND:-45}

python3 "$HERE/piput.py" "$IMG" /root/test.bin.gz \
    "$HERE/../pi/send_game.sh" /root/send_game.sh "$HERE/../pi/live.py" /root/live.py >/dev/null || exit 1
python3 "$HERE/pi.py" "chmod +x /root/send_game.sh; nohup /root/send_game.sh $NETDIMM /root/test.bin.gz >/dev/null 2>&1 &
sleep $WAIT_SEND; tail -c 60 /tmp/send_game.log"
sleep 25
python3 "$HERE/pi.py" "cd /root && timeout $((SECS + 40)) python3 live.py $NETDIMM $ADDR $SECS 2>&1 | tail -$((SECS + 2))"
