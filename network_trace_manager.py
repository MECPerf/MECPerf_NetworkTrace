#!/usr/bin/env python3

import configparser
import random
import datetime
import logging
import json

datetime_format = "%Y-%m-%d %H:%M:%S.%f"

class InvalidConfiguration(Exception):
        """Invalid configuration"""
        pass

class NetworkTraceManager:
        __OK = 0
        __WRONG_CONFIGURATION = -1
        __WRONG_INPUTFILEPATH = -2

        @staticmethod
        def get_tracelist(mapping_file, typeofmeasure = None, first_endpoint = None, second_endpoint = None,
                          direction = None, command = None, noise = None, observerPos = None, 
                          access_technology = None):
                trace_list = []

                with open (mapping_file, "r") as inputjson:
                        data = json.load(inputjson)

                for elem in data:
                        config = {}
                        discard_elem = False
                        for key in elem :
                                if discard_elem == True:
                                        continue

                                if key == "typeofmeasure":
                                        if typeofmeasure != None and typeofmeasure != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_typeofmeasure = elem[key]
                                if key == "command":
                                        if command != None and command != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_command = elem[key]    
                                if key == "direction":
                                        if direction != None and direction != elem[key]:
                                                discard_elem = True
                                                continue
                                                
                                        if elem[key] != None:
                                                curr_direction = elem[key]
                                        else:
                                                curr_direction = None
                                if key == "ObserverPos":                                        
                                        if observerPos != None and observerPos != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_observerPos = elem[key]
                                if key == "noise":
                                        if noise != None and noise != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_noise = elem[key]
                                if key == "senderIdentity":              
                                        if first_endpoint != None and first_endpoint != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_senderIdentity  = elem[key]
                                if key == "receiverIdentity":
                                        if second_endpoint != None and second_endpoint != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_receiverIdentity = elem[key]
                                if key == "access-technology":
                                        if access_technology != None and access_technology != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_accesstech = elem[key]
                                if key == "path":
                                        pass

                                if key == "first-endpoint":              
                                        if first_endpoint != None and first_endpoint != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_firstendpoint  = elem[key]
                                if key == "second-endpoint":
                                        if second_endpoint != None and second_endpoint != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_secondendpoint = elem[key]
                                        
                        if discard_elem != True:
                                if "RTT" in curr_command  and curr_direction != None:
                                        continue
                                
                                config['typeofmeasure'] = curr_typeofmeasure
                                config['command'] = curr_command
                                config['ObserverPos'] = curr_observerPos
                                config['noise'] = curr_noise
                                config['access-technology'] = curr_accesstech

                                if "TCPBandwidth" in curr_command or "UDPBandwidth" in curr_command: 
                                        config['direction'] = curr_direction
                                        config['senderIdentity'] = curr_senderIdentity
                                        config['receiverIdentity'] = curr_receiverIdentity

                                elif "TCPRTT" in curr_command or "UDPRTT" in curr_command: 
                                        config['first-endpoint'] = curr_firstendpoint
                                        config['second-endpoint'] = curr_secondendpoint

                                trace_list.append(config)
                
                return trace_list

        def __init__(self, config):
                self._status = self.__OK
                self._rtt_trace = []
                self._rtt_index = 0
                self._rtt_timestamp = None
                self._bandwidth_trace = []
                self._bandwidth_index = 0    
                self._bandwidth_timestamp = None            
                self._instanceconfiguration = config

                self._check__instanceconfiguration()
                self.print_instanceconfiguration()
                
                #initialize the random generator
                random.seed(self._instanceconfiguration.getint("seed"))

                self._get_traces()
                self._rtt_timestamp = self._rtt_trace[0]["timestamp"]
                self._bandwidth_timestamp = self._bandwidth_trace[0]["timestamp"]

                logging.info("rtt: " + str(self._rtt_trace))
                logging.info("_rtt_timestamp: " + str(self._rtt_timestamp))
                logging.info("bandwidth: " + str(self._bandwidth_trace))
                logging.info("_bandwidth_timestamp: " + str(self._bandwidth_timestamp))

        def _throw_if_invalid(self):
                """Throw an exception if the current status is not OK"""

                if self._status != self.__OK:
                        raise InvalidConfiguration

        def get_all_values(self, field_type):
                """Return all the possible values for a given field type, according to the mapping file"""

                self._throw_if_invalid()

                trace_list = self.get_tracelist(self._instanceconfiguration.get('mapping_file'))

                ret = set()
                for elem in trace_list:
                        for k, v in elem.items():
                                if k == field_type:
                                        ret.add(v)

                return ret

        def get_rtt_timeseries(self):
                """Return the full RTT timeseries as two vectors of equal size: the first vector
                contains the timestamp of the i-th sample, in seconds starting from 0, the second
                vector contains the RTT of the i-th sample"""

                return NetworkTraceManager._get_timeseries(
                        self._rtt_trace,
                        'rtt')

        def get_bandwidth_timeseries(self):
                """Return the full bandwidth timeseries as two vectors of equal size: the first vector
                contains the timestamp of the i-th sample, in seconds starting from 0, the second
                vector contains the bandwidth of the i-th sample"""

                return NetworkTraceManager._get_timeseries(
                        self._bandwidth_trace,
                        'bandwidth')

        @staticmethod
        def _get_timeseries(trace, trace_type):
                timestamps = []
                values = []

                assert trace_type in ['rtt', 'bandwidth']
                assert len(trace) > 0
                assert 'timestamp' in trace[0]

                first_timestamp = trace[0]['timestamp']
                for elem in trace:
                        assert 'timestamp' in elem
                        assert trace_type in elem

                        timestamps.append((elem['timestamp'] - first_timestamp).total_seconds())
                        values.append(float(elem[trace_type]))
                
                return [timestamps, values]

        def get_rtt(self, sec):
                self._throw_if_invalid()
 
                while (True):
                        next_index = (self._rtt_index + 1) % len(self._rtt_trace)
                        if next_index != 0:
                                next_timestamp = self._rtt_trace[self._rtt_index + 1]["timestamp"]
                        else:
                                max_tracegap = self._instanceconfiguration.getint("max_tracegap_seconds")
                                next_timestamp = self._rtt_trace[-1]["timestamp"] + \
                                                 datetime.timedelta(seconds=max_tracegap)


                        if self._rtt_timestamp + datetime.timedelta(seconds=sec) >= next_timestamp:
                                self._rtt_index = next_index

                                if next_index == 0:
                                        diff_seconds = (self._rtt_trace[-1]["timestamp"] -
                                                        self._rtt_trace[0]["timestamp"]  + 
                                                        datetime.timedelta(seconds=max_tracegap)).total_seconds()
                                        for elem in self._rtt_trace:
                                                elem["timestamp"] = elem["timestamp"] + \
                                                                    datetime.timedelta(seconds=diff_seconds)

                                        logging.info("rrt: " + str(self._rtt_trace))


                        next_index = (self._rtt_index + 1) % len(self._rtt_trace)
                        if next_index != 0:
                                next_timestamp = self._rtt_trace[self._rtt_index + 1]["timestamp"]
                        else:
                                max_tracegap = self._instanceconfiguration.getint("max_tracegap_seconds")
                                next_timestamp = self._rtt_trace[-1]["timestamp"] + \
                                                 datetime.timedelta(seconds=max_tracegap)
        
                        if self._rtt_timestamp + datetime.timedelta(seconds=sec) < next_timestamp:
                                self._rtt_timestamp += datetime.timedelta(seconds=sec)
                
                                return self._rtt_trace[self._rtt_index]["rtt"], self._rtt_timestamp, \
                                       self._rtt_trace[self._rtt_index]["absolute_timestamp"]

        def get_bandwidth(self, sec):
                self._throw_if_invalid()

                while (True):
                        next_index = (self._bandwidth_index + 1) % len(self._bandwidth_trace)
                        if next_index != 0:
                                next_timestamp = self._bandwidth_trace[self._bandwidth_index + 1]["timestamp"]
                        else:
                                max_tracegap = self._instanceconfiguration.getint("max_tracegap_seconds")
                                next_timestamp = self._bandwidth_trace[-1]["timestamp"] + \
                                                 datetime.timedelta(seconds=max_tracegap)


                        if self._bandwidth_timestamp + datetime.timedelta(seconds=sec) >= next_timestamp:
                                self._bandwidth_index = next_index

                                if next_index == 0:
                                        diff_seconds = (self._bandwidth_trace[-1]["timestamp"] -
                                                        self._bandwidth_trace[0]["timestamp"]  + 
                                                        datetime.timedelta(seconds=max_tracegap)).total_seconds()
                                        for elem in self._bandwidth_trace:
                                                elem["timestamp"] = elem["timestamp"] + \
                                                                    datetime.timedelta(seconds=diff_seconds)

                                        logging.info(self._bandwidth_trace)


                        next_index2 = (self._bandwidth_index + 1) % len(self._bandwidth_trace)
                        if next_index2 != 0:
                                next_timestamp2 = self._bandwidth_trace[self._bandwidth_index + 1]["timestamp"]
                        else:
                                max_tracegap = self._instanceconfiguration.getint("max_tracegap_seconds")
                                next_timestamp2 = self._bandwidth_trace[-1]["timestamp"] + \
                                                  datetime.timedelta(seconds=max_tracegap)

        
                        if self._bandwidth_timestamp + datetime.timedelta(seconds=sec) < next_timestamp2:
                                self._bandwidth_timestamp += datetime.timedelta(seconds=sec)
                
                                return self._bandwidth_trace[self._bandwidth_index]["bandwidth"], \
                                       self._bandwidth_timestamp, \
                                       self._bandwidth_trace[self._bandwidth_index]["absolute_timestamp"]

            

        def get_networkvalues(self, sec):
                self._throw_if_invalid()

                rtt = self.get_rtt(sec)
                bandwidth = self.get_bandwidth(sec)

                return rtt, bandwidth

        def _check__instanceconfiguration(self):
                if self._instanceconfiguration.getint("seed") == None:
                        logging.error("Error: seed is missing")
                        self._status = self.__WRONG_CONFIGURATION
                        return

                if self._instanceconfiguration.get("typeofmeasure") == None:
                        logging.error("Error: typeofmeasure is missing")
                        self._status = self.__WRONG_CONFIGURATION
                        return
                
                if self._instanceconfiguration.get("typeofmeasure") == "active":
                        if self._instanceconfiguration.get("protocol") == None or \
                           self._instanceconfiguration.get("observerPos") == None or \
                           self._instanceconfiguration.get("cross-traffic") == None or \
                           self._instanceconfiguration.get("access-technology") == None or \
                           self._instanceconfiguration.get("sender-identity") == None or \
                           self._instanceconfiguration.get("receiver-identity") == None or \
                           self._instanceconfiguration.get("trace") == None:
                                logging.error("Error: Wrong configuration")
                                self._status = self.__WRONG_CONFIGURATION
                                return

        def print_instanceconfiguration(self):
                self._throw_if_invalid()
                
                logging.info("\n")
                logging.info("NetworkTraceManager instance configuration: ")
                for key in self._instanceconfiguration:
                        logging.info ("\t" + key + " = " + self._instanceconfiguration.get(key))

        def _compact_trace(self, tracelist):
                max_tracegap = self._instanceconfiguration.getint("max_tracegap_seconds")
                logging.info("\tmax_tracegap=" + str(max_tracegap))

                previous_time = tracelist[0]["timestamp"]                
                for i in range(0, len(tracelist)):
                        diff_seconds = (tracelist[i]["timestamp"] - previous_time).total_seconds()
                        
                        if diff_seconds > max_tracegap:
                                diff_seconds -= max_tracegap                                

                                for j in range(i, len(tracelist)):
                                        tracelist[j]["timestamp"] = tracelist[j]["timestamp"] \
                                                                    - datetime.timedelta(seconds=diff_seconds)
                        
                        logging.info(str(tracelist[i]["timestamp"]) + "-" + str(previous_time) + " = " + 
                                     str((tracelist[i]["timestamp"] - previous_time).total_seconds()))
                        
                        previous_time = tracelist[i]["timestamp"]
                        


        def _get_traces(self):
                self._throw_if_invalid()

                rtt_tracefile = self._select_trace_file("RTT")
                bandwidth_tracefile = self._select_trace_file("Bandwidth")
                logging.info(f'RTT tracefile:       {rtt_tracefile}')
                logging.info(f'Bandwidth tracefile: {bandwidth_tracefile}')

                if rtt_tracefile == None or bandwidth_tracefile == None:
                        self._status = self.__WRONG_INPUTFILEPATH
                        return

                starting_time = NetworkTraceManager._swallow_trace(
                        rtt_tracefile,
                        self._rtt_trace,
                        'rtt',
                        None)
                assert starting_time is not None
                NetworkTraceManager._swallow_trace(
                        bandwidth_tracefile,
                        self._bandwidth_trace,
                        'bandwidth',
                        starting_time)

                self._compact_trace(self._rtt_trace)
                self._compact_trace(self._bandwidth_trace)

        @staticmethod
        def _swallow_trace(trace_filename, trace_out, trace_type, starting_time):
                assert trace_type in ['rtt', 'bandwidth']
                assert len(trace_out) == 0

                with open (trace_filename, "r") as input_tracefile:
                        # read whole file (1 file == 1 line)
                        data_list = input_tracefile.readline().split(",")

                        assert len(data_list) >= 2

                        # select random starting point, unless the client
                        # specified a given starting point to use as argument
                        #
                        # never select the first element as the starting element
                        # (not to concern with that corner case)
                        if starting_time:
                                # select the starting_item as the element before
                                # the one exceeding the given time (if this happens
                                # at the very first element, then the starting_item
                                # is 0), or if no elements exceed the given
                                # time then we set starting_time to the last
                                # element
                                starting_item = len(data_list) - 1
                                for i in range(len(data_list)):
                                        trace_timestamp = datetime.datetime.strptime(
                                                data_list[i].split("_")[0].strip(),
                                                datetime_format)
                                        if trace_timestamp > starting_time:
                                                starting_item = i - 1 if i > 0 else 0
                                                break
                        else:
                                starting_item = random.randint(1, len(data_list) - 1)

                        # insert all elements from the starting one onward
                        #
                        # the timestamp is kept the same as the
                        # actual timestamp read from file
                        for i in range(starting_item, len(data_list)):
                                trace_timestamp = datetime.datetime.strptime(
                                        data_list[i].split("_")[0].strip(),
                                        datetime_format)
                                trace_data = data_list[i].split("_")[1].strip()

                                trace_out.append({
                                        "timestamp": trace_timestamp,
                                        trace_type: trace_data,
                                        "absolute_timestamp": trace_timestamp})

                        last_timestamp = datetime.datetime.strptime(
                                        data_list[len(data_list) - 1].split("_")[0].strip(),
                                        datetime_format)

                        # insert all elements preceding the starting one
                        # 
                        # the timestamp is modified so as to pretend
                        # that the values before the starting element have been
                        # obtained _after_ that (looping)
                        #
                        # however, the absolute timestamp is kept equal to
                        # the actual timestamp from the trace file
                        first_looped_timestamp = datetime.datetime.strptime(
                                        data_list[0].split("_")[0].strip(),
                                        datetime_format)
                        for i in range(0, starting_item):
                                trace_timestamp = datetime.datetime.strptime(
                                        data_list[i].split("_")[0].strip(),
                                        datetime_format)
                                trace_data = data_list[i].split("_")[1].strip()
                                adjusted_timestamp = \
                                        last_timestamp + \
                                        (trace_timestamp - first_looped_timestamp)

                                trace_out.append({
                                        "timestamp": adjusted_timestamp,
                                        trace_type: trace_data,
                                        "absolute_timestamp": trace_timestamp})

                        return datetime.datetime.strptime(
                                        data_list[starting_item].split("_")[0].strip(),
                                        datetime_format)
                return None

        def _select_trace_file(self, m):
                typeofmeasure = self._instanceconfiguration.get("typeofmeasure").strip()
                command = self._instanceconfiguration.get("protocol").strip() + m.strip()
                observerPos = self._instanceconfiguration.get("observerPos").strip()
                cross_traffic = self._instanceconfiguration.get("cross-traffic").strip()
                access_technology = self._instanceconfiguration.get("access-technology").strip()
                sender_identity = self._instanceconfiguration.get("sender-identity").strip()
                receiver_identity = self._instanceconfiguration.get("receiver-identity").strip()

                logging.info("searching for " + typeofmeasure + " " + command + ", " + observerPos + ", " + \
                         cross_traffic + ", " + access_technology + ", " + sender_identity + ", " + \
                         receiver_identity)

                with open (self._instanceconfiguration.get("mapping_file"), "r") as inputjson:
                        data = json.load(inputjson)

                for elem in data:
                        path = None
                        for key in elem :
                                if key == "typeofmeasure" and typeofmeasure != elem[key]:
                                        path = None
                                        break
                                if key == "command" and command != elem[key]:
                                        path = None
                                        break 
                                if key == "ObserverPos" and observerPos != elem[key]:
                                        path = None
                                        break
                                if key == "noise" and cross_traffic != elem[key]:
                                        path = None
                                        break
                                if key == "senderIdentity" and sender_identity != elem[key]:
                                        path = None
                                        break
                                if key == "receiverIdentity" and receiver_identity != elem[key]:
                                        path = None
                                        break
                                if key == "access-technology" and access_technology != elem[key]:
                                        path = None
                                        break
                                if key == "path":
                                        path = elem[key]                                                            
                                if key == "direction" and elem[key] == "downstream":
                                        if (sender_identity == "Client" and receiver_identity == "Observer")  or\
                                           (sender_identity == "Observer" and receiver_identity == "Server"):
                                                path = None
                                                break    
                                if key == "direction" and elem[key] == "upstream":
                                        if (sender_identity == "Observer" and receiver_identity == "Client")  or\
                                           (sender_identity == "Server" and receiver_identity == "Observer"):
                                                path = None
                                                break 
                                if key == "first-endpoint":
                                        if  elem[key]!=sender_identity and elem[key]!=receiver_identity:
                                                path = None
                                                break
                                       
     
                        if path != None:
                                logging.info("trace_file:\t" + path)
                                return path

                return None


        def _compute_randomtimes(self, tracefile):
                #t_start & t_end are selected randomly
                with open(tracefile, "r") as input_tracefile:
                        data_list = input_tracefile.readline().split(",")  
                        first_timestamp = data_list[0].split("_")[0].strip()
                        last_timestamp = data_list[-1].split("_")[0].strip()
                        
                        first_time = datetime.datetime.strptime(first_timestamp, datetime_format)
                        last_time = datetime.datetime.strptime(last_timestamp, datetime_format)
                        
                        trace_duration_sec = (last_time - first_time).seconds
                        randomdelta_sec = random.random() * trace_duration_sec
                        random_tstart = first_time + datetime.timedelta(seconds = randomdelta_sec)

                        residual_duration_sec = (last_time - random_tstart).seconds
                        randomdelta_sec = random.random() * residual_duration_sec
                        random_tend = random_tstart + datetime.timedelta(seconds = randomdelta_sec)

                        assert random_tend <= last_time

                        logging.info ("t_start: " + str(random_tstart) + "\t\t(randomly generated)")
                        logging.info ("t_end: " + str(random_tend) + "\t\t(randomly generated)")
                        
                        return random_tstart, random_tend