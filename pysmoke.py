#!/usr/bin/python

import ConfigParser
import subprocess
import re
import logging
import sys
import os
import socket
import threading
import time
from Queue import Queue
from influxdb import InfluxDBClient

OS = os.name

LOG = logging.getLogger(__name__)
LOG_FILE = "pysmoke.log"
LOG.setLevel(logging.DEBUG)

handler = logging.FileHandler(LOG_FILE)
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s -'
                              ' %(levelname)s - %(message)s')
handler.setFormatter(formatter)
LOG.addHandler(handler)

def load_config():
    try:
        config = ConfigParser.ConfigParser()
        config.read('pysmoke.conf')
        ipList = re.split('; |;|, |,|\*|\n|\ ', config.get('default', 'ipList'))
        for i in range(len(ipList)):
            ipList[i] = ipList[i].strip()
        host_influx = config.get('influx_db', 'Host')
        port_influx = config.get('influx_db', 'Port')
        db_influx = config.get('influx_db', 'Database')
        user_influx = config.get('influx_db', 'User')
        pass_influx = config.get('influx_db', 'Pass')        
        all_config = {'list_IP': ipList, 'host_influx': host_influx,
                    'port_influx': port_influx, 'db_influx': db_influx,
                    'user_influx': user_influx, 'pass_influx': pass_influx}
        return all_config
    except Exception as io:
        LOG.error('Your config is wrong: ' + str(io))
        sys.exit(1)

def doping(ip):
    try:
        if OS == 'nt':
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            source = s.getsockname()[0]
            s.close()
            rtt = re.compile(r'Average = (.*)ms')
            loss = re.compile(r'Lost = d{1,5} \((.*)% loss\)')
            process = subprocess.Popen(['ping', '-n', '5', ip],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
            respone = process.stdout.read()
            rta = rtt.search(respone).group(1)
            loss_packet = loss.search(respone).group(1)
        else:
            gw = os.popen("ip -4 route show default").read().split()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((gw[2], 0))
            source = s.getsockname()[0]
            s.close()
            rtt = re.compile(r'rtt min/avg/max/mdev = (.*)/(.*)/(.*)/(.*) ms')
            loss = re.compile(r'(\d{1,3})% packet loss')
            process = subprocess.Popen(['ping', '-c', '5', '-i', '0.2', ip],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
            respone = process.stdout.read()
            rta = rtt.search(respone).group(2)
            loss_packet = loss.search(respone).group(1)
        result_ping = {'Source': source + '-' + socket.gethostname(),
                       'Host': ip, 'RTA': rta, '%Loss': loss_packet}
        return result_ping
    except Exception as e:
        LOG.error('Error occurred: ' + str(e))
        rta = 0
        loss_packet = 0
        result_ping = {'Source': source + '-' + socket.gethostname(),
                       'Host': ip, 'RTA': rta, '%Loss': loss_packet}
        return result_ping

def push_data_to_influx(result_ping, host_influx, port_influx,
                        db_influx, user_influx, pass_influx):
    try:
        connect = InfluxDBClient(host = host_influx,
                                port = port_influx,
                                database = db_influx,
                                username = user_influx,
                                password = pass_influx)
    except Exception as e:
        LOG.error('Error occurred: ' + str(e))
        sys.exit(1)
    json_body = [
        {
            "measurement": "result_ping",
            "tags": {
                "Source": result_ping['Source'],
                "Host": result_ping['Host']
            },
            "fields": {
                "RTA": float(result_ping['RTA']),
                "%Loss": float(result_ping['%Loss'])
            }
        }
    ]
    connect.write_points(json_body)

def worker(queue, host_influx, port_influx,
           db_influx, user_influx, pass_influx):
    while True:
        ip = queue.get()
        result_ping = doping(ip)
        push_data_to_influx(result_ping, host_influx, port_influx,
                            db_influx, user_influx, pass_influx)
        queue.task_done()

def main():
    config = load_config()
    list_ip = config['list_IP']
    host_influx = config['host_influx']
    port_influx = config['port_influx']
    db_influx = config['db_influx']
    user_influx = config['user_influx']
    pass_influx = config['pass_influx']
    queue = Queue(maxsize = 0)
    num_threads = 4
    for i in range(num_threads):
        w = threading.Thread(target=worker, args=(queue, host_influx,
                                                  port_influx, db_influx,
                                                  user_influx, pass_influx,))
        w.setDaemon(True)
        w.start()
    for i in list_ip:
        queue.put(i)
    queue.join()

if __name__ == '__main__':
    main()
