import pycom
pycom.heartbeat(False)
pycom.rgbled(0x110000) 

import machine
from network import WLAN
import utime

print("Init WLAN")
wlan = WLAN(mode=WLAN.STA)
wlan.connect(ssid='LOPY_NETWORK', auth=(WLAN.WPA2, 'LOPYROCKS'))
while not wlan.isconnected():
	utime.sleep_ms(10)

print(wlan.ifconfig())

import socket
s = socket.socket()
print("Connecting...")
s.connect(('192.168.4.1', 70))

while True:
	print("Sending data...")
	s.send(b'1234')
	data = s.recv(4)
	pycom.rgbled(0x000011) # make the LED light up in green color
	utime.sleep_ms(50)
	pycom.rgbled(0x001100)
	utime.sleep_ms(500)
