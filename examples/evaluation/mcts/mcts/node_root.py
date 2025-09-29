from pathlib import Path

import mcts.node_node
from mcts.logger import TimestampedJsonLogger


class MCTSNode_Root(mcts.node_node.MCTSNode_Node):
    def __init__(self, prefix, *args, **kwargs):
        super().__init__(*args, **kwargs)
        prefix_dir = Path(prefix)
        prefix_dir.mkdir(exist_ok=True)
        prefix_str = str(prefix_dir / self.app.source.name)
        self.logger = TimestampedJsonLogger(prefix_str)
        self.logger.log(1, [], self.app.source.name)
        self.speedup = 1
