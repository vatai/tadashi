#!/bin/env python
import subprocess
from pprint import pprint
from typing import Optional


class PassParser:
    _pass_tree: Optional[list]

    def __init__(self):
        cmd = ["opt", "-O3", "--print-pipeline-passes", "/dev/null", "-o", "/dev/null"]
        proc = subprocess.run(cmd, capture_output=True)
        self.passes_str = proc.stdout.decode()[:-1]
        self._pass_tree = None

    def pass_tree(self) -> list:
        if self._pass_tree is None:
            self._pass_tree = self.parse(0, len(self.passes_str))
        return self._pass_tree

    def parse(self, begin: int, end: int) -> list:
        cur = begin
        results = []
        while cur < end:
            if self.passes_str[cur] in ",":
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
        if begin < cur - 1:
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

    def reassemble(self, passes: list | tuple):
        if isinstance(passes, list):
            flat = [p if isinstance(p, str) else self.reassemble(p) for p in passes]
            return ",".join(flat)
        elif isinstance(passes, tuple):
            fn, subtree = passes
            return f"{fn}({self.reassemble(subtree)})"
        else:
            raise ValueError("This shouldn't happen")

    def find(self, prefix: str):
        return self._find(prefix, self.pass_tree())

    def _find(self, prefix: str, subtree: list):
        for i, node in enumerate(subtree):
            if isinstance(node, tuple):
                rest = self._find(prefix, node[1])
                if rest:
                    return [i] + rest
            else:
                if node.startswith(prefix):
                    return [i]

    def cut():
        pass


def main():
    pp = PassParser()
    full = pp.pass_tree()
    reassembled = pp.reassemble(full)
    assert pp.passes_str == reassembled

    # print(d.compare(pp.passes_str, reassembled))
    pprint(full)
    loc = pp.find("loop-rotate")
    print(loc)
    # pp.split([22, 3, 0])

    rv = full[22][1][3][1][0]
    print(rv)


if __name__ == "__main__":
    main()
