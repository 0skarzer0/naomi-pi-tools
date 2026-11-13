#!/usr/bin/env python3
"""piput.py LOCAL REMOTE [LOCAL REMOTE ...]: copy files to the netbooter Raspberry over SFTP.

Same environment as pi.py (PIHOST, PIPASS; never in a file). Prints the size of each file on the Raspberry.

    python3 piput.py game.bin.gz /boot/roms/game.bin.gz live.py /root/live.py
"""
import os
import sys

import paramiko

if len(sys.argv) < 3 or len(sys.argv) % 2 != 1 or "PIHOST" not in os.environ or "PIPASS" not in os.environ:
    sys.exit(__doc__)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ["PIHOST"], username="root", password=os.environ["PIPASS"], timeout=8,
          look_for_keys=False, allow_agent=False)
sftp = c.open_sftp()
for i in range(1, len(sys.argv), 2):
    sftp.put(sys.argv[i], sys.argv[i + 1])
    print("put", sys.argv[i + 1], sftp.stat(sys.argv[i + 1]).st_size)
