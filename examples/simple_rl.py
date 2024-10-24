#! /bin/env python
#
# Adopted from https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html#dqn-algorithm
import argparse
import math
import random
import re
from collections import deque, namedtuple
from itertools import count
from pathlib import Path

import matplotlib.pyplot as plt
import tadashi
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import yaml

CURRENT_MARK = "CURRENT_"


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


def optimize_model(args, memory):
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
    next_state_values = torch.zeros(BATCH_SIZE, device=device)
    with torch.no_grad():
        next_state_values[non_final_mask] = (
            target_net(non_final_next_states).max(1).values
        )
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

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

    steps_done = env.steps_done
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
            optimize_model(args, memory)

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
    base = Path("build/_deps/polybench-src/")
    result = []
    for p in base.glob("**"):
        if Path(p / (p.name + ".c")).exists():
            result.append(p.relative_to(base))
    return base, result


def tokenize(isl_str: str):
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
        # last_match = match
        match = re.match(pattern, isl_str.strip())
    # print(f"{last_match=}")
    # print(f"remaining: |{isl_str[:20]}|")
    if isl_str.strip():
        raise NotImplementedError(f"ISL string not fully parsed. Remaining: {isl_str}")
    return result


def parse_isl(isl_str: str, pos: int, result: list) -> int:
    # open_delim = re.compile(r"^\{|^\[|^\(")
    # match = re.match(open_delim, isl_str)
    # match.string
    # if match.span() != (0, 1):
    #     raise NotImplementedError("This should not be happening!!!")
    open_delims = "([{"
    closed_delims = ")]}"
    if isl_str[pos] in open_delims:
        result.append(isl_str[pos])
        pos += 1
        pos = parse_isl(isl_str, pos, result)
        result.append(isl_str[pos])
        pos += 1
    # else:
    #     while isl_str[pos]

    return isl_str[:100]


def traverse(yaml_dict, level):
    result = []
    if isinstance(yaml_dict, str):
        # isl_tokens = []
        # pos = parse_isl(yaml_dict, 0, isl_tokens)
        # if pos != len(yaml_dict):
        #     raise NotImplementedError(
        #         "yaml_dict (which should be an isl_string) was not parsed completely!"
        #     )
        isl_tokens = tokenize(yaml_dict)
        return [(level, f"{yaml_dict}|{isl_tokens}...|")]
    elif isinstance(yaml_dict, list):
        for item in yaml_dict:
            result += traverse(item, level + 1)
    else:
        for k, v in yaml_dict.items():
            if k == "child":
                # print(f"{v=}")
                result += traverse(v, level + 1)
            else:
                current = False
                if k.startswith(CURRENT_MARK):
                    k = k.replace(CURRENT_MARK, "")
                    current = True
                result.append((level, current, k))
                result += traverse(v, level)
    if not isinstance(result, str) and level == 0:
        for r in result:
            print(r)
        print("--- end ---")
    return result


def main2():
    base, results = get_polybench_list()
    gemm = tadashi.apps.Polybench(results[29], base)
    print(f"{gemm.benchmark=}")
    scops = tadashi.Scops(gemm)
    scop = scops[0]
    node = scop.schedule_tree[11]
    node.transform(tadashi.TrEnum.TILE, 16)
    yaml_str = node.yaml_str
    pattern = re.compile(r"# YOU ARE HERE\n *")
    yaml_str = re.sub(pattern, CURRENT_MARK, yaml_str)
    print(yaml_str[:800])
    yaml_dict = yaml.load(yaml_str, yaml.SafeLoader)
    traverse(yaml_dict, 0)
    isl_expr = yaml_dict["child"]["sequence"][0]["filter"]
    print(isl_expr)
    # print(f"{tokenize(yaml_str)=}")


if __name__ == "__main__":
    main2()
