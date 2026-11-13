#!/usr/bin/env python3
"""pi.py 'COMMAND': run one command on the netbooter Raspberry over SSH and print its output.

Needs paramiko (pip install paramiko). The Raspberry's address and the root password come from the
environment and are NEVER written in a file or committed:

    export PIHOST=192.168.x.y
    export PIPASS=...            # ask the cabinet's owner; it is not in any repository
    python3 pi.py 'ls /boot/roms | head'
"""
import os
import sys

import paramiko

if len(sys.argv) != 2 or "PIHOST" not in os.environ or "PIPASS" not in os.environ:
    sys.exit(__doc__)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ["PIHOST"], username="root", password=os.environ["PIPASS"], timeout=8,
          look_for_keys=False, allow_agent=False)
_, out, err = c.exec_command(sys.argv[1], timeout=170)
sys.stdout.write(out.read().decode(errors="replace"))
sys.stdout.write(err.read().decode(errors="replace"))
sys.exit(out.channel.recv_exit_status())
