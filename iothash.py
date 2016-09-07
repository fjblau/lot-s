#!/usr/bin/python

import hashlib
from crate import client
import datetime
import time

connection = client.connect('http://192.168.1.135:4200')
cursor = connection.cursor()

while True:

	tranmin = int(datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M')) -1 
	print tranmin
	cursor.execute("select strjson from berry where tranmin = ? order by sensordttm", (str(tranmin),))
	data = hashlib.sha256()
	result = "START"
	while result:
		result = cursor.fetchone()
		data.update(str(result))
	print(data.hexdigest())
	time.sleep(60)
	


