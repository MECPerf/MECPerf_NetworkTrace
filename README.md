
# NetworkTraceManager

## Class methods
```python
def __init__(self, config):
```
Use the configuration object to initialize the current instance. 
First, a set of configuration keys (*typeofmeasure*, *protocol*, *observerPos*, *cross-traffic*, *access-technology*, *sender-identity*, and *receiver-identity*) are used to select the RTT and the bandwidth input files. Then, the RTT and the bandwidth traces are generated from each input file using a random number of consecutive measures. The *mininimum_tracelen* key configures the minimum number of measures contained in each trace. Finally, traces are optimized so that two consecutive measures differ by *max_tracegap_seconds* at most. 

An example of ini file can be found [here](https://github.com/ChiaraCaiazza/MECPerf_NetworkTrace/blob/master/conf.ini).
```python
@staticmethod
def get_tracelist(typeofmeasure=None, senderIdentity=None, receiverIdentity=None, direction=None, command=None, noise=None, observerPos=None, access_technology=None) 
```
Scan the mapping.json file and search for trace files whose configuration matches the parameters provided. Returns a list of available matching configurations.
**Parameters** 
 - ***typeofmeasure***: Search traces with a given measurement type. Use "active" for active measurements and *"self"* or *"mim"* for passive measurements.
 - ***first_endpoint***: One of the two endpoints involved in the measures. For bandwidth measures, it indicates the sender host. Use one of *"Client"*, *"Observer"* or *"Server"*.
 - ***second_endpoint***: One of the two endpoints involved in the measures. For bandwidth measures, it indicates the receiver host. Use one of *"Client"*, *"Observer"* or *"Server"*.
 -  ***direction***: Search traces with a specific communication direction. Use *"upstream"* for measures from the MECPerf Client to the MECPerf Observer and from MECPerf Observer to the MECPerf Server and *"downstream"* for measures from the MECPerf Observer to the MECPerf Client and from MECPerf Server to the MECPerf Observer.
 - ***command***: Search traces for a given command. Use one of *"TCPBandwidth"*, *"UDPBandwidth"*, *"TCPRTT"*, and *"UDPRTT"*
 - ***noise***: Search traces having a given amount of cross-traffic injected in the network. 
 - **observerPos**: Use *"edge"* to select traces having the MECPerf Observer deployed in the MEC network and  *"cloud"* for traces having the MECPerf Observer deployed in the cloud network.
 - **access_technology**: The access-technology used to connect the client and the Observer. Use one of *"wifi"* and *"lte"*
                
```python
def get_rtt(self, sec) 
```
Push forward the RTT trace for *sec* seconds. If successful, it returns the current trace timestamp, the RTT value, and the absolute timestamp. Otherwise, a negative value is returned.

```python  
def get_bandwidth(self, sec)
```
Push forward the bandwidth trace for *sec* seconds. If successful, it returns the current trace timestamp, the bandwidth value, and the absolute timestamp. Otherwise, a negative value is returned.

```python
def get_networkvalues(self, sec) 
```
Call the *get_rtt(sec)* and *get_bandwidth(sec)* methods. 



## Input files
The repository provides a set of [input files](https://github.com/ChiaraCaiazza/MECPerf_NetworkTrace/tree/master/inputFiles). Each text file contains the list of comma-separated  measures of a specified configuration (i.e typeofmeasure, command, direction, etc.).  Timestamps use the *%Y-%m-%d %H:%M:%S.%f* format. Instead, the file [mapping.json](https://github.com/ChiaraCaiazza/MECPerf_NetworkTrace/tree/master/inputFiles/mapping.json) maps the input files with their configuration.





