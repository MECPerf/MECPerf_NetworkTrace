import configparser
import random
import datetime
import logging

OK = 0
WRONG_CONFIGURATION = 1
logging.basicConfig(filename="file.log", filemode='a', 
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S', 
                    level=logging.DEBUG)

logging.info("Running Urban Planning")

datetime_format = "%Y-%m-%d %H:%M:%S.%f"

class NetworkTraceManager:
        def __init__(self, config):
                self.status = OK
                self.delay_trace = []
                self.delay_index = 0
                self.bandwidth_trace = []
                self.bandwidth_index = 0                
                self.instanceconfiguration = config

                self.check_instanceconfiguration()
                self.print_instanceconfiguration()

                if self.instanceconfiguration.getint("seed") != None:
                        #initialize the random generator
                        random.seed(self.instanceconfiguration.getint("seed"))

                self.get_traces()

                logging.info("delay: " + str(self.delay_trace))
                logging.info("bandwidth: " + str(self.bandwidth_trace))

                
        def get_delay(self):
                if self.status != OK:
                        return self.status
                
                delay = self.delay_trace[self.delay_index]["delay"]
                self.delay_index = (self.delay_index + 1) % len(self.delay_trace) 


                return delay
        def get_bandwidth(self):
                if self.status != OK:
                        return self.status

                bandwidth = self.bandwidth_trace[self.bandwidth_index]["bandwidth"]
                self.bandwidth_index = (self.bandwidth_index + 1) % len(self.bandwidth_trace) 

                return bandwidth 
        def get_networkvalues(self):
                if self.status != OK:
                        return self.status

                delay = self.get_delay()
                bandwidth = self.get_bandwidth()

                return delay, bandwidth


        def check_instanceconfiguration(self):
                if self.instanceconfiguration.getint("seed") == None:
                        if self.instanceconfiguration.get("t_start") == None:
                                print ("Error: seed and t_start values are both missing")
                                self.status = WRONG_CONFIGURATION

                        if self.instanceconfiguration.get("t_start") != None and \
                           self.instanceconfiguration.get("t_end") == None:
                                print ("t_end is missing (?)")
                                #self.status = ?
                        
                if self.instanceconfiguration.get("t_start") != None and \
                   self.instanceconfiguration.get("t_end") != None and \
                   datetime.datetime.strptime(self.instanceconfiguration.get("t_start"), datetime_format) > \
                   datetime.datetime.strptime(self.instanceconfiguration.get("t_end"), datetime_format):
                        print ("Error: t_start is greater than t_end")
                        self.status = WRONG_CONFIGURATION
        def print_instanceconfiguration(self):
                if self.status != OK:
                        return self.status
                
                
                logging.info("\n")
                logging.info ("NetworkTraceManager instance configuration: ")
                for key in self.instanceconfiguration:
                        logging.info ("\t" + key + " = " + self.instanceconfiguration.get(key))


        def get_traces(self):
                if self.status != OK:
                        return self.status

                delay_tracefile = self.select_trace_file("delay")
                bandwidth_tracefile = self.select_trace_file("bandwidth")

                t_start, t_end = self.compute_randomtimes(delay_tracefile)
                minimum_tracelen = self.instanceconfiguration.getint("mininimum_tracelen")

                #read the delays
                with open (delay_tracefile, "r") as input_tracefile:
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
                                if len(self.delay_trace) >= minimum_tracelen and max_timestamp > t_end:
                                        break

                                self.delay_trace.append({"timestamp": trace_timestamp, "delay": trace_data})   
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

                                self.bandwidth_trace.append({"timestamp": trace_timestamp, "bandwidth": trace_data})


        def select_trace_file(self, typeof_measure):
                print ("select_trace_file("+ typeof_measure +"):  TODO")
                
                return "prova.txt"


        def compute_randomtimes(self, tracefile):
                if self.instanceconfiguration.get("t_start") != None:
                        #t_start & t_end from configuration
                        t_start = datetime.datetime.strptime(self.instanceconfiguration.get("t_start"), datetime_format)
                        t_end = datetime.datetime.strptime(self.instanceconfiguration.get("t_end"), datetime_format)

                        logging.info ("t_start: " + str(t_start) + "\t\t(from configuration)")
                        logging.info ("t_end: " + str(t_end) + "\t\t(from configuration)")
                                
                        print "TODO: E se viene passato solo t_start?"

                        return t_start, t_end
                
                #t_start & t_end are selected randomly
                with open (tracefile, "r") as input_tracefile:
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

                                


                                

                
                                


                

 
        
                                






