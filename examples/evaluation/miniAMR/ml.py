#!/usr/bin/env python

import tadashi

from app import miniAMR

app = miniAMR()

print(f"{len(app.scops)}")
node = app.scops[0].schedule_tree[0]
print(node.yaml_str)

# do something with app
