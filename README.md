
# NetworkTraceManager


## Input files
The repository contains a set of input files. Each of them is a text file that contains the list of comma-separated measurements contained within a trace. To use these traces, unzip the [input files](https://github.com/ChiaraCaiazza/MECPerf_NetworkTrace/blob/master/inputFiles/active.tar.xz)  into the MECPerf_NetworkTrace/inputFiles folder.

Each trace is associated with the setup used to collect the trace. The setup includes the type of measures, the protocol, the segment measured, the identity of the hosts involved in the measurements,  
the direction of communication, the access technology used to connect the client, and the amount of cross-traffic injected into the access network. The mapping between each input trace and the corresponding setup is contained in a [JSON file](https://github.com/ChiaraCaiazza/MECPerf_NetworkTrace/tree/master/inputFiles/mapping.json).

## Class methods

```python
NetworkTraceManager(configuration)
```

It receives as input a configuration consisting of:

- a key (*mapping_file*) containing the path of the mapping file.
- a set of keys (*typeofmeasure*, *protocol*, *observerPos*, *cross-traffic*, *access-technology*, *sender-identity*, *receiver-identity*) that define the target setup. These keys are used in conjunction with the mapping file to select a list of RTT traces and a list of bandwidth traces that match with the setup provided.
- two seed (*traceseed*, *startingitemseed*) used to initialized two pseudorandom number generator. The first Pseudorandom number generator is used to choose a random trace among the selected ones, while the second is used to select a random starting point within the trace.
- a key (*max_tracegap_seconds*) used to optimize traces so that two consecutive measures differ by *max_tracegap_seconds* at most.

An example of an ini file can be found [here](https://github.com/ChiaraCaiazza/MECPerf_NetworkTrace/blob/master/conf.ini).

```python
get_rtt(sec)
```

Push forward the RTT trace by *sec* seconds. If an error occurs, a negative value is returned. Otherwise, the method returns a RTT value expressed in milliseconds, a datetime object containing the current trace timestamp, and a datetime object containing the timestamp originally associated with the current RTT. If there is no value available for the requested trace time, then the previous RTT is returned. If the requested trace time exceeds the trace timestamp associated with the last element by *max_tracegap*, seconds then all the trace timestamps within the trace are shifted forward of *t_l - t_i + max_tracegap* where t_i and t_l are the timestamps associated with the first and the last element of the trace respectively.

```python  
get_bandwidth(sec)
```

Push forward the bandwidth trace by *sec* seconds. If an error occurs, a negative value is returned. Otherwise, the method returns a bandwidth value expressed in kbps, a datetime object containing the current trace timestamp, and a datetime object containing the timestamp originally associated with the current bandwidth value. If there is no value available for the requested trace time, then the previous bandwidth is returned. If the requested trace time exceeds the trace timestamp associated with the last element by *max_tracegap* seconds, then all the trace timestamps within the trace are shifted forward of *t_l - t_i + max_tracegap* where t_i and t_l are the timestamps associated with the first and the last element of the trace respectively.

```python
get_networkvalues(sec)
```

Call the *get_rtt(sec)* and *get_bandwidth(sec)* methods. 

```python
get_tracelist(mapping_file, typeofmeasure = None, first_endpoint = None, second_endpoint = None, direction = None, command = None, noise = None, observerPos = None, access_technology = None) 
```

Scan the *mapping_file* file and search for the configurations that match the parameters provided. 
**Parameters**

- ***typeofmeasure***: Searches for configurations containing a specific measurement type. Use "active" for active measurements.
- ***first_endpoint***: Specifies one of the two endpoints involved in the measures. For bandwidth measures, it indicates the sender host. The available values are *"Client"*, *"Observer"* or *"Server"* for configurations involving bandwidth measurements and *"Client"* and *"Server"* for configuration involving RTT measurements.
- ***second_endpoint***: Specifies one of the two endpoints involved in the measures. For bandwidth measures, it indicates the receiver host. Available values are *"Client"*, *"Observer"* or *"Server"* for configurations involving bandwidth measurements and *"Observer"* for configuration involving RTT measurements.
-  ***direction***: Searches for configuration with a specific direction of the communication. Use *"upstream"* for configurations involving bandwidth measures from the MECPerf Client to the MECPerf Observer and from MECPerf Observer to the MECPerf Server and *"downstream"* for configurations involving bandwidth measures from the MECPerf Observer to the MECPerf Client and from MECPerf Server to the MECPerf Observer.
- ***command***: Specified the measurement of interest. Available values are *"TCPBandwidth"*, *"UDPBandwidth"*, *"TCPRTT"*, and *"UDPRTT"*.
- ***noise***: Search for a specific amount of cross-traffic expressed in Mbps. Available values are *"0M"*, *"10M"*, *"20M"*, *"30M"*, *"40M"*, *"50M"*. 
- ***observerPos***: Use *"edge"* to select traces having the MECPerf Observer deployed in the MEC network and  *"cloud"* for traces having the MECPerf Observer deployed in the cloud network.
- ***access_technology***: Specifies the access-technology used to connect the client and the Observer. Use one of *"wifi"* and *"lte"*

A list of matching configuration is returned.
