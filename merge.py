#! /usr/bin/env python3

"""Merge an assembler file and the referenced source code.

GCC outputs .file and .loc markers in its assembly output. This program
re-inserts the source code from the referenced locations."""

import codecs
import subprocess
import sys
import re
import os

CHARSET = 'cp1252'


class SrcMerger(object):
    skipped = ('LB', 'LF', 'LV', ' # ', '\t.cfi_')
    file_re = re.compile('^\t' + r'\.file\s+(\d+) "(.*)"')
    loc_re = re.compile('^\t' + r'\.loc (\d+) (\d+)')
    mangled_re = re.compile(r'__Z\w+')

    def merge(self, asm, merged):
        self.out = []
        self.files = {}

        for l in codecs.open(asm):
            if any(l.startswith(s) for s in self.skipped):
                continue
            m = self.file_re.match(l)
            if m:
                self.do_file(int(m.group(1)), m.group(2))
                continue
            m = self.loc_re.match(l)
            if m:
                self.do_loc(int(m.group(1)), int(m.group(2)))
                continue
            if l == 'Letext0:\n':
                break
            self.out.append(l)
        self.out = ''.join(self.out)
        with open(merged, 'w') as out:
            out.write(self.out)
        if merged.endswith('+'):
            os.rename(merged, asm)

    def do_file(self, nr, name):
        # print(';\t\t===\t', nr, name)
        self.files[nr] = [''] + codecs.open(name, 'r', CHARSET).readlines()

    def do_loc(self, filenr, linenr):
        lines = self.files.get(filenr)
        if lines and linenr <= len(lines):
            self.out.append(';\t\t+++\t' + lines[linenr])


if __name__ == '__main__':
    del sys.argv[0]
    sm = SrcMerger()
    if sys.argv:
        for f in sys.argv:
            sm.merge(f, f + '+')
    else:
        sm.merge('/dev/stdin', '/dev/stdout')
