#!/usr/bin/env python3

import argparse
import configparser
import logging
import random

from network_trace_manager import NetworkTraceManager


class UserTerminal:
    """Model a user terminal connected to two different edge networks."""

    def __init__(self, identifier: int, rng: random.Random):
        self.identifier = identifier
        self.time = 0

        config = configparser.ConfigParser()
        config['myconf1'] = {}
        config['myconf1']['mapping_file'] = 'inputFiles/mapping.json'
        config['myconf1']['max_tracegap_seconds'] = str(365 * 86400)  # 1 year
        config['myconf1']['startingitemseed'] = str(0)
        config['myconf1']['typeofmeasure'] = 'active'
        config['myconf1']['protocol'] = 'TCP'
        config['myconf1']['command'] = 'TCPRTT'
        config['myconf1']['observerPos'] = 'edge'
        config['myconf1']['sender-identity'] = 'Observer'
        config['myconf1']['receiver-identity'] = 'Client'
        config['myconf1']['first-endpoint'] = 'Observer'
        config['myconf1']['second-endpoint'] = 'Client'

        config['myconf2'] = config['myconf1']

        config['myconf1']['access-technology'] = rng.choice(['wifi', 'lte'])
        config['myconf1']['cross-traffic'] = rng.choice(
            [f'{x}M' for x in range(0, 51, 10)])
        config['myconf1']['traceseed'] = str(identifier)

        config['myconf2']['access-technology'] = rng.choice(['wifi', 'lte'])
        config['myconf2']['cross-traffic'] = rng.choice(
            [f'{x}M' for x in range(0, 51, 10)])
        config['myconf2']['traceseed'] = str(identifier + 10000)

        self.rtt_values = (
            NetworkTraceManager(
                config["myconf1"]).get_rtt_timeseries()[1],
            NetworkTraceManager(
                config["myconf2"]).get_rtt_timeseries()[1])
        assert len(self.rtt_values[0]) == len(self.rtt_values[1])

    def rtt(self, network: int) -> float:
        """Return the next RTT of this terminal on the given network"""
        assert 0 <= network <= 1
        rtt_values = self.rtt_values[network]
        ret = rtt_values[self.time]
        self.time += 1
        if self.time == len(self.rtt_values):
            self.time = 0
        return ret


class Network:
    """Model a telco operator network with edge compute resources."""

    def __init__(self, identifier: int):
        self.identifer = identifier
        self._users = []
        self._rtts = {}

    def associate(self, ut: UserTerminal):
        """Associate the given `UserTerminal` to this network."""

        assert not ut in self._users
        self._users.append(ut)

    def dissociate(self, ut: UserTerminal):
        """Dissociate the given `UserTerminal` from this network."""

        if ut in self._users:
            self._users.remove(ut)

    def simulate(self):
        """Simulate the execution of a time slot."""

        self._rtts.clear()
        for user in self._users:
            self._rtts[user.identifier] = user.rtt(self.identifer)

    def rtts(self):
        """Return the RTTs in the last time slot."""

        return self._rtts.values()

    def ut_identifiers(self):
        """Return the list of identifiers of associated users."""

        return [ut.identifier for ut in self._users]

    def migrate(self):
        """Return the list of `UserTerminal` to migrate."""

        ret = []
        return ret


class Simulator:
    """Flow-level simulator with two networks and multiple users."""

    def __init__(self, seed: int, num_users: int, on_time: float, off_time: float):
        logger.info(
            f"simulation seed {seed} num users {num_users} ON/OFF times {on_time}/{off_time}")
        self.time_slot = 0
        self.num_users = num_users
        self.on_time = on_time
        self.off_time = off_time
        self.rng = random.Random(seed)

        # statistics
        self.rtts = []
        self.migrations = 0

        self.users = []
        self.networks = [Network(0), Network(1)]
        init_active_prob = on_time / (on_time + off_time)
        for user in range(num_users):
            self.users.append((None, None))
            if self.rng.random() < init_active_prob:
                self._new_user(user)
            else:
                self._del_user(user)

    def next_slot(self):
        """Advance simulation until the next slot."""

        # do the RTT measurements
        for network in [0, 1]:
            self.networks[network].simulate()
            logger.debug((
                f"#{self.time_slot} OP{network} "
                f"users {self.networks[network].ut_identifiers()} "
                f"RTTs {list(self.networks[network].rtts())}"))
            self.rtts += self.networks[network].rtts()

        # migrate the users between the two networks
        from0 = self.networks[0].migrate()
        from1 = self.networks[1].migrate()
        self.migrations += len(from0) + len(from1)
        for ut in from0:
            self.networks[1].associate(ut)
        for ut in from1:
            self.networks[0].associate(ut)

        # activate/deactivate users
        for user in range(self.num_users):
            if self.users[user][0] is None and self.users[user][1] < self.time_slot:
                self._new_user(user)
            elif self.users[user][0] is not None and self.users[user][1] < self.time_slot:
                self._del_user(user)

        # advance time
        self.time_slot += 1

    def _new_user(self, identifier: int):
        """Create a new user and associate it to a random network."""

        ut = UserTerminal(identifier, self.rng)
        on_time = self.time_slot + self.rng.expovariate(1.0 / self.on_time)
        self.users[identifier] = (ut, on_time)
        network = 0
        if self.rng.random() >= 0.5:
            network = 1
        self.networks[network].associate(ut)
        logger.debug(
            f"#{self.time_slot} activating user {identifier} on OP{network} until {on_time}")

    def _del_user(self, identifier: int):
        """Delete the given user."""

        for network in [0, 1]:
            self.networks[network].dissociate(self.users[identifier][0])
        off_time = self.time_slot + self.rng.expovariate(1.0 / self.off_time)
        self.users[identifier] = (None, off_time)
        logger.debug(
            f"#{self.time_slot} deactivating user {identifier} until {off_time}")


def printRtt(num_seeds: int):
    config = configparser.ConfigParser()
    config['myconf'] = {}
    config['myconf']['mapping_file'] = 'inputFiles/mapping.json'
    config['myconf']['max_tracegap_seconds'] = str(365 * 86400)  # 1 year
    config['myconf']['startingitemseed'] = str(0)
    config['myconf']['typeofmeasure'] = 'active'
    config['myconf']['protocol'] = 'TCP'
    config['myconf']['command'] = 'TCPRTT'
    config['myconf']['observerPos'] = 'edge'
    config['myconf']['sender-identity'] = 'Observer'
    config['myconf']['receiver-identity'] = 'Client'
    config['myconf']['first-endpoint'] = 'Observer'
    config['myconf']['second-endpoint'] = 'Client'

    access = ['wifi', 'lte']
    cross = [f'{x}M' for x in range(0, 51, 10)]
    for seed in range(num_seeds):
        for a in access:
            for c in cross:
                config['myconf']['access-technology'] = a
                config['myconf']['cross-traffic'] = c
                config['myconf']['traceseed'] = str(seed)
                rtt = NetworkTraceManager(
                    config["myconf"]).get_rtt_timeseries()[1]
                print(f"#{seed} {a} {c} {rtt}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    logger = logging.getLogger("edge_operator")
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(
        description='Simple flow-level simulation with NetworkTraceManager',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--test", type=int, default=0,
                        help="Print the RTT measurements for the given number of seeds and quit")
    parser.add_argument("--num_drops", type=int, default=1,
                        help="Number of simulation drops")
    parser.add_argument("--on_time", type=float, default=10.0,
                        help="Average ON time, in slots")
    parser.add_argument("--off_time", type=float, default=10.0,
                        help="Average OFF time, in slots")
    parser.add_argument("--duration", type=int, default=10,
                        help="Simulation duration, in slots")

    args = parser.parse_args()

    if args.test > 0:
        printRtt(args.test)

    num_users = 10
    for drop in range(args.num_drops):
        sim = Simulator(drop, num_users, args.on_time, args.off_time)
        for slot in range(args.duration):
            sim.next_slot()
        migration_rate = sim.migrations / (2 * args.duration)
        logger.debug(f"migration-rate {migration_rate}")
        logger.debug(f"RTTs {sim.rtts}")
