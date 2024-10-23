#! /bin/env python
import argparse
import random
from collections import deque, namedtuple
from itertools import count

import matplotlib.pyplot as plt
import tadashi
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gamma", default=0.5, type=float)
    return parser.parse_args()


def get_device():
    # if GPU is to be used
    return torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available() else "cpu"
    )


Transition = namedtuple("Transition", ("state", "action", "next_state", "reward"))


class ReplayMemory:
    """Cyclic buffer of bounded size that holds the transitions
    observed recently."""

    def __init__(self, capacity):
        """Init the memory."""
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition."""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        """Sample thememory."""
        return random.sample(self.memory, batch_size)

    def __len__(self):
        """Get the lenght."""
        return len(self.memory)


class DQN(nn.Module):
    """The network."""

    def __init__(self, n_observations, n_actions):
        """Init the network."""
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, x):
        """Perform a forward step in the network."""
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)


def main():
    """Run the code."""
    device = get_device()
    args = get_args()
    print(f"{device=}")
    print(f"{args=}")


if __name__ == "__main__":
    main()
