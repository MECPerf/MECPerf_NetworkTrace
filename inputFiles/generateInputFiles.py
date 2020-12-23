#!/usr/bin/env python3
 

import configparser
import mysql.connector
import os
import errno
import sys
import json
import datetime
import logging

from mysql.connector import Error

_FAILURE_CODE = "\033[1;31m"
_RESET_CODE= "\033[0m"

_INI_FILENAME = "generateInputFiles.ini"
_GENERAL_LOGFILENAME = "generateInputFiles.log"

log = logging.getLogger()

datetime_format = "%Y-%m-%d %H:%M:%S.%f"

 

def connect(configuration_parser, section, log):
    host_ip = configuration_parser.get(section, "host")
    user_name = configuration_parser.get(section, "user")
    database_name =configuration_parser.get(section, "database")
    password = configuration_parser.get(section, "password")

    # Connect to MySQL database
    print ("Connecting to MySQL database using")
    print ("\thost: " + host_ip)
    print ("\tuser: " + user_name)
    print ("\tdatabase: " + database_name)
    print ("\tpassword: " + password)
    print ("\n\n")
        
    try:
        mydb = mysql.connector.connect(host = host_ip, database = database_name, user = user_name,
                                       password = password)
        if mydb.is_connected():
            print('Connection Established')
            log.info("Connection established with DB '" + database_name + "' on host = " + host_ip + \
                     " and user = " + user_name)
    except:
        print(_FAILURE_CODE + "MySQL connection failed" + _RESET_CODE)
        log.error("MySQL connection failed")
        exit(1)

    return mydb

def initialize_generallogfile():
    filehandler = logging.FileHandler(_GENERAL_LOGFILENAME, "w")
    formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(funcName)s %(message)s', datefmt='%H:%M:%S')
    filehandler.setFormatter(formatter)
    general_log = logging.getLogger()
    general_log.addHandler(filehandler)
    general_log.setLevel(logging.DEBUG)

    print (_GENERAL_LOGFILENAME + " initialized")
    general_log.info(_GENERAL_LOGFILENAME + " initialized")

    return general_log
def init_logfile(logpath):
    for hdlr in log.handlers[:]:
        if isinstance(hdlr, logging.FileHandler):
            if _GENERAL_LOGFILENAME not in hdlr.baseFilename:
                log.removeHandler(hdlr)

    newfilehandler = logging.FileHandler(logpath, "w")
    formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S')
    newfilehandler.setFormatter(formatter)
    log.addHandler(newfilehandler)
    log.setLevel(logging.DEBUG)

    return log
 


def createfolder(directoryname, log):
    try:
        os.makedirs(directoryname)
    except OSError as error:
        if error.errno != errno.EEXIST:
            print (error)
            log.error(directoryname + " creation failed")
            sys.exit(1)
    
    log.info("folder " + directoryname + " created")

def get_bandwidth_burstresults_query(burstID):
    query  = "SELECT TestNumber, Test.ID, Timestamp, Direction, Command, SenderIdentity, ReceiverIdentity, "
    query += "SenderIPv4Address, ReceiverIPv4Address, Keyword, PackSize, NumPack, "    
    query += "(1.0 * (SUM(kBytes * 8))/(1.0 * SUM(nanotimes) / 1000000000))as 'Kbps' "
    query += "FROM Test INNER JOIN BandwidthMeasure ON Test.ID = BandwidthMeasure.id "
    query += "WHERE Test.ID = '" + str(burstID) + " ORDER BY Timestamp asc"

    return query
def get_latency_burstresults_query(burstID):
    query  = "SELECT TestNumber, Test.ID, Timestamp, Direction, Command, SenderIdentity, ReceiverIdentity, "
    query += "SenderIPv4Address, ReceiverIPv4Address, Keyword, PackSize, NumPack, latency "
    query += "FROM Test INNER JOIN RttMeasure ON Test.ID = RttMeasure.id "
    query += "WHERE Test.ID = " + str(burstID) +" ORDER BY Timestamp asc"

    return query
def get_burstresults_query(command, burstID, log):
    if command == "TCPBandwidth" or command == "UDPBandwidth":
        return get_bandwidth_burstresults_query(burstID=burstID)
    if command == "TCPRTT" or command == "UDPRTT":
        return get_latency_burstresults_query(burstID=burstID)
    
    print (_FAILURE_CODE + "Unknown type of measure " + str(command) + _RESET_CODE)
    log.error(print ("Unknown type of measure " + str(command)))
    exit(1)    

def compute_bandwidthburstresults(cursor, filename, burstresults_query, temp_mapping, log):
    cursor.execute(burstresults_query) 
    data = cursor.fetchall()   
    columns = cursor.description
    hdr = str(columns[0][0])
    for j in range(1, len(columns)):
        hdr += ", " + str(columns[j][0])

    log.info(burstresults_query + "\n\t" + hdr + "\n\t" + \
             "number of measurements for the current burst = " +  str(cursor.rowcount)) 

    with open(filename, "w+") as out:
        for i in range(0, len(data)):
            row = data[i]
            timestamp = row[2]
            timestamp = timestamp.strftime(datetime_format).strip()
            command = row[5]
            senderIPv4Address = row[7]
            receiverIPv4Address = row[8]
            Kbps = float(row[12])

            assert command in ["TCPBandwidth", "UDPBandwidth"]

            if i == 0:
                temp_mapping["first_timestamp"].append(timestamp)
            if i == (len(data) - 1):
                temp_mapping["last_timestamp"].append(timestamp)
                        
            Mbps = Kbps/1000
            
            out.write(timestamp +"_" + str(Mbps))                    
def compute_rttburstresults(cursor, filename, burstresults_query, temp_mapping, log):
    cursor.execute(burstresults_query) 
    data = cursor.fetchall()   

    columns = cursor.description
    hdr = str(columns[0][0])
    for j in range(1, len(columns)):
        hdr += ", " + str(columns[j][0])

    log.info(burstresults_query + "\n\t" + hdr + "\n\t" + "number of measurements for the current burst = " +\
             str(cursor.rowcount)) 

    with open(filename, "w+") as out:
        for i in range(0, len(data)):
            row = data[i]
            if i != 0:
                previous_timestamp = timestamp
            timestamp = row[2]
            timestamp = timestamp.strftime(datetime_format).strip()
            command = row[4]
            senderIPv4Address = row[7]
            receiverIPv4Address = row[8]
            latency = row[12]

            if i != 0:
                timestamp = max (datetime.datetime.strptime(timestamp, datetime_format), datetime.datetime.strptime(previous_timestamp, datetime_format) + datetime.timedelta(milliseconds=latency))
                timestamp = timestamp.strftime(datetime_format).strip()

            assert command == temp_mapping["command"]

            if i == 0:
                temp_mapping["first_timestamp"].append(timestamp)
            if i == (len(data) - 1):
                temp_mapping["last_timestamp"].append(timestamp)
                        
            out.write(timestamp +"_" + str(latency))
            if i < len(data) - 1:
                out.write(",")
            
            

    log.info("temp_mapping added\n\t" + str(temp_mapping))
def compute_burstresults(cursor, filename, command, burstID, temp_mapping, generallog, tracelog):
    burstresults_query = get_burstresults_query(command=command, burstID=burstID, log=generallog)

    if command == "TCPBandwidth" or command == "UDPBandwidth":
        compute_bandwidthburstresults(cursor=cursor, filename=filename, burstresults_query=burstresults_query, 
                                      temp_mapping=temp_mapping, log=tracelog)
        return
    if command == "TCPRTT" or command == "UDPRTT":
        compute_rttburstresults(cursor=cursor, filename=filename, burstresults_query=burstresults_query, 
                                temp_mapping=temp_mapping, log=tracelog)
        return
    
    print (_FAILURE_CODE + "Unknown type of measure " + str(command) + _RESET_CODE)
    log.error(print ("Unknown type of measure " + str(command)))
    exit(1)    



def get_rtt_testnumber_list(command, direction, access_tech, segment, observerPos, noise, t0, tn):
    assert command in ["TCPRTT", "UDPRTT"]
    assert segment in ["access-MEC", "MEC-cloud"]
    assert observerPos in ["edge", "cloud"]
      
    if "access" in segment:
        identity= "Client"
    else:
        identity = "Server"
    
    query  = "SELECT * FROM Test WHERE (SenderIdentity = '" + identity + "' OR ReceiverIdentity = '" 
    query += identity + "') "

    if access_tech== "wifi":
        query += "AND Keyword NOT LIKE \"%LTE%\" "
    elif access_tech == "lte":
        query += "AND Keyword LIKE \"%LTE%\" "

    query += "AND Keyword LIKE '%experiment_active_%' AND Keyword LIKE '%noise" + noise + "%' "
    query += "AND Timestamp > '" + str(t0) + "' AND Timestamp < '" + str(tn) + "' AND Command = '" + command + "' "
    
    if observerPos == "edge":
        query += "AND Keyword LIKE '%local%' "
    elif observerPos == "cloud":
        query += "AND Keyword LIKE '%remote%' "
    
    query += "ORDER BY TestNumber asc"

    return query
def get_bandwidth_testnumber_list(command, direction, access_tech, segment, observerPos, noise, t0, tn):
    assert command in ["TCPBandwidth", "UDPBandwidth"]
    assert observerPos in ["edge", "cloud"]

    query  = "SELECT * FROM Test WHERE Direction = '" + direction + "' AND SenderIdentity = '" + segment[0] + "' " 
    query += "AND ReceiverIdentity = '" + segment[1] + "' "

    if access_tech== "wifi":
        query += "AND Keyword NOT LIKE \"%LTE%\" "
    elif access_tech == "lte":
        query += "AND Keyword LIKE \"%LTE%\" "

    query += "AND Keyword LIKE '%experiment_active_%' AND Keyword LIKE '%noise" + noise + "%' "
    query += "AND Timestamp > '" + str(t0) + "' AND Timestamp < '" + str(tn) + "' AND Command = '" + command + "' "
    
    if observerPos == "edge":
        query += "AND Keyword LIKE '%local%' "
    elif observerPos == "cloud":
        query += "AND Keyword LIKE '%remote%' "
    
    query += "ORDER BY TestNumber asc"

    return query
def get_testnumbers_list(command, direction, access_tech, segment, observerPos, noise, t0, tn, log):
    if command == "TCPRTT" or command == "UDPRTT":
        return get_rtt_testnumber_list(command=command, direction=direction, access_tech=access_tech, 
                                       segment=segment, observerPos=observerPos, noise=noise, t0=t0, tn=tn)

    if command == "TCPBandwidth" or command == "UDPBandwidth":
        return get_bandwidth_testnumber_list(command=command, direction=direction, access_tech=access_tech, 
                                       segment=segment, observerPos=observerPos, noise=noise, t0=t0, tn=tn)
        
    print (_FAILURE_CODE + "Unknown type of measure " + str(command) + _RESET_CODE)
    log.error(print ("Unknown type of measure " + str(command)))
    exit(1)    
def compute_testnumberList(cursor, query, log):
    testnumber_list = []
        
    cursor.execute(query) 
    testnumber_data = cursor.fetchall()                    
    testnumber_columns = cursor.description
    hdr = str(testnumber_columns[0][0])
    for j in range(1, len(testnumber_columns)):
        hdr += ", " + str(testnumber_columns[j][0])
    for i in range(0, len(testnumber_data)):
        testnumber_list.append(testnumber_data[i][1])
    
    log.info(query + "\n\t" + hdr + "\n\t# of burst = " +  str(cursor.rowcount) + "\n\t" +\
             "burst id = " + str(testnumber_list) + "\n")
    return testnumber_list

def initialize_mappingentry(command, noise, segment, direction, access_technology, observerposition):
    temp_mapping = {"typeofmeasure": "active", "command":command, "direction":direction, 
                    "access-technology":access_technology, "ObserverPos":observerposition, "noise":noise, 
                    "path":[], "first_timestamp":[], "last_timestamp":[]}
    if command in ["TCPBandwidth", "UDPBandwidth"]:
        temp_mapping["senderIdentity"] = segment[0]
        temp_mapping["receiverIdentity"] = segment[1] 
    elif command == "TCPRTT" or command == "UDPRTT":
        assert segment in ["access-MEC", "MEC-cloud"]
        
        temp_mapping["second-endpoint"] = "Observer"
        if "access" in segment:
            temp_mapping["first-endpoint"] = "Client"
        else:
            temp_mapping["first-endpoint"] = "Server"
    
    return temp_mapping
def compute_inputfilename(access_tech, command, direction, noise, segment, observerposition, tracenumber):
    filename = "active/" + access_tech + "-" + command 
    if direction != None:
        filename += "-" + direction

    if command == "TCPBandwidth" or command == "UDPBandwidth":
        filename += "-noise" + noise + "_" + str(segment[0]) + "-" + str(segment[1]) + "_" + observerposition
    elif command == "TCPRTT" or command == "UDPRTT":
        assert segment in ["access-MEC", "MEC-cloud"]

        filename += "-noise" + noise + "_" 
        if "access" in segment:
            filename += "Client" + "_" + observerposition
        elif "cloud" in segment:
            filename += "Server" + "_" + observerposition        
    

    return filename + "_trace" + str(tracenumber) + ".txt"
def generate_activeinput(config_parser, section, mydb, mapping, command, direction, access_tech, segment, 
                         observerposition, log):
    noiselist = config_parser.get(section, "noise").split(",")
    starttime_str= config_parser.get(section, "starttime_" + access_tech)
    endtime_str= config_parser.get(section, "endtime_" + access_tech)

    cursor = mydb.cursor()

    log.info ("Generating input file for commend " + command + ", access-tecnology " + access_tech + \
              ", segment " + segment + " using the " + observerposition + " MECPerfObserver\n\t\t\t\t" +\
              "noiselist = " + str(noiselist) + "\n\t\t\t"  +\
              "start_time = " + starttime_str + "\n\t\t\t" +\
              "end_time = " + starttime_str + "\n\t\t\t")

    for n in noiselist:
        inputfilenumber = 0
        temp_mapping = initialize_mappingentry(command=command, noise=n, segment=segment, direction=direction, 
                                               access_technology=access_tech, observerposition=observerposition)
        testnumber_query = get_testnumbers_list(command=command, direction=direction, access_tech=access_tech, 
                                                segment=segment, observerPos=observerposition, noise=n, 
                                                t0=starttime_str, tn=endtime_str, log = log)
        testnumber_list = compute_testnumberList(cursor=cursor, query=testnumber_query, log=log)
    
        for testID in testnumber_list:
            filename = compute_inputfilename(access_tech=access_tech, command=command, direction=direction,
                                             noise=n, segment=segment, observerposition=observerposition, 
                                             tracenumber=inputfilenumber)
            #add the file to the mapping
            inputfoldername = os.path.basename(os.getcwd())
            temp_mapping["path"].append(inputfoldername + "/" + filename)   
            #initialize the log file for the current trace
            tracelog = init_logfile(filename.split(".")[0] + ".log")
            tracelog.info(filename.split(".")[0] + ".log initialized")

            compute_burstresults(cursor=cursor, filename=filename, command=command, burstID=testID, 
                                 temp_mapping=temp_mapping, generallog=log, tracelog=tracelog)

            inputfilenumber += 1
    

        mapping.append(temp_mapping)
    
    cursor.close()
    return mapping


def generate_activeinputfile(configuration_parser, mydb, activemapping, log):
    direction = ["upstream", "downstream"]
    command_bandwidth = ["TCPBandwidth", "UDPBandwidth"]
    command_rtt = ["TCPRTT", "UDPRTT"]
    accesstech = ["wifi", "lte"]

    
    for at in accesstech:
        #Bandwidth measures
        '''for c_bandwidth in command_bandwidth:
            for d in direction:
                if d == "upstream": 
                    firstSegment = ["Client", "Observer"]
                    secondSegment = ["Observer", "Server"]
                if d == "downstream": 
                    firstSegment = ["Observer", "Client"]
                    secondSegment = ["Server", "Observer"]

                activemapping = generate_activeinput(config_parser, mydb, activemapping, c_bandwidth, d, at, 
                                                     segment=firstSegment, observerposition="edge")
                activemapping = generate_activeinput(config_parser, mydb, activemapping, c_bandwidth, d, at, 
                                                     segment=secondSegment, observerposition="edge")

                activemapping = generate_activeinput(config_parser, mydb, activemapping, c_bandwidth, d, at, 
                                                     segment=firstSegment, observerposition="cloud")
                activemapping = generate_activeinput(config_parser, mydb, activemapping, c_bandwidth, d, at, 
                                                     segment=secondSegment, observerposition="cloud")
        '''
        #RTT measures
        for c_rtt in command_rtt:
            activemapping = generate_activeinput(config_parser=config_parser, 
                                section = "RTTexperiment_configuration", mydb=mydb, mapping=activemapping, 
                                command=c_rtt, direction=None, access_tech=at, segment="access-MEC", 
                                observerposition="edge", log=general_log)
            activemapping = generate_activeinput(config_parser=config_parser, 
                                section = "RTTexperiment_configuration", mydb=mydb, mapping=activemapping, 
                                command=c_rtt, direction=None, access_tech=at, segment="MEC-cloud", 
                                observerposition="edge", log=general_log)

            activemapping = generate_activeinput(config_parser=config_parser, 
                                section = "RTTexperiment_configuration", mydb=mydb, mapping=activemapping, 
                                command=c_rtt, direction=None, access_tech=at, segment="access-MEC", 
                                observerposition="cloud", log=general_log)

    return activemapping


def read_inifile(log):
    config_parser = configparser.RawConfigParser()
    config_parser.read(_INI_FILENAME)
    config_sections = config_parser.sections()

    print ("Available sections in " + _INI_FILENAME + ":")
    confsections = config_parser.sections()
    for section in confsections:
        print("\t" + section)
    
    try:
        assert "sql_configuration" in config_sections
    except:
        print(_FAILURE_CODE + "Missing 'sql_configuration' section." + _RESET_CODE)
        log.error("Missing 'sql_configuration' section.")
        exit(1)
    try:
        assert "RTTexperiment_configuration" in config_sections
    except:
        print(_FAILURE_CODE + "Missing 'RTTexperiment_configuration' section." + _RESET_CODE)
        log.error("Missing 'RTTexperiment_configuration' section.")
        exit(1)

    return config_parser
    


if __name__ == '__main__':
    
    #init_logfile(_GENERAL_LOGFILENAME)
    general_log = initialize_generallogfile()

    #read configuration file
    config_parser = read_inifile(log = general_log)
    mydb = connect(configuration_parser=config_parser, section = "sql_configuration", log = general_log)
    createfolder(directoryname = "passive", log = general_log)
    createfolder(directoryname = "active", log = general_log)

    with open ("mapping.json", "w+") as mapping_file:
        mapping = []

        mapping = generate_activeinputfile(configuration_parser = config_parser, mydb = mydb, 
                                           activemapping = mapping, log = general_log)

        json.dump(mapping, mapping_file, indent=4, sort_keys=False)

        

    mydb.close()