#!/usr/bin/env python3

import argparse
import configparser
import random

from network_trace_manager import NetworkTraceManager


class UserTerminal:
    """Model a user terminal connected to two different edge networks."""

    def __init__(self, identifier: int):
        self.identifier = identifier

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

        config['myconf1']['access-technology'] = random.choice(['wifi', 'lte'])
        config['myconf1']['cross-traffic'] = random.choice(
            [f'{x}M' for x in range(0, 51, 10)])
        config['myconf1']['traceseed'] = str(identifier)

        config['myconf2']['access-technology'] = random.choice(['wifi', 'lte'])
        config['myconf2']['cross-traffic'] = random.choice(
            [f'{x}M' for x in range(0, 51, 10)])
        config['myconf2']['traceseed'] = str(identifier + 10000)

        self.rtt_values = (
            NetworkTraceManager(
                config["myconf1"]).get_rtt_timeseries()[1],
            NetworkTraceManager(
                config["myconf2"]).get_rtt_timeseries()[1])


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

    parser = argparse.ArgumentParser(
        description='Simple flow-level simulation with NetworkTraceManager',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--test", type=int, default=0,
                        help="Print the RTT measurements for the given number of seeds and quit")
    parser.add_argument("--num_drops", type=int, default=1,
                        help="Number of simulation drops")

    args = parser.parse_args()

    if args.test > 0:
        printRtt(args.test)

    num_users = 2
    for drop in range(args.num_drops):
        print(f"drop #{drop}")
        random.seed(drop)

        users = []
        for user in range(num_users):
            users.append(UserTerminal(user))

        # for user in users:
        #     print(f'{user.rtt_values}')
