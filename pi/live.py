#!/usr/bin/env python3
"""live.py NETDIMM_IP ADDR [SECONDS] [--fields a,b,c] [--magic 0xNNNNNNNN]

Live figures of a NAOMI program while it runs, read through the NetDIMM (no screen overlay needed).

Runs ON the netbooter Raspberry (WiPi Netbooter), which has DragonMinded's netdimm.py in /sbin/piforce/dm_netboot.
The program must answer the NetDIMM's peek requests (libnaomi's dimmcomms.c protocol; naomi-kit and the
dc2naomi resident do it) and keep a block of 32-bit words in RAM: ADDR is the block's address, taken from the
program's symbols, for example `sh-elf-nm game.elf | grep naomi_live`. It changes with every build.

By default the block is the one of mame4all-naomi (struct naomi_live_t in src/naomi/naomi.h). For any other
layout give the word names with --fields; the first word is checked against --magic if you give one. A field called
`seconds` makes it print once per second; times in the mame4all block are tenths of a ms.

    python3 live.py 10.0.0.4 0x8c357fe8 60
    python3 live.py 10.0.0.4 0x8c100000 20 --fields magic,frame,fps --magic 0x12345678
"""
import sys
import time

sys.path.append('/sbin/piforce/dm_netboot')
from netdimm import NetDimm, PeekPokeTypeEnum as T   # noqa: E402

MAME4ALL = ('magic version seconds emulated shown busy game_loops cpu0 cpu1 cpu2 sound video upload sound_out '
            'dimm_requests emulated_worst pieces_mo pieces_pf pieces_al').split()
MAME4ALL_MAGIC = 0x454d414d   # "MAME"
TENTHS = {'cpu0', 'cpu1', 'cpu2', 'sound', 'video', 'upload'}


def main():
    args = sys.argv[1:]
    fields, magic = MAME4ALL, MAME4ALL_MAGIC
    for opt in ('--fields', '--magic'):
        if opt in args:
            i = args.index(opt)
            value = args[i + 1]
            del args[i:i + 2]
            if opt == '--fields':
                fields, magic = value.split(','), None
            else:
                magic = int(value, 0)
    if len(args) < 2:
        sys.exit(__doc__)
    dimm, base = NetDimm(args[0]), int(args[1], 0)
    seconds = int(args[2]) if len(args) > 2 else 30
    peek = lambda a: dimm.peek(a & 0x01ffffff, T.TYPE_LONG)   # the NetDIMM sees RAM without the 0x8c.. cache bits
    read = lambda: dict(zip(fields, (peek(base + 4 * i) for i in range(len(fields)))))
    live = read()
    if magic is not None and live[fields[0]] != magic:
        sys.exit('no live block at 0x%08x (first word %08x, expected %08x): wrong address, or the program is not '
                 'running' % (base, live[fields[0]], magic))
    last = None
    for _ in range(seconds * 4):
        live = read()
        stamp = live.get('seconds')
        if stamp is None or stamp != last:
            last = stamp
            text = ' '.join('%s %s' % (k, ('%.1f' % (v / 10)) if k in TENTHS else v)
                            for k, v in live.items() if k not in ('magic', 'version'))
            print(text, flush=True)
        time.sleep(0.25)


if __name__ == '__main__':
    main()
