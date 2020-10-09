import configparser
import mysql.connector
import os
import errno
import sys
import json
import datetime
import logging

from mysql.connector import Error


filehandler = logging.FileHandler("file.log", "w")
formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S')
filehandler.setFormatter(formatter)
log = logging.getLogger()



datetime_format = "%Y-%m-%d %H:%M:%S.%f"

 
def connect(config_parser):
    # Connect to MySQL database
    print ("Connecting to MySQL database")
    print ("host: " + config_parser.get("sql_conf", "host"))
    print ("user: " + config_parser.get("sql_conf", "user"))
    print ("database: " + config_parser.get("sql_conf", "database"))
    print ("password: " + config_parser.get("sql_conf", "password"))
    print ("\n\n")
        
    try:
        mydb = mysql.connector.connect(host = config_parser.get("sql_conf", "host"), 
                                       database = config_parser.get("sql_conf", "database"), 
                                       user = config_parser.get("sql_conf", "user"),
                                       password = config_parser.get("sql_conf", "password"))
        if mydb.is_connected():
            print('Connected')
    except Error as e:
        print(e)
        sys.exit(0)

    return mydb



def init_logfile(logpath):
    for hdlr in log.handlers[:]:
        if isinstance(hdlr, logging.FileHandler):
            log.removeHandler(hdlr)

    newfilehandler = logging.FileHandler(logpath, "w")
    formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', datefmt='%H:%M:%S')
    newfilehandler.setFormatter(formatter)
    log.addHandler(newfilehandler)
    log.setLevel(logging.DEBUG)

    print (logpath)
 


def createfolder(directoryname):
    try:
        os.makedirs(directoryname)
    except OSError as error:
        if error.errno != errno.EEXIST:
            print (error)
            sys.exit(0)



def get_query(command, direction, access_tech, segment, observerPos, noise, t0, tn):
    ret = "SELECT TestNumber, Test.ID, Timestamp, Direction, Command, SenderIdentity, ReceiverIdentity, "
    ret += "SenderIPv4Address, ReceiverIPv4Address, Keyword, PackSize, NumPack, "    
    if command == "TCPBandwidth" or command == "UDPBandwidth":
        ret += "(1.0 * (SUM(kBytes * 8))/(1.0 * SUM(nanotimes) / 1000000000))as 'Kbps' "
        ret += "FROM Test INNER JOIN BandwidthMeasure ON Test.ID = BandwidthMeasure.id "
        ret += "WHERE Direction = '" + direction + "' AND SenderIdentity = '" + segment[0] + "' "
        ret += "AND ReceiverIdentity = '" + segment[1] + "' "

    elif command == "TCPRTT" or command == "UDPRTT":
        ret += "AVG(latency) "
        ret += "FROM Test INNER JOIN RttMeasure ON Test.ID = RttMeasure.id "
        ret += "WHERE (SenderIdentity = '" + segment[0] + "' OR ReceiverIdentity = '" + segment[0] + "') "
    else:
        print (ret)
        print ("\tunknown type of measure " + str(command))
        sys.exit(1)    

    if access_tech== "wifi":
        ret += "AND Keyword NOT LIKE \"%LTE%\" "
    elif access_tech == "lte":
        ret += "AND Keyword LIKE \"%LTE%\" "

    ret += "AND Keyword LIKE '%experiment_active_%' AND Keyword LIKE '%noise" + noise + "%' "
    ret += "AND Timestamp > '" + str(t0) + "' AND Timestamp < '" + str(tn) + "' AND Command = '" + command + "' "
    
    if observerPos == "edge":
        ret += "AND Keyword LIKE '%local%' "
    elif observerPos == "cloud":
        ret += "AND Keyword LIKE '%remote%' "
    else:
        print ("unknown observerPosition")
        exit(1)
    
    ret += "GROUP By Test.ID ORDER BY Timestamp asc"

    return ret



def get_testnumbers_list(command, direction, access_tech, segment, observerPos, noise, t0, tn):
    ret = "SELECT * FROM Test WHERE "   
    if command == "TCPBandwidth" or command == "UDPBandwidth":
        ret += "Direction = '" + direction + "' AND SenderIdentity = '" + segment[0] + "' " 
        ret += "AND ReceiverIdentity = '" + segment[1] + "' "
    elif command == "TCPRTT" or command == "UDPRTT":
        ret += "(SenderIdentity = '" + segment[0] + "' OR ReceiverIdentity = '" + segment[0] + "') "
    else:
        print (ret)
        print ("\tunknown type of measure " + str(command))
        sys.exit(1)    


    if access_tech== "wifi":
        ret += "AND Keyword NOT LIKE \"%LTE%\" "
    elif access_tech == "lte":
        ret += "AND Keyword LIKE \"%LTE%\" "

    ret += "AND Keyword LIKE '%experiment_active_%' AND Keyword LIKE '%noise" + noise + "%' "
    ret += "AND Timestamp > '" + str(t0) + "' AND Timestamp < '" + str(tn) + "' AND Command = '" + command + "' "
    
    if observerPos == "edge":
        ret += "AND Keyword LIKE '%local%' "
    elif observerPos == "cloud":
        ret += "AND Keyword LIKE '%remote%' "
    else:
        print ("unknown observerPosition")
        exit(1)
    
    ret += "ORDER BY TestNumber asc"

    return ret


def compute_testnumberList(cursor, query):
    testnumber_list = []
    log.info(query)
        
    testnumber_data = cursor.fetchall()                    
    testnumber_columns = cursor.description
    hdr = str(testnumber_columns[0][0])
    for j in range(1, len(testnumber_columns)):
        hdr += ", " + str(testnumber_columns[j][0])

    log.info(hdr)          
    log.info("# of rows = " +  str(cursor.rowcount))

    for i in range(0, len(testnumber_data)):
        log.info(testnumber_data[i])
        testnumber_list.append(testnumber_data[i][0])
    
    log.info("testnumber_list = " + str(testnumber_list) + "\n\n")
    return testnumber_list





def generate_activeinput(config_parser, mydb, mapping, c, d, at, segment, observerposition):
    cursor = mydb.cursor()

    if d != None:
        basefilename = "active/" + at + "-" + c + "-" + d
    else:
        basefilename = "active/" + at + "-" + c
    observerAddress = config_parser.get("experiment_conf", observerposition + "Observer" + at)
    noiselist = config_parser.get("experiment_conf", "noise").split(",")
    dates_list = config_parser.get("experiment_conf", "dates_active" + at).split(",")


    for n in noiselist:
        testnumber_query = get_testnumbers_list(command=c, direction=d, access_tech=at, segment=segment, 
                                               observerPos=observerposition, noise=n, t0=dates_list[0], 
                                               tn=dates_list[-1])

        q = get_query(command=c, direction=d, access_tech=at, segment=segment, observerPos=observerposition, 
                      noise=n, t0=dates_list[0], tn=dates_list[-1])

        if c == "TCPBandwidth" or c == "UDPBandwidth":
            filename = basefilename + "-noise" + n + "_" + str(segment[0]) + "-" + str(segment[1]) + "_" \
                     + observerposition
            temp_mapping = {"typeofmeasure": "active", "command":c, "direction":d, "access-technology":at, 
                            "senderIdentity":segment[0], "receiverIdentity": segment[1], 
                            "ObserverPos":observerposition, "noise":n}
        elif c == "TCPRTT" or c == "UDPRTT":
            filename = basefilename + "-noise" + n + "_" + str(segment[0]) + "_" + observerposition
            temp_mapping = {"typeofmeasure": "active", "command":c, "direction":d, "access-technology":at, 
                            "first-endpoint":segment[0], "second-endpoint": "Observer", 
                            "ObserverPos":observerposition, "noise":n}
        else:
            print ("pippo")
            print (c)

        init_logfile(filename + ".log")
        filename += ".txt"
        print (filename)

        dirpath = os.getcwd()
        inputfoldername = os.path.basename(dirpath)
        
        temp_mapping["path"] = inputfoldername + "/" + filename
        
        log.info(filename + " - {" + str(observerposition) + "}\n")
        cursor.execute(testnumber_query) 

        testnumber_list = compute_testnumberList(cursor=cursor, query=testnumber_query)
        



        log.info(q)
        
        with open(filename, "w+") as out:
            cursor.execute(q) 
            
            data = cursor.fetchall()                    
            columns = cursor.description
            row = str(columns[0][0])
            for j in range(1, len(columns)):
                row += ", " + str(columns[j][0])

            log.info(row)          
            log.info("row count = " +  str(cursor.rowcount))

            for i in range(0, len(data)):
                row = data[i]
                timestamp = row[2]
                timestamp = timestamp.strftime(datetime_format).strip()
                senderIPv4Address = row[7]
                receiverIPv4Address = row[8]


                if i != 0:
                    out.write(",")
                    temp_mapping["last_timestamp"] =  timestamp
                else:
                    temp_mapping["first_timestamp"] =  timestamp
                    temp_mapping["last_timestamp"] = timestamp


                if c == "TCPRTT" or c == "UDPRTT":
                    if observerposition == "cloud":
                        assert senderIPv4Address == "131.114.73.2" or receiverIPv4Address == "131.114.73.2"
                    elif observerposition == "edge":
                        assert senderIPv4Address != "131.114.73.2" and receiverIPv4Address != "131.114.73.2"

                    latency = row[12]
                    out.write(timestamp +"_" + str(latency))
                elif c == "TCPBandwidth" or c == "UDPBandwidth":
                    if observerposition == "cloud":
                        if segment[0] == "Observer":
                            assert senderIPv4Address == "131.114.73.2"
                        else:
                            assert receiverIPv4Address == "131.114.73.2"
                    elif observerposition == "edge":
                        if segment[0] == "Observer":
                            assert senderIPv4Address != "131.114.73.2"
                        else:
                            assert receiverIPv4Address != "131.114.73.2"

                    Kbps = float(row[12])
                    Mbps = Kbps/1000

                    out.write(timestamp +"_" + str(Mbps))                    


            out.write("\n")           

        mapping.append(temp_mapping)
    cursor.close()
    return mapping




def generate_activeinputfile(config_parser, mydb, activemapping):
    #active measures (wifi)

    
    direction = ["upstream", "downstream"]
    command_bandwidth = ["TCPBandwidth", "UDPBandwidth"]
    command_rtt = ["TCPRTT", "UDPRTT"]
    accesstech = ["wifi", "lte"]

    
    for at in accesstech:
        #Bandwidth measures
        for c_bandwidth in command_bandwidth:
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

        #RTT measures
        for c_rtt in command_rtt:
            firstSegment = ["Client"]
            secondSegment = ["Server"]

            activemapping = generate_activeinput(config_parser, mydb, activemapping, c_rtt, None, at, 
                                                    segment=firstSegment, observerposition="edge")
            activemapping = generate_activeinput(config_parser, mydb, activemapping, c_rtt, None, at, 
                                                    segment=secondSegment, observerposition="edge")

            activemapping = generate_activeinput(config_parser, mydb, activemapping, c_rtt, None, at, 
                                                    segment=firstSegment, observerposition="cloud")
            activemapping = generate_activeinput(config_parser, mydb, activemapping, c_rtt, None, at, 
                                                    segment=secondSegment, observerposition="cloud")
   

    return activemapping


if __name__ == '__main__':
    #read configuration file
    config_parser = configparser.ConfigParser()
    config_parser.read("experiments.conf")
    
    mydb = connect(config_parser)
    createfolder("passive")
    createfolder("active")

    with open ("mapping.json", "w+") as mapping_file:
        mapping = []

        mapping = generate_activeinputfile(config_parser, mydb, mapping)

        json.dump(mapping, mapping_file, indent=4, sort_keys=False)

        

    mydb.close()