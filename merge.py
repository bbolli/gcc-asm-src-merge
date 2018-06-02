#! /usr/bin/env python3

"""Merge an assembler file and the referenced source code.

GCC outputs .file and .loc markers in its assembly output. This program
re-inserts the source code from the referenced locations and unmangles
the C++ identifiers."""

import codecs
import subprocess
import sys
import re
import os

CHARSET = 'cp1252'
CXXFILT = ['/usr/bin/c++filt', '-_']


class SrcMerger(object):
    skipped = ('LB', 'LF', 'LV', ' # ', '\t.cfi_')
    file_re = re.compile('^\t' + r'\.file\s+(\d+) "(.*)"')
    loc_re = re.compile('^\t' + r'\.loc (\d+) (\d+)')
    mangled_re = re.compile(r'__Z\w+')

    def merge(self, asm, merged):
        self.out = []
        self.files = {}
        mangled = set()

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
            mangled.update(self.mangled_re.findall(l))
            self.out.append(l)
        self.out = ''.join(self.out)
        if mangled:
            self.unmangle(mangled)
        with open(merged, 'w') as out:
            out.write(self.out)

    def do_file(self, nr, name):
        # print(';\t\t===\t', nr, name)
        self.files[nr] = [''] + codecs.open(name, 'r', CHARSET).readlines()

    def do_loc(self, filenr, linenr):
        lines = self.files.get(filenr)
        if lines and linenr <= len(lines):
            self.out.append(';\t\t+++\t' + lines[linenr])

    def unmangle(self, mangled):
        # sort the longest names first to avoid common prefix problems
        mangled = sorted(mangled, key=len, reverse=True)
        try:
            stdout = subprocess.check_output(CXXFILT + mangled,
                universal_newlines=True
            )
        except subprocess.CalledProcessError:
            return
        stdout = stdout.replace('> >', '>>')
        for m, u in zip(mangled, stdout.split('\n')):
            self.out = self.out.replace(m, u)


if __name__ == '__main__':
    del sys.argv[0]
    sm = SrcMerger()
    if sys.argv:
        for f in sys.argv:
            sm.merge(f, f + '+')
            os.rename(f + '+', f)
    else:
        sm.merge('/dev/stdin', '/dev/stdout')
