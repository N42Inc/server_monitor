import os
import pprint
import subprocess
import sys
import re
import json
import potsdb,sys,linecache,time,math
from string import rstrip
tsdbIp="52.8.104.253"
tsdbPort=4343
interval=1
hostname = os.uname()[1]
import urllib2
response = urllib2.urlopen("http://169.254.169.254/latest/meta-data/ami-id")
instanceid = response.read()
in_statictics = {}

'''
root@ubuntu:~# cat /proc/net/dev
Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
  eth0: 140792077  239476    0    0    0     0          0         0 145515280  146321    0    0    0     0       0          0
docker0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
  eth1:  144464     854    0    0    0     0          0         0     5754      32    0    0    0     0       0          0
    lo: 8933788   35373    0    0    0     0          0         0  8933788   35373    0    0    0     0       0          0
'''
def proc_net_dev_parse(parse_this):
        interfaces_dict = {}
        for line in parse_this :
                if re.search('Receive|packets|qvb|qvo|qbr|ovs-system|br-tun|br-int|lo|veth|docker|flannel|virbr', line) or  line == "":
                        continue
                line = line.strip()
                data = line.split(":")
                interface = data[0]
                in_data = data[1].strip().split()
                interfaces_dict[interface]={'rbytes':in_data[0],'rerrs':in_data[2],'rdrop':in_data[3],'tbytes':in_data[8],'terrs':in_data[10],'tdrop':in_data[11]}
        return interfaces_dict


def difference(list_1,list_2):
        global in_statictics
        for k,v in list_1.iteritems():
                in_statictics[k] = {'rbytes':(int(list_2[k]['rbytes']) - int(list_1[k]['rbytes']))/3,'rerrs':(int(list_2[k]['rerrs']) - int(list_1[k]['rerrs']))/3,'rdrop':(int(list_2[k]['rdrop']) - int(list_1[k]['rdrop']))/3,'tbytes':(int(list_2[k]['tbytes']) - int(list_1[k]['tbytes']))/3,'terrs':(int(list_2[k]['terrs']) - int(list_1[k]['terrs']))/3,'tdrop':(int(list_2[k]['tdrop']) - int(list_1[k]['tdrop']))/3}
        return  in_statictics
def calculate(Bytes):
        d = {}
        return {'v':float(Bytes)/(2**10),'type':"kB/s"}

def transferrate():
        global in_statictics
        for k,v in in_statictics.iteritems():
                r1 = calculate(v['rbytes'])
                t1 = calculate(v['tbytes'])
                in_statictics[k]['rrate'] = r1['v']
                in_statictics[k]['trate'] = t1['v']#str(t1['v']) +" "+ t1['type']

def ethtool_parse(parse_this):
        v = 0
        for line in parse_this :
                if re.search('Speed', line):
                        value = line.split(":")[1]
                        value = value.strip()
                        if re.search('M', value):
                                v = int(value.split("M")[0])*(2**20)
                else :
                        continue
        return v
def utilization():
        global in_statictics
        speed = {}
        for k,v in in_statictics.iteritems():
                s = "ethtool "+k
                speed_parse = subprocess.check_output(s,shell=True).split('\n');
                speed[k]=ethtool_parse(speed_parse)
                if speed[k] != 0:
                        in_util = (float(in_statictics[k]['rbytes']*100))/speed[k]
                        out_util = (float(in_statictics[k]['tbytes']*100))/speed[k]
                        in_statictics[k]['rutil'] = round(in_util,4)
                        in_statictics[k]['tutil'] = round(out_util,4)


def main():
        interfaes_statictics_list_first = subprocess.check_output("cat /proc/net/dev",shell=True).split('\n');
        first = proc_net_dev_parse(interfaes_statictics_list_first)
        subprocess.check_output("sleep 3",shell=True)
        interfaes_statictics_list_second = subprocess.check_output("cat /proc/net/dev",shell=True).split('\n');
        second = proc_net_dev_parse(interfaes_statictics_list_second)
        difference(first,second)
        transferrate()
        utilization()
        if_metrics = {'rbytes':'system.net.bytes_rcvd','tbytes':'system.net.bytes_send','rutil':'system.net.in_util','tutil':'system.net.out_util','rrate':'system.net.received_rate','trate':'system.net.transmit_rate','rerrs':'system.net.packets_in.error','terrs':'system.net.packets_out.error','rdrop':'system.net.packets_in.drops','tdrop':'system.net.packets_out.drops'}
        #print if_metrics,if_metrics['rbytes'],if_metrics["rbytes"]
        try:
        #tsdb
                metrics = potsdb.Client(tsdbIp, port=tsdbPort,qsize=1000, host_tag=True, mps=100, check_host=True)
                for k,v in in_statictics.iteritems():
                        for k1,v1 in v.iteritems():
                                metrics.send(if_metrics[k1],v1,interface=k,host=hostname,instanceid=instanceid)
                                print if_metrics[k1],v1,"interface=",k,"host="+hostname,"instanceid"+instanceid
                metrics.wait()
                print "========= drops   packets,error  int,util   %,rate  kB/s ======="
        except Exception ,e :
                print "Exception:",e,"At Line Number {}".format(sys.exc_info()[-1].tb_lineno)



if __name__ == "__main__":
       main()
