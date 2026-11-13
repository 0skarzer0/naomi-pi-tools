#!/usr/bin/env python3
"""add_romsinfo_rows.py ROWS.csv [--csv /boot/config/romsinfo.csv]

Runs ON the netbooter Raspberry (WiPi Netbooter). Adds rows to the WiPi's romsinfo.csv without the usual accidents:
  * makes a dated copy first (romsinfo.csv.bak_YYYYmmdd_HHMMSS),
  * adds the missing newline at the end of the file (a row appended with >> used to be glued to the last one),
  * skips rows whose ROM file name (second column) is already there.

ROWS.csv has one row per game, in the same format as romsinfo.csv (copy the row of a similar game and change it).
After this the web interface needs the file imported: see docs/trampas.md (importcsv.py).
"""
import csv
import io
import shutil
import sys
import time

path = '/boot/config/romsinfo.csv'
args = sys.argv[1:]
if '--csv' in args:
    i = args.index('--csv')
    path = args[i + 1]
    del args[i:i + 2]
if len(args) != 1:
    sys.exit(__doc__)

with open(path, newline='') as f:
    text = f.read()
have = {row[1] for row in csv.reader(io.StringIO(text)) if len(row) > 1}

with open(args[0], newline='') as f:
    new = [line for line in f.read().splitlines() if line.strip()]
add = []
for line in new:
    row = next(csv.reader([line]))
    if len(row) < 2:
        print('skipped (not a romsinfo row):', line[:60])
    elif row[1] in have:
        print('already there:', row[1])
    else:
        add.append(line)
        have.add(row[1])
if not add:
    sys.exit('nothing to add')

backup = path + '.bak_' + time.strftime('%Y%m%d_%H%M%S')
shutil.copy2(path, backup)
with open(path, 'a', newline='') as f:
    if text and not text.endswith('\n'):
        f.write('\n')
    f.write('\n'.join(add) + '\n')
print('added %d row(s) to %s (copy: %s)' % (len(add), path, backup))
