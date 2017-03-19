#!/usr/bin/env python

# ############################################################################
# (c) 2017 Wilber Wanjira <wwanjira@cisco.com>
# ############################################################################

#import modules

from pprint import pprint
from pprint import pformat

import json
import requests
import ConfigParser
import io
import sys
import re
import os

# Disable Certificate warning
try:
  requests.packages.urllib3.disable_warnings()
except:
  pass

reload(sys)
sys.setdefaultencoding('utf-8')


##############################################################################
# READ VARIABLES
##############################################################################

config = ConfigParser.ConfigParser()
config.read('iAmAlive_config.cfg')

#apic variables
APIC_URL = config.get("APIC_EM","APIC_URL")
APIC_USER = config.get("APIC_EM","APIC_USER")
APIC_PASSWD = config.get("APIC_EM","APIC_PASSWD")
PROXY = config.get("APIC_EM","PROXY")

# Creates APIC_BASE url based on APIC_URL
APIC_BASE = 'https://%s/api/v1' % APIC_URL

# Makes Proxy Exception if configured 
if PROXY == "No":
  os.environ['no_proxy'] = '%s' % APIC_URL

#tropo variables
TROPO_MSG_TOKEN = config.get("TROPO","TROPO_MSG_TOKEN")
TROPO_CALL_TOKEN = config.get("TROPO","TROPO_CALL_TOKEN")
ADMIN_NAME = config.get("TROPO","ADMIN_NAME")
TROPO_MSG_NUMBER = config.get("TROPO","TROPO_MSG_NUMBER")
TROPO_CALL_NUMBER = config.get("TROPO","TROPO_CALL_NUMBER")

# Creates TROPO url                                         - recheck this 
TROPO_SESSION = 'https://api.tropo.com/1.0/sessions?action=create&token='

##############################################################################
# Start API Session APIC_EM
##############################################################################

apic_credentials = json.dumps({'username':APIC_USER,'password':APIC_PASSWD})
tmp_headers = {'Content-type': 'application/json'}
tmp_get = '%s/ticket' % APIC_BASE
print("Connecting to APIC-EM ..."+'\r\n')
req = requests.post(tmp_get, data=apic_credentials, verify=False, headers=tmp_headers)

# Add session ticket to my http header for subsequent calls
apic_session_ticket = req.json()['response']['serviceTicket']
apic_headers = {'Content-type': 'application/json', 'X-Auth-Token': apic_session_ticket}
print("Connecting to APIC-EM Done" +'\r\n')

# tropo header
tropo_header = {"content-type": "application/json"}

def getHost():
    #global host_list

    url = '%s/host' % APIC_BASE
    req_inv = requests.get(url,verify=False, headers=apic_headers)
    parsed_result = req_inv.json()
    
    #convert data to json format.
    req_list = parsed_result['response']
    
    host_list = []
    i = 0
    for item in req_list:
        i = i + 1
        host_list.append([i,str(item["hostType"]),str(item["hostIp"])])
    return host_list;

##############################################################################
# iAmAlive Checker
##############################################################################

ip = raw_input(" [>] Enter IPv4 host address to check:  ")

if re.match(r'^((\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])$', ip):  
    print "\nValid IPv4\n"  
else:
    print "\nInvalid IPv4... come on! - back to basics bro!...\n"
    quit()
    
##############################################################################
# Checking if this IP is used by a host...
##############################################################################

print "Checking if the HOST is Online...\n"
isOnline = 0
for row in getHost():
    if row[2] == ip:
        isOnline = 1
        break

if isOnline == 1:
    print ("IP address %s is currently used by a host connected via %s\n" % (ip,row[1]))
    
    #trigger an sms to admin via tropo
    payload = {
               "token":TROPO_MSG_TOKEN, "adminName":ADMIN_NAME, "numberToDial":TROPO_MSG_NUMBER, "msg": ip + " is Reachable!"
              }
    
    #Performs a POST to tropo to send an sms to the admin
    response= requests.post(TROPO_SESSION,data=json.dumps(payload))
    
else:
    print ("Dudeeeeeeee! HOST %s is currently offline! .. calling network admin\n" % ip)

    #tropo 
    payload = {
               "token":TROPO_CALL_TOKEN, "adminName":ADMIN_NAME, "numberToDial":TROPO_CALL_NUMBER, "msg": ip + " is Down!, Server is Down!"
              }
    
    #Performs a POST to tropo to send an sms to the admin
    response= requests.post(TROPO_SESSION,data=json.dumps(payload))
    