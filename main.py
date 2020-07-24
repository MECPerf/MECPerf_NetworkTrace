#!/usr/bin/env python3

import logging
import configparser
import copy

from network_trace_manager import NetworkTraceManager 

logging.basicConfig(filename="file.log", filemode='w', 
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(funcName)s(): %(message)s', 
                    datefmt='%H:%M:%S', level=logging.DEBUG)

config = configparser.ConfigParser()
config.read("conf.ini")

'''
for elem in NetworkTraceManager.get_tracelist(command="TCPBandwidth", direction="upstream", typeofmeasure="active"):
    print (elem)
'''


network_trace1 = NetworkTraceManager(config["conf1"])
network_trace2 = NetworkTraceManager(config["conf2"])

print(network_trace1.get_rtt(1))
print(network_trace1.get_rtt(3))
print(network_trace1.get_rtt(2))
print(network_trace1.get_rtt(4))
print("\n")
    

print(network_trace2.get_rtt(1))
print(network_trace2.get_rtt(6))
print(network_trace2.get_rtt(8))
print(network_trace2.get_rtt(2))
print("\n")

print(network_trace1.get_bandwidth(1))
print(network_trace1.get_bandwidth(2))
print(network_trace1.get_bandwidth(3))
print(network_trace1.get_bandwidth(4))
print("\n")

print(network_trace2.get_bandwidth(1))
print(network_trace2.get_bandwidth(1))
print(network_trace2.get_bandwidth(1))
print(network_trace2.get_bandwidth(1))
print(network_trace2.get_bandwidth(1))
print("\n")

for i in range(0,4):
    rtt, bandwidth = network_trace1.get_networkvalues(1)
    print(str(rtt) + ", " + str(bandwidth))
print("\n")


for i in range(0,4):
    rtt, bandwidth = network_trace2.get_networkvalues(1)
    print(str(rtt) + ", " + str(bandwidth))
