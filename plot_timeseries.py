#!/usr/bin/python
"""Plot MECPerf RTT/bandwidth timeseries"""

import argparse
import sys
import pprint
from configparser import ConfigParser

import matplotlib.pyplot as plt
import numpy as np

from network_trace_manager import NetworkTraceManager, InvalidConfiguration

parser = argparse.ArgumentParser(
    description='Plot MECPerf RTT/bandwidth timeseries',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("--typeofmeasure", default='active',
                    help="Type of measure")
parser.add_argument("--sender", default='Observer',
                    help="Sender")
parser.add_argument("--receiver", default='Client',
                    help="Receiver")
parser.add_argument("--cross_traffic", default='0M',
                    help="Amount of cross-traffic")
parser.add_argument("--access_technology", default='wifi',
                    help="Access technology")
parser.add_argument("--observer_location", default='edge',
                    help="Location of the observer")
parser.add_argument("--protocol", default='TCP',
                    help="Transpot protocol")
parser.add_argument("--direction", default='downstream',
                    help="Traffic direction")
parser.add_argument("--mapping_file", default='inputFiles/mapping.json',
                    help="JSON mapping file")
parser.add_argument("--metric", default='RTT',
                    help="Metric, one of { RTT, bandwidth }")
parser.add_argument("--histo_values", action='store_true', default=False,
                    help="Print a histogram of the values rather than the time series")
parser.add_argument("--histo_time", action='store_true', default=False,
                    help="Print a histogram of the time interval between two consecutive samples rather than the time series")
parser.add_argument("--ylog", action='store_true', default=False,
                    help="Use logarithmic scale for the y-axis")
args = parser.parse_args()

config = ConfigParser()
config['myconf'] = {}
config['myconf']['mapping_file'] = args.mapping_file
config['myconf']['max_tracegap_seconds'] = str(365 * 86400) # 1 year
config['myconf']['seed'] = str(0)
config['myconf']['typeofmeasure'] = args.typeofmeasure
config['myconf']['protocol'] = args.protocol
config['myconf']['observerPos'] = args.observer_location
config['myconf']['cross-traffic'] = args.cross_traffic
config['myconf']['access-technology'] = args.access_technology
config['myconf']['sender-identity'] = args.sender
config['myconf']['receiver-identity'] = args.receiver
config['myconf']['first-endpoint'] = args.sender
config['myconf']['second-endpointity'] = args.receiver
config['myconf']['direction'] = args.direction
config['myconf']['trace'] = 'True'

try:
    trace = NetworkTraceManager(config['myconf'])

    assert args.metric in ['RTT', 'bandwidth']

    timeseries = trace.get_rtt_timeseries() \
        if args.metric == 'RTT' \
            else trace.get_bandwidth_timeseries()

    if args.histo_values:
        plt.xlabel('Time (seconds)')
        plt.ylabel('Count')
        plt.hist(timeseries[1], bins=100)

    elif args.histo_time:
        plt.xlabel('Time interval between samples (seconds)')
        plt.ylabel('Count')
        deltas = []
        last = None
        for t in timeseries[0]:
            if last is None:
                last = t
            else:
                deltas.append(t - last)
                last = t
        plt.hist(deltas, bins=100)

    else:
        plt.xlabel('Time (seconds)')
        plt.ylabel(args.metric)
        plt.plot(timeseries[0], timeseries[1], '.')
        plt.axes([
            min(timeseries[0]),
            max(timeseries[0]),
            min(timeseries[1]),
            max(timeseries[1])])

    if args.ylog:
        plt.yscale('log')

    plt.show()
    

except InvalidConfiguration:
    sys.stderr.write('Invalid configuration:\n\n{}\n\nPlease check command-line arguments\n'.format(
        pprint.pformat(dict(config['myconf']))))