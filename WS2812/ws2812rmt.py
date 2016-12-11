from esp32 import esp32
import machine
import uctypes
import utime
import pycom

RMT_BASE = 0x3ff56000

rmtConfiguration = uctypes.struct(RMT_BASE+0x20, (uctypes.ARRAY | 0, 8, {
        "mem_pd": uctypes.BFUINT32 | 0 | 30<<uctypes.BF_POS | 1<<uctypes.BF_LEN, 
        "carrier_out_lv": uctypes.BFUINT32 | 0 | 29<<uctypes.BF_POS | 1<<uctypes.BF_LEN,
        "carrier_en": uctypes.BFUINT32 | 0 | 28<<uctypes.BF_POS | 1<<uctypes.BF_LEN,
        "mem_size": uctypes.BFUINT32 | 0 | 24<<uctypes.BF_POS | 4<<uctypes.BF_LEN,
        "idle_thres": uctypes.BFUINT32 | 0 | 8<<uctypes.BF_POS  | 16<<uctypes.BF_LEN,
        "div_cnt": uctypes.BFUINT32 | 0 | 0<<uctypes.BF_POS  | 8<<uctypes.BF_LEN,
        "idle_out_en": uctypes.BFUINT32 | 4 | 19<<uctypes.BF_POS | 1<<uctypes.BF_LEN,
        "idle_out_lv": uctypes.BFUINT32 | 4 | 18<<uctypes.BF_POS | 1<<uctypes.BF_LEN,
        "ref_always_on": uctypes.BFUINT32 | 4 | 17<<uctypes.BF_POS | 1<<uctypes.BF_LEN,
        "ref_cnt_rst": uctypes.BFUINT32 | 4 | 16<<uctypes.BF_POS | 1<<uctypes.BF_LEN,
        "rx_filter_thres": uctypes.BFUINT32 | 4 | 8<<uctypes.BF_POS  | 8<<uctypes.BF_LEN,
        "rx_filter_en": uctypes.BFUINT32 | 4 | 7<<uctypes.BF_POS  | 1<<uctypes.BF_LEN,
        "tx_conti_mode": uctypes.BFUINT32 | 4 | 6<<uctypes.BF_POS  | 1<<uctypes.BF_LEN,
        "mem_owner": uctypes.BFUINT32 | 4 | 5<<uctypes.BF_POS  | 1<<uctypes.BF_LEN,
        "mem_rd_rst": uctypes.BFUINT32 | 4 | 3<<uctypes.BF_POS  | 1<<uctypes.BF_LEN,
        "mem_wr_rst": uctypes.BFUINT32 | 4 | 2<<uctypes.BF_POS  | 1<<uctypes.BF_LEN,
        "rx_en": uctypes.BFUINT32 | 4 | 1<<uctypes.BF_POS  | 1<<uctypes.BF_LEN,
        "tx_start": uctypes.BFUINT32 | 4 | 0<<uctypes.BF_POS  | 1<<uctypes.BF_LEN
    }))

carrier_duty = uctypes.struct(RMT_BASE + 0xb0, (uctypes.ARRAY | 0, 8, {
        "low": uctypes.BFUINT32 | 0 |  0<<uctypes.BF_POS | 16<<uctypes.BF_LEN,
        "high": uctypes.BFUINT32 | 0 | 16<<uctypes.BF_POS | 16<<uctypes.BF_LEN
    }))

apb_conf = uctypes.struct(RMT_BASE + 0xf0, {
        'fifo_mask': uctypes.BFUINT32 | 0 | 0<<uctypes.BF_POS | 1<<uctypes.BF_LEN,
        'mem_tx_wrap_en': uctypes.BFUINT32 | 0 | 1<<uctypes.BF_POS | 1<<uctypes.BF_LEN,
    })

# RMT RAM is divided into 8 blocks of 64 words, each holding 2 entries. 
# 1 LED = 3 bytes (Red, Green, Blue)
# 1 transfert = 3 bytes / led + 1 byte (end of transfert)
# In the RMT memory, 1 bit = 1 word 
# 1 word : 32 bits : logical level (1 bit) - duration (15 bits) - logical level (1 bit) - duration (15 bit)
# -> 1 LED -> 24 bits = 24 word
# -> 1 transfert = (24 words * nbled) + 1 word
# Each RMT channel has 64 word of memory, but channels can use the memory of the other channel if needed
rmtRam = uctypes.struct(RMT_BASE+0x800, (uctypes.ARRAY | 0x0, uctypes.UINT32 | 64*8))

# Timings for the generated signal
WS2812_0 = 1<<15 | 4*8<<0  | 0<<31 | 4*17<<16
WS2812_1 = 1<<15 | 4*16<<0 | 0<<31 | 4*9<<16
WS_END   = 0<<15 | 4*20*50<<0 | 0<<31 | 0<<16  # ends transfer

DPORT = uctypes.struct(0x3ff00000, {
        'perip_clk_en': (0x0c0, {'rmt': uctypes.BFUINT32 | 0 | 9<<uctypes.BF_POS | 1<<uctypes.BF_LEN}),
        'perip_rst_en': (0x0c4, {'rmt': uctypes.BFUINT32 | 0 | 9<<uctypes.BF_POS | 1<<uctypes.BF_LEN}),
    })

class WS2812RMT:
    def __init__(self, channel = 0):
        self.channel = channel
        self.ram = uctypes.struct(RMT_BASE+0x800, (uctypes.ARRAY | 0x0, uctypes.UINT32 | 64*8))
        self._LowLevelInitPin()
        self._LowLevelInitRMT()
        
    def _LowLevelInitPin(self):        
        machine.Pin('P22', machine.Pin.OUT)
        
        # Inputs are 83+ch, outputs are 87+ch
        # P22 = GPIO25 on ESP32
        esp32.GPIO.func_out_sel_cfg[25].func = 87 + self.channel
            
    def _LowLevelInitRMT(self):       
        DPORT.perip_rst_en.rmt = 1
        DPORT.perip_clk_en.rmt = 1
        DPORT.perip_rst_en.rmt = 0
        
        rmtConfiguration[self.channel].rx_en = 0
        rmtConfiguration[self.channel].mem_rd_rst = 1
        rmtConfiguration[self.channel].mem_owner = 0
        rmtConfiguration[self.channel].tx_conti_mode = 0 # if 1, the transmission will loop
        rmtConfiguration[self.channel].ref_always_on = 1 # use 80MHz clock
        rmtConfiguration[self.channel].idle_out_lv = 0
        rmtConfiguration[self.channel].div_cnt = 1 # divider. could go as high as 4
        rmtConfiguration[self.channel].mem_size = 8 # Use all (8) memory block available
        rmtConfiguration[self.channel].carrier_en = 0
        rmtConfiguration[self.channel].mem_pd = 0
        
    def Display(self,  data):
        base = self.channel * 64
        apb_conf.fifo_mask = 1	# If 0, RAM access is in FIFO mode
        for red,  green,  blue in data:
            for i in range(8):
                rmtRam[base   +i] = WS2812_1 if green&(0x80>>i) else WS2812_0
                rmtRam[base+ 8+i] = WS2812_1 if red&(0x80>>i) else WS2812_0
                rmtRam[base+16+i] = WS2812_1 if blue&(0x80>>i) else WS2812_0            
            base = base + 3*8
        rmtRam[base] = WS_END
        rmtConfiguration[self.channel].mem_rd_rst = 1
        rmtConfiguration[self.channel].mem_owner = 0
        rmtConfiguration[self.channel].tx_start = 1
        
if __name__ == "__main__":
    pycom.heartbeat(False)
    
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
    
    
