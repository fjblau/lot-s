#!/usr/local/bin/python

import hashlib
from crate import client

connection = client.connect('http://192.168.99.100:32769')
cursor = connection.cursor()
cursor.execute("select * from test order by testtime")
recs = cursor.execute("select count(*) from test")
cursor.execute("select * from test order by testtime")
data = hashlib.sha256()
result = "START"
while result:
	data.update(str(result))
	result = cursor.fetchmany(2)
	print(data.hexdigest())
	


