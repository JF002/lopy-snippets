import pycom
import utime
from WS2812.ws2812rmt import WS2812RMT

pycom.heartbeat(False)
pycom.rgbled(0x002000)

ws2812 = WS2812RMT(channel = 0)
data = [(255, 102, 0), (127, 21, 0), (63, 10, 0), (31, 5, 0),
    (15, 2, 0), (7, 1, 0), (0, 0, 0), (0,0,0),
    (0, 0, 0), (0, 0, 0), (0, 0, 0), (0,0,0),
    (0, 0, 0), (0, 0, 0), (0, 0, 0), (0,0,0)
]

while True:
    t1 = utime.ticks_ms()
    data = data[1:] + data[0:1]
    ws2812.Display(data)
    t2 = utime.ticks_ms()
    
    utime.sleep_ms(40 - (t2-t1))
    
