#!/usr/bin/env python3
"""live.py [NETDIMM_IP] ADDR [watch [SECONDS] | SECONDS | log | words | reset] [--fields a,b,c] [--magic 0xN] [--window0]

Live figures of a program running on the NAOMI, read through the NetDIMM: the one reader for every project.
Runs ON the netbooter Raspberry (WiPi), which has DragonMinded's netdimm.py in /sbin/piforce/dm_netboot.

The program must answer the NetDIMM's peek requests (libnaomi's dimmcomms.c protocol) and keep a block of 32-bit
words in RAM. ADDR is the block's address, from the program's symbols (`sh-elf-nm prog.elf | grep live`) or its
console; it changes with every build. The block is recognised by its first word:

  "NKLV"  naomi-kit games (OutRunners...): nk_live_head names the game's own words; console ring
  "MAME"  mame4all-naomi (naomi_live_t in src/naomi/naomi.h); times in tenths of a ms
  "NEST"  Daytona USA native NAOMI port (nm_naomi_live_t, daytona-arcade-recomp branch naomi-native); console ring
  "LIVE"  KallistiOS programs built with dc2naomi's NAOMI_HOST patch (Mario Kart 64: homebrew/mk64 in dc2naomi):
          vblank PC samples, 8 KB of everything KallistiOS printed, the exception that stopped it
  other   only with --fields NAME,NAME,... (and --magic to check the first word)

  watch [N]  (default) one line a second for N seconds (default 30). "LIVE": until the program stops, then the
             exception and the log. A bare number N means "watch N"; "fps" is the same as "watch".
  log        the program's console / log ring ("NKLV", "NEST", "LIVE")
  words      every word of the block once, by name
  reset      "NEST": start the worst second over

NETDIMM_IP defaults to $NK_DIMM, or 10.0.0.4 (the Crazy Taxi cabinet). --window0 first sets the address window of
dc2naomi's resident / NAOMI_HOST programs back to RAM (a poke at 0x01fffffc): only for those, in case a peek tool
was stopped half way (on any other program that poke writes the last word of RAM). Do not leave timehack.py running
while reading: with both talking to the NetDIMM, peeks came back with stale values.

    python3 live.py 10.0.0.4 0x8c357fe8 60                   # mame4all, a minute
    python3 live.py 0x8c2a1b40 log                            # a naomi-kit game's console, NetDIMM 10.0.0.4
    python3 live.py 10.0.0.4 0x8c173164 fps 60               # Daytona native
    python3 live.py 10.0.0.4 0x8c10d868                       # Mario Kart 64: until it stops, then its log
    python3 live.py 10.0.0.4 0x8c100000 20 --fields magic,frame,fps --magic 0x12345678
"""
import os
import struct
import sys
import time

sys.path.append('/sbin/piforce/dm_netboot')
from netdimm import NetDimm, PeekPokeTypeEnum as T   # noqa: E402

WINDOW = 0x01fffffc


class Block:
    """A live block in the board's RAM, read word by word through the NetDIMM."""

    def __init__(self, dimm, base):
        self.dimm, self.base = dimm, base

    def peek(self, address):
        return self.dimm.peek(address & 0x01ffffff, T.TYPE_LONG)   # the NetDIMM sees RAM without the 0x8c.. bits

    def poke(self, address, value):
        self.dimm.poke(address & 0x01ffffff, T.TYPE_LONG, value)

    def word(self, offset):
        return self.peek(self.base + offset)

    def words(self, names, first=0):
        return dict(zip(names, (self.word(first + 4 * i) for i in range(len(names)))))

    def string(self, address, limit=1024):
        out = b''
        while len(out) < limit:
            out += struct.pack('<I', self.peek(address + len(out)))
            if b'\0' in out:
                break
        return out.split(b'\0', 1)[0].decode('ascii', 'replace')

    def ring(self, lines, count, width, next_ptr):
        """A console ring of COUNT lines of WIDTH bytes; the index of the line being written is at NEXT_PTR."""
        written = self.peek(next_ptr)
        for index in range(max(0, written - count + 1), written + 1):
            at = lines + (index % count) * width
            raw = b''.join(struct.pack('<I', self.peek(at + 4 * k)) for k in range(width // 4))
            line = raw.split(b'\0', 1)[0].decode('ascii', 'replace')
            if line:
                yield line


def every_second(seconds, read, show):
    """Read 4 times a second and print when the block's own second counter changes."""
    last = None
    for _ in range(seconds * 4):
        values = read()
        stamp = values.get('seconds')
        if stamp is None or stamp != last:
            last = stamp
            print(show(values), flush=True)
        time.sleep(0.25)


# ---- "MAME": mame4all-naomi -------------------------------------------------------------------------------------
MAME = ('magic version seconds emulated shown busy game_loops cpu0 cpu1 cpu2 sound video upload sound_out '
        'dimm_requests emulated_worst pieces_mo pieces_pf pieces_al').split()


def mame(block, verb, seconds):
    t = lambda v: v / 10
    if verb == 'words':
        for k, v in block.words(MAME).items():
            print('%-15s %d' % (k, v))
        return
    every_second(seconds, lambda: block.words(MAME), lambda v: (
        '%4ds emu %2d shown %2d busy %3d%% loops %2d | cpu0 %4.1f cpu1 %4.1f cpu2 %4.1f snd %4.1f vid %4.1f upl %4.1f '
        '| worst %2d | quads %d/%d/%d' % (v['seconds'], v['emulated'], v['shown'], v['busy'], v['game_loops'],
                                         t(v['cpu0']), t(v['cpu1']), t(v['cpu2']), t(v['sound']), t(v['video']),
                                         t(v['upload']), v['emulated_worst'], v['pieces_mo'], v['pieces_pf'],
                                         v['pieces_al'])))


# ---- "NKLV": naomi-kit (naomi_kit.h, nk_live_head; same reading as naomi-kit's tools/pi/nk_live.py) --------------
NK_HEAD = ('magic version game names count seconds dimm_requests log_lines log_count log_width log_next heap_left '
           'misaligned profile_pcs profile_count profile_size test_inputs inputs frames_alive profile_prs profile_waiting').split()
NK_HEAD_WORDS = 24


def naomi_kit(block, verb, seconds):
    head = block.words(NK_HEAD)
    names = block.string(head['names']).split()[:head['count']] if head['names'] else []
    game = lambda: block.words(names, 4 * NK_HEAD_WORDS)
    if verb == 'log':
        for line in block.ring(head['log_lines'], head['log_count'], head['log_width'], head['log_next']):
            print(line)
    elif verb == 'words':
        version = head['version']
        print('version %08x%s  game %s' % (version, '  (AN EXCEPTION: %03x)' % (version & 0xffff)
                                            if version >> 16 == 0xdead else '',
                                            head['game'].to_bytes(4, 'little').decode('ascii', 'replace')))
        for name in ('seconds', 'dimm_requests', 'heap_left', 'misaligned', 'profile_count', 'inputs', 'frames_alive'):
            print('%-14s %d' % (name, head[name]))
        for name, value in game().items():
            print('%-14s %d' % (name, value))
    else:
        def read():
            values = block.words(NK_HEAD)
            values['game_words'] = game()
            return values

        def show(v):
            i = v['inputs']
            words = '  '.join('%s %d' % item for item in v['game_words'].items())
            return '%5ds  %s  | misaligned %d  heap %d KB  wheel %02x gas %02x brake %02x buttons %02x' % (
                v['seconds'], words, v['misaligned'], v['heap_left'] // 1024, i & 255, i >> 8 & 255, i >> 16 & 255,
                i >> 24)
        every_second(seconds, read, show)


# ---- "NEST": Daytona USA native NAOMI port --------------------------------------------------------------------
NEST = ('magic version seconds fps vbls fps_worst frames_total frame_us render_us dimm_requests '
        'log_lines log_count log_width log_next heap_left').split()


def daytona(block, verb, seconds):
    if verb == 'reset':
        block.poke(block.base + 4 * NEST.index('fps_worst'), 0)
        print('worst second reset')
    elif verb == 'log':
        v = block.words(NEST)
        for line in block.ring(v['log_lines'], v['log_count'], v['log_width'], v['log_next']):
            print(line)
    elif verb == 'words':
        for k, v in block.words(NEST).items():
            print('%-13s %d' % (k, v))
    else:
        every_second(seconds, lambda: block.words(NEST), lambda v: (
            '%5ds  %2d fps (%d vblanks)  worst %2d  frame %5.2f ms  render %5.2f ms  heap left %d KB' % (
                v['seconds'], v['fps'], v['vbls'], v['fps_worst'], v['frame_us'] / 1000, v['render_us'] / 1000,
                v['heap_left'] // 1024)))


# ---- "LIVE": KallistiOS + NAOMI_HOST (dc2naomi homebrew/mk64/kos-680d1862-naomi_host.patch, maple_utils.c) -------
KOS = 'magic vbls served last_cmd istext irq_pc irq_pr irq_sr main_pc main_pr'.split()
KOS_TAIL = 'thd_polls halted halt_pr halt_why log_pos'.split()            # at 0x68, after pc_ring[16]
KOS_EXC = 'code evt pc pr sr'.split()                                       # at 0x7c, then r[16], EXPEVT INTEVT TEA


def kos_log(block):
    pos = block.word(0x78)
    raw = b''.join(struct.pack('<I', block.word(0xdc + 4 * i)) for i in range(2048))
    log = raw[pos & 8191:] + raw[:pos & 8191] if pos > 8192 else raw[:pos]
    return log.replace(b'\0', b'').decode('latin-1')


def kos_exception(block):
    ex = [block.word(0x7c + 4 * i) for i in range(24)]
    if not (ex[0] or ex[2]):
        return None
    return ('exception code=%d evt=%04x PC=%08x PR=%08x SR=%08x\n' % tuple(ex[:5]) +
            '  R0-R7  ' + ' '.join('%08x' % x for x in ex[5:13]) + '\n' +
            '  R8-R15 ' + ' '.join('%08x' % x for x in ex[13:21]) + '\n' +
            '  EXPEVT=%08x INTEVT=%08x TEA=%08x' % tuple(ex[21:24]))


def kos(block, verb, seconds):
    if verb == 'log':
        print(kos_log(block))
        return
    if verb == 'words':
        for k, v in block.words(KOS).items():
            print('%-9s %08x' % (k, v))
        print('pc_ring   ' + ' '.join('%08x' % block.word(0x28 + 4 * i) for i in range(16)))
        for k, v in block.words(KOS_TAIL, 0x68).items():
            print('%-9s %d' % (k, v))
        return
    t0, last = time.time(), None
    while time.time() - t0 < seconds:
        v, tail = block.words(KOS), block.words(KOS_TAIL, 0x68)
        line = ('vbls %d  peeks %d  irq pc %08x pr %08x  main pc %08x pr %08x  thd %d' %
                (v['vbls'], v['served'], v['irq_pc'], v['irq_pr'], v['main_pc'], v['main_pr'], tail['thd_polls']))
        if line != last:
            print('t+%3ds  %s' % (time.time() - t0, line), flush=True)
            last = line
        if tail['halted']:
            print('HALTED (%s, called from %08x)' % ({1: 'abort', 2: 'exit', 3: 'reboot'}.get(tail['halt_why'], '?'),
                                                    tail['halt_pr']))
            break
        time.sleep(2)
    exc = kos_exception(block)
    if exc:
        print(exc)
    print('----- log -----')
    print(kos_log(block))


FORMATS = {0x564c4b4e: naomi_kit, 0x454d414d: mame, 0x5453454e: daytona, 0x4556494c: kos}


def generic(block, verb, seconds, fields):
    tenths = {'cpu0', 'cpu1', 'cpu2', 'sound', 'video', 'upload'}
    if verb == 'words':
        for k, v in block.words(fields).items():
            print('%-15s %d' % (k, v))
        return
    every_second(seconds, lambda: block.words(fields), lambda v: ' '.join(
        '%s %s' % (k, ('%.1f' % (x / 10)) if k in tenths else x) for k, x in v.items() if k not in ('magic', 'version')))


def main():
    args = sys.argv[1:]
    fields = magic = None
    window0 = '--window0' in args
    if window0:
        args.remove('--window0')
    for opt in ('--fields', '--magic'):
        if opt in args:
            i = args.index(opt)
            value = args[i + 1]
            del args[i:i + 2]
            if opt == '--fields':
                fields = value.split(',')
            else:
                magic = int(value, 0)
    if not args:
        sys.exit(__doc__)
    if args[0].count('.') == 3:                      # an IP first (naomi-pi-tools, mame4all, Daytona, dc2naomi)
        ip, args = args[0], args[1:]
    else:                                            # naomi-kit's way: live.py ADDR ...
        ip = os.environ.get('NK_DIMM', '10.0.0.4')
    if not args:
        sys.exit(__doc__)
    base, rest = int(args[0], 0), args[1:]
    verb, seconds = 'watch', 30
    if rest and rest[0].isdigit():
        seconds = int(rest[0])
    elif rest:
        verb = {'fps': 'watch'}.get(rest[0], rest[0])
        if len(rest) > 1 and rest[1].isdigit():
            seconds = int(rest[1])
    if verb not in ('watch', 'log', 'words', 'reset'):
        sys.exit('unknown: %s\n%s' % (verb, __doc__))

    block = Block(NetDimm(ip), base)
    if window0:
        block.poke(WINDOW, 0)
    first = block.word(0)
    if fields:
        if magic is not None and first != magic:
            sys.exit('no live block at 0x%08x (first word %08x, expected %08x): wrong address, or the program is not '
                     'running' % (base, first, magic))
        return generic(block, verb, seconds, fields)
    reader = FORMATS.get(first)
    if not reader:
        sys.exit('no known live block at 0x%08x (first word %08x = %r): wrong address, the program is not running, or '
                 'another layout (give its words with --fields)'
                 % (base, first, first.to_bytes(4, 'little').decode('ascii', 'replace')))
    if verb == 'reset' and reader is not daytona:
        sys.exit('reset is only for the Daytona block ("NEST")')
    reader(block, verb, seconds)


if __name__ == '__main__':
    main()
