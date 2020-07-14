#!/usr/bin/env python3

import configparser
import random
import datetime
import logging
import json


logging.basicConfig(filename="file.log", filemode='w', 
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(funcName)s(): %(message)s', 
                    datefmt='%H:%M:%S', level=logging.DEBUG)

datetime_format = "%Y-%m-%d %H:%M:%S.%f"

class NetworkTraceManager:
        __OK = 0
        __WRONG_CONFIGURATION = -1
        __WRONG_INPUTFILEPATH = -2

        @staticmethod
        def get_tracelist(typeofmeasure = None, senderIdentity = None, receiverIdentity = None, 
                          first_endpoint = None, second_endpoint = None,
                          direction = None, command = None, noise = None, observerPos = None, 
                          access_technology = None):
                trace_list = []

                with open ("inputFiles/mapping.json", "r") as inputjson:
                        data = json.load(inputjson)

                for elem in data:
                        config = ""
                        discard_elem = False
                        for key in elem :
                                if discard_elem == True:
                                        continue

                                if key == "typeofmeasure":
                                        if typeofmeasure != None and typeofmeasure != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_typeofmeasure = str(key) + ": " + elem[key]
                                if key == "command":
                                        if command != None and command != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_command = str(key) + ": " + elem[key]    
                                if key == "direction":
                                        if direction != None and direction != elem[key]:
                                                discard_elem = True
                                                continue
                                                
                                        if elem[key] != None:
                                                curr_direction = str(key) + ": " + (elem[key])
                                        else:
                                                curr_direction = None
                                if key == "ObserverPos":                                        
                                        if observerPos != None and observerPos != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_observerPos = str(key) + ": " + elem[key]
                                if key == "noise":
                                        if noise != None and noise != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_noise = str(key) + ": " + elem[key]
                                if key == "senderIdentity":              
                                        if senderIdentity != None and senderIdentity != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_senderIdentity  = str(key) + ": " + elem[key]
                                if key == "receiverIdentity":
                                        if receiverIdentity != None and receiverIdentity != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_receiverIdentity = str(key) + ": " + elem[key]
                                if key == "access-technology":
                                        if access_technology != None and access_technology != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_accesstech = str(key) + ": " + elem[key]
                                if key == "path":
                                        curr_path = elem[key]

                                if key == "first-endpoint":              
                                        if first_endpoint != None and first_endpoint != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_firstendpoint  = str(key) + ": " + elem[key]
                                if key == "second-endpoint":
                                        if second_endpoint != None and second_endpoint != elem[key]:
                                                discard_elem = True
                                                continue

                                        curr_secondendpoint = str(key) + ": " + elem[key]
                                        
                        if discard_elem != True:
                                if "RTT" in curr_command  and curr_direction != None:
                                        continue
                                
                                config = curr_typeofmeasure + ", " + curr_command + ", " 
                                config += curr_observerPos + ", " + curr_noise  +", " 

                                if "TCPBandwidth" in curr_command or "UDPBandwidth" in curr_command: 
                                        config += curr_direction + ", " 
                                        config += curr_senderIdentity + ", " + curr_receiverIdentity + ", "
                                elif "TCPRTT" in curr_command or "UDPRTT" in curr_command: 
                                        config += curr_firstendpoint + ", " + curr_secondendpoint + ", "
                                config += curr_accesstech
                                

                                trace_list.append(config)

                
                return trace_list


        def __init__(self, config):
                self.status = self.__OK
                self.rtt_trace = []
                self.rtt_index = 0
                self.rtt_timestamp = None
                self.bandwidth_trace = []
                self.bandwidth_index = 0    
                self.bandwidth_timestamp = None            
                self.instanceconfiguration = config

                self.check_instanceconfiguration()
                self.print_instanceconfiguration()
                
                #initialize the random generator
                random.seed(self.instanceconfiguration.getint("seed"))

                self.get_traces()
                self.rtt_timestamp = self.rtt_trace[0]["timestamp"]
                self.bandwidth_timestamp = self.bandwidth_trace[0]["timestamp"]

                logging.info("rtt: " + str(self.rtt_trace))
                logging.info("rtt_timestamp: " + str(self.rtt_timestamp))
                logging.info("bandwidth: " + str(self.bandwidth_trace))
                logging.info("bandwidth_timestamp: " + str(self.bandwidth_timestamp))
                

        def get_rtt(self, sec):
                if self.status != self.__OK:
                        return self.status
 
                while (True):
                        next_index = (self.rtt_index + 1) % len(self.rtt_trace)
                        if next_index != 0:
                                next_timestamp = self.rtt_trace[self.rtt_index + 1]["timestamp"]
                        else:
                                max_tracegap = self.instanceconfiguration.getint("max_tracegap_seconds")
                                next_timestamp = self.rtt_trace[-1]["timestamp"] + \
                                                 datetime.timedelta(seconds=max_tracegap)


                        if self.rtt_timestamp + datetime.timedelta(seconds=sec) >= next_timestamp:
                                self.rtt_index = next_index

                                if next_index == 0:
                                        diff_seconds = (self.rtt_trace[-1]["timestamp"] -
                                                        self.rtt_trace[0]["timestamp"]  + 
                                                        datetime.timedelta(seconds=max_tracegap)).total_seconds()
                                        for elem in self.rtt_trace:
                                                elem["timestamp"] = elem["timestamp"] + \
                                                                    datetime.timedelta(seconds=diff_seconds)

                                        logging.info("rrt: " + str(self.rtt_trace))


                        next_index = (self.rtt_index + 1) % len(self.rtt_trace)
                        if next_index != 0:
                                next_timestamp = self.rtt_trace[self.rtt_index + 1]["timestamp"]
                        else:
                                max_tracegap = self.instanceconfiguration.getint("max_tracegap_seconds")
                                next_timestamp = self.rtt_trace[-1]["timestamp"] + \
                                                 datetime.timedelta(seconds=max_tracegap)
        
                        if self.rtt_timestamp + datetime.timedelta(seconds=sec) < next_timestamp:
                                self.rtt_timestamp += datetime.timedelta(seconds=sec)
                
                                return self.rtt_trace[self.rtt_index]["rtt"], self.rtt_timestamp, \
                                       self.rtt_trace[self.rtt_index]["absolute_timestamp"]

        def get_bandwidth(self, sec):
                if self.status != self.__OK:
                        return self.status

                while (True):
                        next_index = (self.bandwidth_index + 1) % len(self.bandwidth_trace)
                        if next_index != 0:
                                next_timestamp = self.bandwidth_trace[self.bandwidth_index + 1]["timestamp"]
                        else:
                                max_tracegap = self.instanceconfiguration.getint("max_tracegap_seconds")
                                next_timestamp = self.bandwidth_trace[-1]["timestamp"] + \
                                                 datetime.timedelta(seconds=max_tracegap)


                        if self.bandwidth_timestamp + datetime.timedelta(seconds=sec) >= next_timestamp:
                                self.bandwidth_index = next_index

                                if next_index == 0:
                                        diff_seconds = (self.bandwidth_trace[-1]["timestamp"] -
                                                        self.bandwidth_trace[0]["timestamp"]  + 
                                                        datetime.timedelta(seconds=max_tracegap)).total_seconds()
                                        for elem in self.bandwidth_trace:
                                                elem["timestamp"] = elem["timestamp"] + \
                                                                    datetime.timedelta(seconds=diff_seconds)

                                        logging.info(self.bandwidth_trace)


                        next_index2 = (self.bandwidth_index + 1) % len(self.bandwidth_trace)
                        if next_index2 != 0:
                                next_timestamp2 = self.bandwidth_trace[self.bandwidth_index + 1]["timestamp"]
                        else:
                                max_tracegap = self.instanceconfiguration.getint("max_tracegap_seconds")
                                next_timestamp2 = self.bandwidth_trace[-1]["timestamp"] + \
                                                  datetime.timedelta(seconds=max_tracegap)

        
                        if self.bandwidth_timestamp + datetime.timedelta(seconds=sec) < next_timestamp2:
                                self.bandwidth_timestamp += datetime.timedelta(seconds=sec)
                
                                return self.bandwidth_trace[self.bandwidth_index]["bandwidth"], \
                                       self.bandwidth_timestamp, \
                                       self.bandwidth_trace[self.bandwidth_index]["absolute_timestamp"]

            

        def get_networkvalues(self, sec):
                if self.status != self.__OK:
                        return self.status, self.status

                rtt = self.get_rtt(sec)
                bandwidth = self.get_bandwidth(sec)

                return rtt, bandwidth
 

        def check_instanceconfiguration(self):
                if self.instanceconfiguration.getint("seed") == None:
                        print("Error: seed is missing")
                        self.status = self.__WRONG_CONFIGURATION
                        return

                if self.instanceconfiguration.get("typeofmeasure") == None:
                        print("Error: typeofmeasure is missing")
                        self.status = self.__WRONG_CONFIGURATION
                        return
                
                if self.instanceconfiguration.get("typeofmeasure") == "active":
                        if self.instanceconfiguration.get("protocol") == None or \
                           self.instanceconfiguration.get("observerPos") == None or \
                           self.instanceconfiguration.get("cross-traffic") == None or \
                           self.instanceconfiguration.get("access-technology") == None or \
                           self.instanceconfiguration.get("sender-identity") == None or \
                           self.instanceconfiguration.get("receiver-identity") == None or \
                           self.instanceconfiguration.get("trace") == None:
                                print("Error: Wrong configuration")
                                self.status = self.__WRONG_CONFIGURATION
                                return                
        def print_instanceconfiguration(self):
                if self.status != self.__OK:
                        return self.status
                
                logging.info("\n")
                logging.info("NetworkTraceManager instance configuration: ")
                for key in self.instanceconfiguration:
                        logging.info ("\t" + key + " = " + self.instanceconfiguration.get(key))


        def compact_trace(self, tracelist):
                max_tracegap = self.instanceconfiguration.getint("max_tracegap_seconds")
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
                        


        def get_traces(self):
                if self.status != self.__OK:
                        return self.status

                rtt_tracefile = self.select_trace_file("RTT")
                bandwidth_tracefile = self.select_trace_file("Bandwidth")
                if rtt_tracefile == None or bandwidth_tracefile == None:
                        self.status = self.__WRONG_INPUTFILEPATH
                        return


                t_start, t_end = self.compute_randomtimes(rtt_tracefile)
                minimum_tracelen = self.instanceconfiguration.getint("mininimum_tracelen")

                #read the rtt
                with open (rtt_tracefile, "r") as input_tracefile:
                        data_list = input_tracefile.readline().split(",")  

                        i = 0
                        restarted = False
                        max_timestamp = t_start

                        while (True):
                                
                                trace_timestamp = datetime.datetime.strptime(data_list[i].split("_")[0].strip(), datetime_format)
                                if not restarted and trace_timestamp < t_start:
                                        i = (i + 1) % len(data_list)
                                        if i == 0: 
                                                restarted = True
                                        continue

                                trace_data = data_list[i].split("_")[1].strip()
                                if trace_timestamp > max_timestamp:
                                        max_timestamp = trace_timestamp
                                                        
                                i = (i + 1) % len(data_list)
                                if i == 0:
                                        restarted = True
                                if len(self.rtt_trace) >= minimum_tracelen and max_timestamp > t_end:
                                        break

                                self.rtt_trace.append({"timestamp": trace_timestamp, "rtt": trace_data, "absolute_timestamp": trace_timestamp})   
                #read the bandwidth values
                with open (bandwidth_tracefile, "r") as input_tracefile:
                        data_list = input_tracefile.readline().split(",")  

                        i = 0
                        restarted = False
                        max_timestamp = t_start

                        while (True):
                                
                                trace_timestamp = datetime.datetime.strptime(data_list[i].split("_")[0].strip(), datetime_format)
                                if not restarted and trace_timestamp < t_start:
                                        i = (i + 1) % len(data_list)
                                        if i == 0: 
                                                restarted = True
                                        continue

                                trace_data = data_list[i].split("_")[1].strip()
                                if trace_timestamp > max_timestamp:
                                        max_timestamp = trace_timestamp
                                                        
                                i = (i + 1) % len(data_list)
                                if i == 0:
                                        restarted = True

                                if len(self.bandwidth_trace) >= minimum_tracelen and max_timestamp > t_end:                                        
                                        break

                                self.bandwidth_trace.append({"timestamp": trace_timestamp, "bandwidth": trace_data, "absolute_timestamp": trace_timestamp})

                self.compact_trace(self.rtt_trace)
                self.compact_trace(self.bandwidth_trace)

        

        def select_trace_file(self, m):
                typeofmeasure = self.instanceconfiguration.get("typeofmeasure").strip()
                command = self.instanceconfiguration.get("protocol").strip() + m.strip()
                observerPos = self.instanceconfiguration.get("observerPos").strip()
                cross_traffic = self.instanceconfiguration.get("cross-traffic").strip()
                access_technology = self.instanceconfiguration.get("access-technology").strip()
                sender_identity = self.instanceconfiguration.get("sender-identity").strip()
                receiver_identity = self.instanceconfiguration.get("receiver-identity").strip()

                logging.info("searching for " + typeofmeasure + " " + command + ", " + observerPos + ", " + \
                         cross_traffic + ", " + access_technology + ", " + sender_identity + ", " + \
                         receiver_identity)

                with open ("inputFiles/mapping.json", "r") as inputjson:
                        data = json.load(inputjson)

                for elem in data:
                        config = ""
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
                                print ("trace_file:\t" + path)
                                logging.info("trace_file:\t" + path)
                                return path

                return None


        def compute_randomtimes(self, tracefile):
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