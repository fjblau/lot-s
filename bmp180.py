#!/usr/bin/python

from smbus import SMBus
from time import sleep
from ctypes import c_short
import paho.mqtt.publish as publish
import ssl
import paho.mqtt.client as paho
import json
import os
import datetime
import time

import math
from LSM9DS0 import *

from crate import client
connection = client.connect('http://ec2-52-90-8-106.compute-1.amazonaws.com:4200')
cursor = connection.cursor()

connflag = False
RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
G_GAIN = 0.070  # [deg/s/LSB]  If you change the dps for gyro, you need to update this value accordingly
AA =  0.40      # Complementary filter constant

def writeMAG(register,value):
        bus.write_byte_data(MAG_ADDRESS, register, value)
        return -1

def readMAGx():
        mag_l = bus.read_byte_data(MAG_ADDRESS, OUT_X_L_M)
        mag_h = bus.read_byte_data(MAG_ADDRESS, OUT_X_H_M)
        mag_combined = (mag_l | mag_h <<8)

        return mag_combined  if mag_combined < 32768 else mag_combined - 65536


def readMAGy():
        mag_l = bus.read_byte_data(MAG_ADDRESS, OUT_Y_L_M)
        mag_h = bus.read_byte_data(MAG_ADDRESS, OUT_Y_H_M)
        mag_combined = (mag_l | mag_h <<8)

        return mag_combined  if mag_combined < 32768 else mag_combined - 65536


def readMAGz():
        mag_l = bus.read_byte_data(MAG_ADDRESS, OUT_Z_L_M)
        mag_h = bus.read_byte_data(MAG_ADDRESS, OUT_Z_H_M)
        mag_combined = (mag_l | mag_h <<8)

        return mag_combined  if mag_combined < 32768 else mag_combined - 65536

        
def on_connect(client, userdata, flags, rc):
    global connflag
    connflag = True
    #print("Connection returned result: " + str(rc) )

def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))

#def on_log(client, userdata, level, buf):
    print(msg.topic+" "+str(msg.payload))

mqttc = paho.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
#mqttc.on_log = on_log

awshost = "a24q2yxwlht9nv.iot.us-east-1.amazonaws.com"
awsport = 8883
clientId = "pi001"
thingName = "pi001"
caPath = "aws-iot-rootCA.crt"
certPath = "/home/pi/awsiot/34cae591f8-certificate.pem.crt"
keyPath = "/home/pi/awsiot/34cae591f8-private.pem.key"

mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

mqttc.connect(awshost, awsport, keepalive=60)


addr = 0x77
oversampling = 3        # 0..3

bus = SMBus(1);         # 0 for R-Pi Rev. 1, 1 for Rev. 2

mqttc.loop_start()

while (True):
# return two bytes from data as a signed 16-bit value
    def get_short(data, index):
        return c_short((data[index] << 8) + data[index + 1]).value

# return two bytes from data as an unsigned 16-bit value
    def get_ushort(data, index):
        return (data[index] << 8) + data[index + 1]

    (chip_id, version) = bus.read_i2c_block_data(addr, 0xD0, 2)
#print "Chip Id:", chip_id, "Version:", version

#print
#print "Reading calibration data..."
# Read whole calibration EEPROM data
    cal = bus.read_i2c_block_data(addr, 0xAA, 22)

# Convert byte data to word values
    ac1 = get_short(cal, 0)
    ac2 = get_short(cal, 2)
    ac3 = get_short(cal, 4)
    ac4 = get_ushort(cal, 6)
    ac5 = get_ushort(cal, 8)
    ac6 = get_ushort(cal, 10)
    b1 = get_short(cal, 12)
    b2 = get_short(cal, 14)
    mb = get_short(cal, 16)
    mc = get_short(cal, 18)
    md = get_short(cal, 20)

#print "Starting temperature conversion..."
    bus.write_byte_data(addr, 0xF4, 0x2E)
    sleep(0.005)
    (msb, lsb) = bus.read_i2c_block_data(addr, 0xF6, 2)
    ut = (msb << 8) + lsb

#print "Starting pressure conversion..."
    bus.write_byte_data(addr, 0xF4, 0x34 + (oversampling << 6))
    sleep(0.04)
    (msb, lsb, xsb) = bus.read_i2c_block_data(addr, 0xF6, 3)
    up = ((msb << 16) + (lsb << 8) + xsb) >> (8 - oversampling)

#print "Calculating temperature..."
    x1 = ((ut - ac6) * ac5) >> 15
    x2 = (mc << 11) / (x1 + md)
    b5 = x1 + x2 
    t = (b5 + 8) >> 4

#print "Calculating pressure..."
    b6 = b5 - 4000
    b62 = b6 * b6 >> 12
    x1 = (b2 * b62) >> 11
    x2 = ac2 * b6 >> 11
    x3 = x1 + x2
    b3 = (((ac1 * 4 + x3) << oversampling) + 2) >> 2

    x1 = ac3 * b6 >> 13
    x2 = (b1 * b62) >> 16
    x3 = ((x1 + x2) + 2) >> 2
    b4 = (ac4 * (x3 + 32768)) >> 15
    b7 = (up - b3) * (50000 >> oversampling)

    p = (b7 * 2) / b4
#p = (b7 / b4) * 2

    x1 = (p >> 8) * (p >> 8)
    x1 = (x1 * 3038) >> 16
    x2 = (-7357 * p) >> 16
    p = p + ((x1 + x2 + 3791) >> 4)
 
 #initialise the magnetometer
    writeMAG(CTRL_REG5_XM, 0b11110000) #Temp enable, M data rate = 50Hz
    writeMAG(CTRL_REG6_XM, 0b01100000) #+/-12gauss
    writeMAG(CTRL_REG7_XM, 0b00000000) #Continuous-conversion mode
    
    MAGx = readMAGx()
    MAGy = readMAGy()
    MAGz = readMAGz()
	
    #print ("in Loop")
    if connflag == True:
        data = {}
        statedata = "{\"state\": {\"reported\": {\"BerryIMU\": \"Up\"}}}"
        dt = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S%z')
        dtmin = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M')
        data['timestamp'] = dt
        data['dtmin'] = dtmin
        data['sensorid'] = 'BerryIMU'
        data['temp'] = str(t/10.0)
        data['hPa'] = str(p/100.0)
        data['magX'] = str(MAGx)
        data['magY'] = str(MAGy)
        data['magZ'] = str(MAGz)
        
        data['temptime'] = dt
        json_data = json.dumps(data, sort_keys=True)
        mqttc.publish("$aws/things/pi001/bmp180", str(statedata)+" "+json_data, qos=1)
        
        cursor.execute("""INSERT INTO berry (tranmin, sensordttm, temp, bar, magX, magY, magZ, strJson) VALUES (?,?, ?, ?, ?, ?, ?,?)""",
			(dtmin, dt, str(t/10.0), str(p/100.0), str(MAGx),str(MAGy),str(MAGz), json_data))

        tempreading = t/10.0
        #print("msg sent: temperature " + "%.2f" % tempreading )
    else:
        print("waiting for connection...")
        
    sleep(10) 

#print
#print "Temperature:", t/10.0, "C"
#print "Pressure:", p / 100.0, "hPa"
