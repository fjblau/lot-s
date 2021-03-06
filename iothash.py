#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3

import hashlib
from crate import client
import datetime
import time
import requests
import sys


headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

def createPayload(keyname, msg):
	headers = {"Content-Type": "application/json", "Accept": "application/json"}
	#msg = "here is the new mac"
	payload  = '{ \
  		"jsonrpc": "2.0", \
  		"method": "invoke", \
  		"params": { \
    	"type": 1, \
    	"chaincodeID": { \
      		"name": "daa32b86da6e52e446e3bb01d272bc12d1d223d8651c3c96ee990af8ea08e33dcc9fdac82539ce17b8e3ce795323e5b7f22d54cb42c42da5d71d67b9cde1cfe4" \
    	}, \
    		"ctorMsg": { \
      		"function": "write", \
      	"args": [ \
        	"' +keyname+ '", "' +msg+ '" \
     		] \
    		}, \
    		"secureContext": "user_type1_34135b9471" \
  		}, \
  	"id": 0 \
	}'
	return payload

#connection = client.connect('http://ec2-52-90-8-106.compute-1.amazonaws.com:4200')
print("Creating crate connection")
connection = client.connect('http://192.168.1.133:4200')
cursor = connection.cursor()
print("crate connection complete")

while True:
	print("Get DB records")
	tranmin = int(datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M')) -1 
	cursor.execute('select strjson from berry where tranmin = ? order by sensordttm', (str(tranmin),))
	data = hashlib.sha256()
	result = 'START'
	print("Hash result")
	while result:
		result = cursor.fetchone()
		data.update(str(result).encode('utf-8'))
	print("create payload")
	payload=createPayload(str(tranmin), data.hexdigest())

	print("submit to ledger")
	try:
		r=requests.post('https://1c1390b2-5da0-4644-ac20-7414429bbb94_vp1.us.blockchain.ibm.com:443/chaincode', headers=headers, data=payload, timeout=8)
		print("Submitted to ledger: "+str(tranmin)+":"+data.hexdigest())
	#time.sleep(1)

	except:
		print("Error")

	#except:
	#	print("Other Error")
		
	time.sleep(5)


