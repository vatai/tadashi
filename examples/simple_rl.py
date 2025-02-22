#! /bin/env python
#
# Adopted from https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html#dqn-algorithm


# THIS FILE IS NOT FINISHED!
import argparse
import math
import random
import re
from collections import deque, namedtuple
from itertools import count, product
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import tadashi
import tadashi.apps
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import yaml

CURRENT_MARK = "CURRENT_"

torch.manual_seed(42)
random.seed(42)
np.random.seed(42)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num_episodes",
        default=100,
        type=int,
        help="The number episodes",
    )
    parser.add_argument(
        "--batch_size",
        default=128,
        type=int,
        help="The number of transitions sampled from the replay buffer",
    )
    parser.add_argument(
        "--gamma",
        default=0.99,
        type=float,
        help="The discount factor as mentioned in the previous section",
    )
    parser.add_argument(
        "--eps_start",
        default=0.9,
        type=float,
        help="The starting value of epsilon",
    )
    parser.add_argument(
        "--eps_end",
        default=0.05,
        type=float,
        help="The final value of epsilon",
    )
    parser.add_argument(
        "--eps_decay",
        default=1000,
        type=float,
        help="The rate of exponential decay of epsilon, higher means a slower decay",
    )
    parser.add_argument(
        "--tau",
        default=0.005,
        type=float,
        help="The update rate of the target network",
    )
    parser.add_argument(
        "--lr",
        default=1e-4,
        type=float,
        help="The learning rate of the ``AdamW`` optimizer",
    )
    parser.add_argument(
        "--embedding_size",
        default=64,
        type=int,
        help="Size of embeddings",
    )
    parser.add_argument(
        "--lstm_hidden_size",
        default=128,
        type=int,
        help="Size of hidden state vectors",
    )
    parser.add_argument(
        "--num_lstm_layers",
        default=5,
        type=int,
        help="Number of LSTM layers",
    )
    parser.add_argument(
        "--num_mcts_layers",
        default=5,
        type=int,
        help="Number of MCTS layers (1 layer = 3 sublayers)",
    )
    parser.add_argument(
        "--node_top_k",
        default=5,
        type=int,
        help="Top-k for the node (sub)layer",
    )
    parser.add_argument(
        "--tr_top_k",
        default=3,
        type=int,
        help="Top-k for the transformation (sub)layer",
    )
    parser.add_argument(
        "--args_top_k",
        default=5,
        type=int,
        help="Top-k for the args (sub)layer",
    )
    return parser.parse_args()


def get_device():
    # if GPU is to be used
    return torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available() else "cpu"
    )


def tr_args(node, tr):
    if tr == tadashi.TRANSFORMATIONS[tadashi.TrEnum.TILE]:
        tile_size = random.choice([2**x for x in range(5, 12)])
        return [tile_size]
    tr = tadashi.TRANSFORMATIONS[tr]
    print(f"{tr=}")
    lubs = tr.available_args(node)
    print(f"{lubs=}")
    args = []
    for lub in lubs:
        if isinstance(lub, tadashi.LowerUpperBound):
            lb, ub = lub
            if lb is None:
                lb = -5
            if ub is None:
                ub = 5
            args = product(args, range(lb, ub))
        else:
            args = product(args, [t.value for t in lub])

    return args


class ActionSpace:
    @property
    def n(self):
        return 42

    def sample(self):
        return [1]


class Env:
    steps_done = 0

    def step(self, action):
        return "obs", 0.42, True, True, None

    def reset(self):
        return [1], [2]

    @property
    def action_space(self):
        return ActionSpace()


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


def select_action(args, env, policy_net, state):
    sample = random.random()
    eps_threshold = args.eps_end + (args.eps_start - args.eps_end) * math.exp(
        -1.0 * env.steps_done / args.eps_decay
    )
    env.steps_done += 1
    if sample > eps_threshold:
        with torch.no_grad():
            # t.max(1) will return the largest column value of each row.
            # second column on max result is index of where max element was
            # found, so we pick action with the larger expected reward.
            return policy_net(state).max(1).indices.view(1, 1)
    else:
        return torch.tensor(
            [[env.action_space.sample()]],
            device=get_device(),
            dtype=torch.long,
        )


def plot_durations(episode_durations, show_result=False):
    plt.figure(1)
    durations_t = torch.tensor(episode_durations, dtype=torch.float)
    if show_result:
        plt.title("Result")
    else:
        plt.clf()
        plt.title("Training...")
    plt.xlabel("Episode")
    plt.ylabel("Duration")
    plt.plot(durations_t.numpy())
    # Take 100 episode averages and plot them too
    if len(durations_t) >= 100:
        means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
        means = torch.cat((torch.zeros(99), means))
        plt.plot(means.numpy())

    plt.gcf()
    plt.show()


def optimize_model(args, memory, policy_net, target_net, optimizer):
    device = get_device()
    if len(memory) < args.batch_size:
        return
    transitions = memory.sample(args.batch_size)
    # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for
    # detailed explanation). This converts batch-array of Transitions
    # to Transition of batch-arrays.
    batch = Transition(*zip(*transitions))

    # Compute a mask of non-final states and concatenate the batch elements
    # (a final state would've been the one after which simulation ended)
    non_final_mask = torch.tensor(
        tuple(map(lambda s: s is not None, batch.next_state)),
        device=device,
        dtype=torch.bool,
    )
    non_final_next_states = torch.cat([s for s in batch.next_state if s is not None])
    state_batch = torch.cat(batch.state)
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat(batch.reward)

    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken. These are the actions which would've been taken
    # for each batch state according to policy_net
    state_action_values = policy_net(state_batch).gather(1, action_batch)

    # Compute V(s_{t+1}) for all next states.
    # Expected values of actions for non_final_next_states are computed based
    # on the "older" target_net; selecting their best reward with max(1).values
    # This is merged based on the mask, such that we'll have either the expected
    # state value or 0 in case the state was final.
    next_state_values = torch.zeros(args.batch_size, device=device)
    with torch.no_grad():
        next_state_values[non_final_mask] = (
            target_net(non_final_next_states).max(1).values
        )
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * args.gamma) + reward_batch

    # Compute Huber loss
    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    # In-place gradient clipping
    torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
    optimizer.step()


def main():
    """Run the code."""
    ### Begin COPY ###
    device = get_device()
    args = get_args()
    env = Env()
    # Get number of actions from gym action space
    n_actions = env.action_space.n
    # Get the number of state observations
    state, info = env.reset()
    n_observations = len(state)

    policy_net = DQN(n_observations, n_actions).to(device)
    target_net = DQN(n_observations, n_actions).to(device)
    target_net.load_state_dict(policy_net.state_dict())

    optimizer = optim.AdamW(policy_net.parameters(), lr=args.lr, amsgrad=True)
    memory = ReplayMemory(10000)

    episode_durations = []
    for i_episode in range(args.num_episodes):
        print(f"{i_episode=}")
        # Initialize the environment and get its state
        state, info = env.reset()
        state = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
        for t in count():
            action = select_action(args, env, policy_net, state)
            observation, reward, terminated, truncated, _ = env.step(action.item())
            reward = torch.tensor([reward], device=device)
            done = terminated or truncated

            if terminated:
                next_state = None
            else:
                next_state = torch.tensor(
                    observation, dtype=torch.float32, device=device
                ).unsqueeze(0)

            # Store the transition in memory
            memory.push(state, action, next_state, reward)

            # Move to the next state
            state = next_state

            # Perform one step of the optimization (on the policy network)
            optimize_model(args, memory, policy_net, target_net, optimizer)

            # Soft update of the target network's weights
            # θ′ ← τ θ + (1 −τ )θ′
            target_net_state_dict = target_net.state_dict()
            policy_net_state_dict = policy_net.state_dict()
            for key in policy_net_state_dict:
                ps = policy_net_state_dict[key]
                ts = target_net_state_dict[key]
                target_net_state_dict[key] = ps * args.tau + ts * (1 - args.tau)
            target_net.load_state_dict(target_net_state_dict)

            if done:
                episode_durations.append(t + 1)
                plot_durations(episode_durations)
                break

    print("Complete")
    plot_durations(episode_durations, show_result=True)
    plt.ioff()
    plt.show()
    ### End COPY ###

    print(f"{device=}")
    print(f"{args=}")


def get_polybench_list():
    base = Path("examples/polybench/")
    result = []
    for p in base.glob("**"):
        if Path(p / (p.name + ".c")).exists():
            result.append(p.relative_to(base))
    return base, result


def tokenize_isl_str(isl_str: str):
    tokens = [
        r"n",
        r"ni",
        r"nj",
        r"nk",
        r"i",
        r"j",
        r"k",
        r"\d+",
        r"\+",
        r"\- ",
        r"\*",
        r"\/",
        r"=",
        r"<",
        r"<=",
        r">",
        r">=",
        r"mod",
        r"and",
        r"or",
        r'"',
        r"\(",
        r"\)",
        r"\[",
        r"\]",
        r"\}",
        r"\{",
        r"->",
        r",",
        r";",
        r":",
        r"S_\d+",
        r"L_\d+",
    ]
    pattern = re.compile("|".join([f"^{t}" for t in tokens]))

    result = []
    match = re.match(pattern, isl_str.strip())
    while isl_str and match:
        pos = match.span()[1]
        result.append(isl_str[:pos].strip())
        isl_str = isl_str[pos:].strip()
        match = re.match(pattern, isl_str.strip())
    if isl_str.strip():
        raise NotImplementedError(f"ISL string not fully parsed. Remaining: {isl_str}")
    return result


def traverse(yaml_dict: dict, level: int = 0) -> list:
    result = []
    if isinstance(yaml_dict, str):
        if yaml_dict.endswith("leaf"):
            current = yaml_dict.startswith(CURRENT_MARK)
            if current:
                yaml_dict = yaml_dict.replace(CURRENT_MARK, "")
            return [(level, current, yaml_dict)]
        return [(level, False, token) for token in tokenize_isl_str(yaml_dict)]
    elif isinstance(yaml_dict, list):
        for item in yaml_dict:
            result += traverse(item, level + 1)
    else:
        for k, v in yaml_dict.items():
            if k == "child":
                result += traverse(v, level + 1)
            else:
                current = False
                if k.startswith(CURRENT_MARK):
                    k = k.replace(CURRENT_MARK, "")
                    current = True
                result.append((level, current, k))
                result += traverse(v, level)
    return result


def tokenize(node: tadashi.Node, vocab: Optional[list] = None) -> dict:
    pattern = re.compile(r"# YOU ARE HERE\n *")
    yaml_str = re.sub(pattern, CURRENT_MARK, node.yaml_str)
    yaml_dict = yaml.load(yaml_str, yaml.SafeLoader)
    tokens = traverse(yaml_dict)
    if not vocab:
        vocab = ["leaf"]
        for token in tokens:
            if token[-1] not in vocab:
                vocab.append(token[-1])
    return dict(vocab=vocab, tokens=tokens)


class NodeNN(nn.Module):
    def __init__(self, scop: tadashi.Scop, args: argparse.Namespace):
        super().__init__()
        device = get_device()
        self.scop = scop
        tokenizer = tokenize(scop.schedule_tree[0])
        self.vocab = tokenizer["vocab"]
        self.rnn = nn.LSTM(
            input_size=args.embedding_size,
            hidden_size=args.lstm_hidden_size,
            num_layers=args.num_lstm_layers,
            device=device,
        )
        self.embeddings = nn.Embedding(
            len(self.vocab),
            args.embedding_size,
            device=device,
        )
        self.linear = nn.Linear(
            in_features=args.lstm_hidden_size,
            out_features=1,
            device=device,
        )

    def forward(self, node: tadashi.Node):
        device = get_device()
        tokens = tokenize(node, self.vocab)["tokens"]
        indices = [self.vocab.index(token) for _, _, token in tokens]
        indices_tensor = torch.LongTensor(indices).to(device)
        encoded, (h0, c0) = self.rnn(self.embeddings(indices_tensor))
        return h0[-1, :]


class NodeHeadNN(nn.Module):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.linear = nn.Linear(
            in_features=args.lstm_hidden_size,
            out_features=1,
            device=get_device(),
        )

    def forward(self, ht: torch.Tensor):
        return self.linear(ht)


class TranNN(nn.Module):
    def __init__(self, node_nn: NodeNN, args: argparse.Namespace):
        super().__init__()
        device = get_device()
        self.node_nn = node_nn
        in_size = args.lstm_hidden_size + len(tadashi.TrEnum)
        self.linear = nn.Linear(in_features=in_size, out_features=1, device=device)

    def forward(self, node: tadashi.Node, tr: tadashi.TrEnum):
        device = get_device()
        encoded = self.node_nn(node)
        tr_idx = torch.LongTensor([list(tadashi.TrEnum).index(tr)]).to(device)
        one_hot = nn.functional.one_hot(tr_idx, len(tadashi.TrEnum)).squeeze(0)
        combined = torch.hstack([encoded, one_hot]).to(device)
        return self.linear(combined)


class ArgsNN(nn.Module):
    def __init__(self, node_nn: NodeNN, args: argparse.Namespace):
        super().__init__()
        device = get_device()
        self.node_nn = node_nn
        max_num_args = 3
        self.max_num_args = max(
            len(tadashi.TRANSFORMATIONS[t].arg_help) for t in list(tadashi.TrEnum)
        )
        in_size = args.lstm_hidden_size + self.max_num_args
        self.linear = nn.Linear(in_features=in_size, out_features=1, device=device)

    def forward(self, node: tadashi.Node, args: list):
        device = get_device()
        encoded = self.node_nn(node)
        pad_size = self.max_num_args - len(args)
        args_tensor = torch.tensor(args + [0] * pad_size).to(device)
        combined = torch.hstack([encoded, args_tensor]).to(device)
        return self.linear(combined)


def mcts(
    scops: tadashi.Scops,
    scop: tadashi.Scop,
    node_nn: NodeNN,
    node_head_nn: NodeHeadNN,
    tran_nns: dict[TranNN],
    args_nns: dict[ArgsNN],
    args: argparse.Namespace,
):
    for d in range(args.num_mcts_layers):
        nodes = [n for n in scop.schedule_tree if n.available_transformations]
        node_times = torch.vstack([node_nn(node) for node in nodes])
        node_top_k = torch.topk(
            input=node_head_nn(node_times),
            k=args.node_top_k,
            dim=0,
            largest=False,
        )
        for node_idx in node_top_k.indices:
            node = scop.schedule_tree[node_idx]
            trs = node.available_transformations
            tr_times = torch.vstack([tran_nns[tr](node, tr) for tr in trs])
            tr_top_k = torch.topk(
                torch.Tensor(tr_times),
                args.tr_top_k,
                dim=0,
                largest=False,
            )
            for tr_idx in tr_top_k.indices:
                tr = list(tadashi.TrEnum)[tr_idx]
                trargs = list(tr_args(node, tr))
                print(f"{trargs=}")
                stack = [args_nns[tr](node, ta) for ta in trargs]
                if not stack:
                    stack = [args_nns[tr](node, [])]
                args_times = torch.vstack(stack)
                print(f"{torch.Tensor(args_times).shape=}")
                print(f"{args.args_top_k=}")
                times = torch.Tensor(args_times)
                print(f"{times.shape=}")
                k = min(args.args_top_k, times.shape[0])
                args_top_k = torch.topk(times, k, dim=0, largest=False)
                print(f"{type(args_top_k)=}")
                print(f"{args_top_k.values=}")
                print(f"{args_top_k.indices=}")
                for trarg_idx in args_top_k.indices:
                    trarg = trargs[trarg_idx] if trargs else []
                    legal = node.transform(tr, *trarg)
                    if not legal:
                        node.rollback()
                        t = 1000000
                    else:
                        app = scops.app
                        app.compile()
                        t = app.measure()


def main3():
    args = get_args()
    base, results = get_polybench_list()
    # benchmark = results[29]
    benchmark = "linear-algebra/solvers/durbin"
    gemm = tadashi.apps.Polybench(benchmark=benchmark, base=base)
    scop = gemm.scops[0]
    print(scop.schedule_tree[0].yaml_str)
    node_nn = NodeNN(scop, args)
    node_head_nn = NodeHeadNN(args)
    tran_nns = dict((t, TranNN(node_nn, args)) for t in tadashi.TrEnum)
    args_nns = dict((t, ArgsNN(node_nn, args)) for t in tadashi.TrEnum)
    print(benchmark)
    mcts(
        scops=gemm.scops,
        scop=gemm.scops[0],
        node_nn=node_nn,
        node_head_nn=node_head_nn,
        tran_nns=tran_nns,
        args_nns=args_nns,
        args=args,
    )


if __name__ == "__main__":
    main3()
