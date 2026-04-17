#!/bin/env python
import subprocess
from pprint import pprint
from typing import Optional


class PassParser:
    _pass_tree: Optional[list[str | tuple]]

    def __init__(self):
        cmd = [
            "opt",
            "-S",
            "-O3",
            "--print-pipeline-passes",
            "/dev/null",
            "-o",
            "/dev/null",
        ]
        proc = subprocess.run(cmd, capture_output=True, check=True)
        self.passes_str = proc.stdout.decode().strip()
        self._pass_tree = None

    def pass_tree(self) -> list:
        if self._pass_tree is None:
            self._pass_tree = self.parse(0, len(self.passes_str))
        return self._pass_tree

    def parse(self, begin: int, end: int) -> list:
        cur = begin
        results = []
        while cur < end:
            if self.passes_str[cur] == ",":
                results.append(self.passes_str[begin:cur])
                begin = cur + 1
            elif self.passes_str[cur] == "(":
                key = self.passes_str[begin:cur]
                begin = cur + 1
                cur = self._closing_cur(cur)
                assert self.passes_str[cur - 1] == ")"
                subtree = self.parse(begin, cur - 1)
                results.append((key, subtree))
                begin = cur + 1
            cur += 1
        if begin < cur:
            results.append(self.passes_str[begin:cur])
        return results

    def _closing_cur(self, cur: int):
        cur += 1
        num_open = 1
        while num_open != 0:
            if self.passes_str[cur] == "(":
                num_open += 1
            if self.passes_str[cur] == ")":
                num_open -= 1
            cur += 1
        return cur

    @staticmethod
    def reassemble(passes: list | tuple):
        if isinstance(passes, list):
            flat = [
                p if isinstance(p, str) else PassParser.reassemble(p) for p in passes
            ]
            return ",".join(flat)
        elif isinstance(passes, tuple):
            fn, subtree = passes
            return f"{fn}({PassParser.reassemble(subtree)})"
        else:
            raise ValueError("This shouldn't happen")

    def find(self, prefix: str):
        return self._find(prefix, self.pass_tree())

    @staticmethod
    def _find(prefix: str, subtree: list[str | tuple]):
        locs = []
        for i, node in enumerate(subtree):
            if isinstance(node, tuple):
                rest = PassParser._find(prefix, node[1])
                if rest:
                    for r in rest:
                        locs.append([i] + r)
            else:
                if node.startswith(prefix):
                    locs.append([i])
        return locs

    def split(self, locs: list[int]):
        before, after = self._split(locs, self.pass_tree())
        if after[-1] == "print":
            after = after[:-1]
        return before, after

    @staticmethod
    def _split(locs: list[int], subtree: list[tuple]):
        head, *tail = locs
        l, r = [], []
        if any(tail):
            k, v = subtree[head]
            l, r = PassParser._split(tail, v)
            left = subtree[0:head] + [(k, l)]
            right = [(k, r)] + subtree[head + 1 :]
        else:
            left = subtree[0:head]
            right = subtree[head:]
        return left, right


def main():
    pp = PassParser()
    full = pp.pass_tree()
    reassembled = pp.reassemble(full)
    assert pp.passes_str == reassembled

    locs = pp.find("loop-rotate")
    print(reassembled)
    print(locs)
    l, r = pp.split(locs[1])
    print(pp.reassemble(full))
    print("----------")
    print(pp.reassemble(l))
    print("----------")
    print(pp.reassemble(r))


if __name__ == "__main__":
    main()
