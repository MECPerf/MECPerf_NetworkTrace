import configparser
from network_trace_manager import NetworkTraceManager 
import copy

config = configparser.ConfigParser()
config.read("conf.ini")

network_trace1 = NetworkTraceManager(config["conf1"])
network_trace2 = NetworkTraceManager(config["conf2"])


print(network_trace1.get_delay())
print (network_trace1.get_delay())
print (network_trace1.get_delay())
print (network_trace1.get_delay())
print "\n"
    

print (network_trace2.get_delay())
print (network_trace2.get_delay())
print (network_trace2.get_delay())
print (network_trace2.get_delay())
print "\n"

print (network_trace1.get_bandwidth())
print (network_trace1.get_bandwidth())
print (network_trace1.get_bandwidth())
print (network_trace1.get_bandwidth())
print "\n"

print (network_trace2.get_bandwidth())
print (network_trace2.get_bandwidth())
print (network_trace2.get_bandwidth())
print (network_trace2.get_bandwidth())
print (network_trace2.get_bandwidth())
print "\n"

for i in range(0,4):
    delay, bandwidth = network_trace1.get_networkvalues()
    print (str(delay) + ", " + str(bandwidth))
print "\n"


for i in range(0,4):
    delay, bandwidth = network_trace2.get_networkvalues()
    print (str(delay) + ", " + str(bandwidth))
