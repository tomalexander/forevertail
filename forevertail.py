#!/usr/bin/env python3
#
"""Usage:
  forevertail.py <path>...
  forevertail.py (-h | --help)
  forevertail.py --version

Options:
  -h --help  Show this screen.
  --version  Show version.
  <path>     Path to files, can contain globs
"""
from docopt import docopt
import os
import glob
import sys
import time

def get_matching_files(paths):
    all_files = []
    for p in paths:
        all_files.extend(glob.glob(os.path.expanduser(p)))
    return all_files

class TailManager(object):
    def __init__(self):
        self.files = {}

    def add_path(self, path):
        if path not in self.files:
            self.files[path] = TailFile(path)
            print("Started watching", path, file=sys.stderr)

    def get_new_lines(self):
        lines = []
        for k,v in self.files.items():
            while v.has_line():
                lines.append(v.get_line())
        return lines

class TailFile(object):
    """In an effort to be as vanilla as possible and maintain the widest portability, instead of doing something sane like kqueue, we will be counting bytes and doing seeks/reads"""
    def __init__(self, path):
        self.path = path
        self.bytes_read = 0
        self.read_buffer = b''
        self._has_line = False

    def _read_new_bytes(self):
        size_on_disk = os.path.getsize(self.path)
        if size_on_disk > self.bytes_read:
            with open(self.path, "rb") as f:
                f.seek(self.bytes_read)
                new_data = f.read(min(size_on_disk - self.bytes_read, 4096))
                if b'\n' in new_data:
                    self._has_line = True
                self.read_buffer += new_data
                self.bytes_read = f.tell()

    def has_line(self):
        if not self._has_line:
            self._read_new_bytes()
        return self._has_line

    def get_line(self):
        if not self._has_line:
            return None

        index_of_newline = self.read_buffer.index(b'\n')
        line_bytes = self.read_buffer[:index_of_newline+1] # +1 to include newline
        self.read_buffer = self.read_buffer[index_of_newline+1:]
        if not b'\n' in self.read_buffer:
            self._has_line = False
        return line_bytes

if __name__ == "__main__":
    args = docopt(__doc__, version="forevertail 0.1")
    manager = TailManager()
    while True:
        start = time.time()
        for f in get_matching_files(args["<path>"]):
            manager.add_path(f)
        for l in manager.get_new_lines():
            sys.stdout.buffer.write(l)
            sys.stdout.flush()
        end = time.time()
        run_time = end - start
        if run_time < 5:
            time.sleep(5.0 - run_time)
