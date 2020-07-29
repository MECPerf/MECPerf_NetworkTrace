#!/usr/bin/env python3

import logging
import os
import unittest
import tempfile
import configparser

from network_trace_manager import NetworkTraceManager, InvalidConfiguration

logging.basicConfig(level=logging.FATAL)

class TestNetworkTraceManager(unittest.TestCase):

    @staticmethod
    def write_to_conf_file(conf_file):
        conf_file.write(
b'''
[DEFAULT]
max_tracegap_seconds=30
mapping_file=inputFiles/mapping.json

[confGood]
seed=0
typeofmeasure=active
protocol=TCP
observerPos=edge
cross-traffic = 0M
access-technology = wifi
sender-identity=Observer
receiver-identity=Client
trace = True

[confBad]
seed=0
typeofmeasure=active
protocol=TCP
#observerPos=edge <<< this is bad
cross-traffic = 0M
access-technology = wifi
sender-identity=Observer
receiver-identity=Client
trace = True
''')
        conf_file.flush()

    def test_valid_invalid_configuration(self):
        config = None
        with tempfile.NamedTemporaryFile() as conf_file:
            TestNetworkTraceManager.write_to_conf_file(conf_file)
            config = configparser.ConfigParser()
            config.read(conf_file.name)

        self.assertIsNotNone(config)

        # good conf
        good_conf = NetworkTraceManager(config["confGood"])
        self.assertEqual(0, good_conf._status)
        good_conf.print_instanceconfiguration()

        # non-existing conf
        self.assertRaises(KeyError, lambda : NetworkTraceManager(config["confx"]))

        # bad conf
        self.assertRaises(InvalidConfiguration, lambda : NetworkTraceManager(config["confBad"]))

    def test_get_trace_list(self):
        trace_list = NetworkTraceManager.get_tracelist('inputFiles/mapping.json')
        self.assertEqual(288, len(trace_list))

    def test_get_trace_list_custom(self):
        with tempfile.NamedTemporaryFile() as mapping_file:
            mapping_file.write(
b'''[
    {
        "direction": "upstream", 
        "noise": "0M", 
        "typeofmeasure": "active", 
        "last_timestamp": "2020-01-31 21:16:45.000000", 
        "first_timestamp": "2020-01-24 15:36:55.000000", 
        "path": "inputFiles/active/wifi-TCPBandwidth-upstream-noise0M_Client-Observer_edge.txt", 
        "ObserverPos": "edge", 
        "receiverIdentity": "Observer", 
        "access-technology": "wifi", 
        "senderIdentity": "Client", 
        "command": "TCPBandwidth"
    }
    ]
''')
            mapping_file.flush()
            trace_list = NetworkTraceManager.get_tracelist(mapping_file.name)
            self.assertEqual(1, len(trace_list))
            self.assertEqual('active', trace_list[0]['typeofmeasure'])
            self.assertEqual('TCPBandwidth', trace_list[0]['command'])
            self.assertEqual('edge', trace_list[0]['ObserverPos'])
            self.assertEqual('0M', trace_list[0]['noise'])
            self.assertEqual('wifi', trace_list[0]['access-technology'])
            self.assertEqual('upstream', trace_list[0]['direction'])
            self.assertEqual('Client', trace_list[0]['senderIdentity'])
            self.assertEqual('Observer', trace_list[0]['receiverIdentity'])

    def test_get_all_values(self):
        with tempfile.NamedTemporaryFile() as conf_file:
            TestNetworkTraceManager.write_to_conf_file(conf_file)
            config = configparser.ConfigParser()
            config.read(conf_file.name)

            trace = NetworkTraceManager(config["confGood"])
            self.assertEqual({'active'}, trace.get_all_values('typeofmeasure'))
            self.assertEqual(
                {'TCPBandwidth', 'UDPBandwidth', 'TCPRTT', 'UDPRTT'},
                trace.get_all_values('command'))
            self.assertEqual({'edge', 'cloud'}, trace.get_all_values('ObserverPos'))
            self.assertEqual(set([f'{x}M' for x in range(0,51, 10)]), trace.get_all_values('noise'))
            self.assertEqual({'wifi', 'lte'}, trace.get_all_values('access-technology'))
            self.assertEqual({'upstream', 'downstream'}, trace.get_all_values('direction'))
            self.assertEqual({'Observer', 'Client', 'Server'}, trace.get_all_values('senderIdentity'))
            self.assertEqual({'Observer', 'Client', 'Server'}, trace.get_all_values('receiverIdentity'))
            self.assertEqual({'Client', 'Server'}, trace.get_all_values('first-endpoint'))
            self.assertEqual({'Observer'}, trace.get_all_values('second-endpoint'))

    def test_get_timeseries(self):
        with tempfile.NamedTemporaryFile() as conf_file:
            TestNetworkTraceManager.write_to_conf_file(conf_file)
            config = configparser.ConfigParser()
            config.read(conf_file.name)

            trace = NetworkTraceManager(config["confGood"])

            rtt_timeseries = trace.get_rtt_timeseries()
            self.assertEqual(2, len(rtt_timeseries))
            self.assertEqual(len(rtt_timeseries[0]), len(rtt_timeseries[1]))
            self.assertEqual(0, rtt_timeseries[0][0])
            for i in range(1, len(rtt_timeseries)):
                self.assertLessEqual(rtt_timeseries[0][i-1], rtt_timeseries[0][i])

            bw_timeseries = trace.get_bandwidth_timeseries()
            self.assertEqual(2, len(bw_timeseries))
            self.assertEqual(len(bw_timeseries[0]), len(bw_timeseries[1]))
            self.assertEqual(0, bw_timeseries[0][0])
            for i in range(1, len(bw_timeseries)):
                self.assertLessEqual(bw_timeseries[0][i-1], bw_timeseries[0][i])

if __name__ == '__main__':
    unittest.main()