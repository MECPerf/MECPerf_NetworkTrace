#!/usr/bin/env python3

import configparser
import copy

from network_trace_manager import NetworkTraceManager 

config = configparser.ConfigParser()
config.read("conf.ini")

'''
for elem in NetworkTraceManager.get_tracelist(command="TCPBandwidth", direction="upstream", typeofmeasure="active"):
    print (elem)
'''


network_trace1 = NetworkTraceManager(config["conf1"])
network_trace2 = NetworkTraceManager(config["conf2"])

print(network_trace1.get_rtt())
print(network_trace1.get_rtt())
print(network_trace1.get_rtt())
print(network_trace1.get_rtt())
print("\n")
    

print(network_trace2.get_rtt())
print(network_trace2.get_rtt())
print(network_trace2.get_rtt())
print(network_trace2.get_rtt())
print("\n")

print(network_trace1.get_bandwidth())
print(network_trace1.get_bandwidth())
print(network_trace1.get_bandwidth())
print(network_trace1.get_bandwidth())
print("\n")

print(network_trace2.get_bandwidth())
print(network_trace2.get_bandwidth())
print(network_trace2.get_bandwidth())
print(network_trace2.get_bandwidth())
print(network_trace2.get_bandwidth())
print("\n")

for i in range(0,4):
    rtt, bandwidth = network_trace1.get_networkvalues()
    print(str(rtt) + ", " + str(bandwidth))
print("\n")


for i in range(0,4):
    rtt, bandwidth = network_trace2.get_networkvalues()
    print(str(rtt) + ", " + str(bandwidth))
