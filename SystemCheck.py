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
'''
root@poweredge-1 vm]# vmstat -w 2 2
procs -----------------------memory---------------------- ---swap-- -----io---- -system-- --------cpu--------
 r  b         swpd         free         buff        cache   si   so    bi    bo   in   cs  us  sy  id  wa  st
 7  0       389528       244096           52      6536180    0    0     7    86    2    6  19  23  58   0   0
 2  0       389528       242092           52      6536248    0    0     0   936 14764 23788  12  31  57   0   0
'''
def vmstat_parse(parse_this):
        vmstat_dict = {}
        line = parse_this[3].strip().split()
        #print line,type(line[0])
        #cpu
        vmstat_dict['system.cpu.numprocesswaiting'] = int(line[0])
	vmstat_dict['system.io.numprocesswaiting'] = int(line[1])
        vmstat_dict['system.cpu.user'] = int(line[12])
        vmstat_dict['system.cpu.system'] = int(line[13])
        vmstat_dict['system.cpu.idle'] =  int(line[14])
        vmstat_dict['system.cpu.iowait'] = int(line[15])
        vmstat_dict['system.cpu.stolen'] = int(line[16])
        vmstat_dict['system.cpu.util'] = vmstat_dict['system.cpu.user'] + vmstat_dict['system.cpu.system']

        #disk
        vmstat_dict['system.disk.blocks.read'] = int(line[8]) #blocks/s
        vmstat_dict['system.disk.blocks.write'] = int(line[9]) #blocks/s

        #memmory
        vmstat_dict['system.mem.swap.in'] = int(line[6]) #si: Amount of memory swapped in from disk (/s).
        vmstat_dict['system.mem.swap.out'] = int(line[7]) #si: Amount of memory swapped in from disk (/s).

        return vmstat_dict

'''
root@ubuntu:~# cat /proc/meminfo
MemTotal:        1008644 kB
'''
def proc_meminfo_parse(parse_this):
        meminfo_dict = {}
        for i in range(len(parse_this)-1) :
                line = parse_this[i]
                line = line.split(":")
                key = line[0]
                value = int(line[1].strip().split()[0])
                #print key,type(key),value,type(value)
                meminfo_dict[key] = value
        return meminfo_dict
'''
ubuntu@stress2:~$ df -m
Filesystem     1M-blocks  Used Available Use% Mounted on
/dev/vda1           2183  1795       269  88% /
none                   1     0         1   0% /sys/fs/cgroup
udev                 241     1       241   1% /dev
'''
def df_parse(parse_this):
   df_dict = {}
   for line in parse_this:
	if re.search('Filesystem',line) or  line == "":
		continue
        line = line.split()
	df_dict[line[0]] = {'Size':float(line[1]),'Used':float(line[2]),'Available':float(line[3]),'Use':float(line[4].split("%")[0]),'Mountedon':line[5]}
   return df_dict



def main():
    try:
        #tsdb
        metrics = potsdb.Client(tsdbIp, port=tsdbPort,qsize=1000, host_tag=True, mps=100, check_host=True)
        #cpu
        vmstat = subprocess.check_output("vmstat -w 2 2",shell=True).split('\n');
        #print vmstat
        vmstat_dict = vmstat_parse(vmstat)
        #print "\nCPU (metrics in %)"
        for k,v in vmstat_dict.iteritems():
                metrics.send(k,v,host=hostname,instanceid=instanceid)
                print k,v,"host="+hostname,"instanceid"+instanceid
        #memory
        meminfo = subprocess.check_output("cat /proc/meminfo",shell=True).split('\n');
                                                                                          
        meminfo_dict = proc_meminfo_parse(meminfo)
        #system.mem.free,buffered(used for file buffers),cached(used as cache memory,),total,shared,usable(sum of free,buffered,cache),used,pct_usable(usable Ram as a fraction of total)
        memfree = meminfo_dict['MemFree']/(2**10) + meminfo_dict['Buffers']/2**10 + meminfo_dict['Cached']/2**10
        memtotal = meminfo_dict['MemTotal']/2**10
        memused = memtotal - memfree
        memutil = (memused*100)/memtotal
	swaptotal = meminfo_dict['SwapTotal']/(2**10)
	swapfree =  meminfo_dict['SwapFree']/(2**10)
        mem_dict = {'system.mem.free':memfree,'system.mem.total':memtotal,'system.mem.used':memused,'system.mem.util':memutil,'system.mem.swap.total':swaptotal,'system.mem.swap.free':swapfree}
        #print "\nMemory (metrics in  MB) \n"
        for k,v in mem_dict.iteritems():
                metrics.send(k,v,host=hostname,instanceid=instanceid)
                print k,v,"host="+hostname,"instanceid"+instanceid
        #disk
        df = subprocess.check_output("df -m",shell=True).split('\n');
        df_dict = df_parse(df)
        #print df_dict
        #print "\n Disk \n"
        for k,v in df_dict.iteritems():
                metrics.send("system.disk.size",v['Size'],host=hostname,device=k,mounton=v['Mountedon'],instanceid=instanceid)
		metrics.send("system.disk.used",v['Used'],host=hostname,device=k,mounton=v['Mountedon'],instanceid=instanceid)
		metrics.send("system.disk.avail",v['Available'],host=hostname,device=k,mounton=v['Mountedon'],instanceid=instanceid)
		metrics.send("system.disk.util",v['Use'],host=hostname,device=k,mounton=v['Mountedon'],instanceid=instanceid)

                print "system.disk.size",v['Size'],"host="+hostname,"device="+k,"mounton="+v['Mountedon'],"instanceid"+instanceid
		print "system.disk.used",v['Used'],"host="+hostname,"device="+k,"mounton="+v['Mountedon'],"instanceid"+instanceid
		print "system.disk.avail",v['Available'],"host="+hostname,"device="+k,"mounton="+v['Mountedon'],"instanceid"+instanceid
		print "system.disk.util",v['Use'],"host="+hostname,"device="+k,"mounton="+v['Mountedon'],"instanceid"+instanceid

        cores = int(subprocess.check_output("nproc --all",shell=True))
        metrics.send("system.cpu.cores",cores,host=hostname,instanceid=instanceid)
        print "system.cpu.cores",cores,"host="+hostname,"instanceid"+instanceid

        metrics.wait()
        #print "==cpu %(except cpu.numprocesswaiting int), disk MB(except disk.utill %) ,mem MB ,disk.blocks.read/write(blocks/s usually 1KB=1 block)====="
    except Exception ,e :
        print "Exception:",e,"At Line Number {}".format(sys.exc_info()[-1].tb_lineno)



if __name__ == "__main__":
       main()
