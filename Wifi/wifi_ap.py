import pycom # we need this module to control the LED
pycom.heartbeat(False) # disable the blue blinking
pycom.rgbled(0x001100) # make the LED light up in green color

from network import WLAN
import utime
import socket

print("Init WLAN")
wlan = WLAN(mode=WLAN.AP, ssid='LOPY_NETWORK', auth=(WLAN.WPA2, 'LOPYROCKS'), channel=1, antenna = WLAN.INT_ANT)

s = socket.socket()

print("Bind socket")
s.bind(('192.168.4.1', 70))

print("Listen socket")
s.listen()

print("Accept connection")
t = s.accept()
conn = t[0]
print("Connection received from : " + str([1]))

while True:
	print("Waiting for data...")
	data = conn.recv(4)
	print("Data received : " + str(data))
	conn.send(b'4567')
	pycom.rgbled(0x000011) # make the LED light up in green color
	utime.sleep_ms(50)
	pycom.rgbled(0x001100)
