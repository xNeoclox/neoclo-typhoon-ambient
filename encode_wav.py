#!/usr/bin/env python3
"""Python 3 QPSK WAV encoder for pinned SuperParasites STM32F4 application builds.
48 kHz mono 16-bit, 12 kbps, 6 kHz carrier, 256-byte packets.
Experimental: validates vector table structure, not hardware safety.
"""
import argparse
import math
from pathlib import Path
import wave
import zlib
import numpy as np

SAMPLE_RATE=48000
CARRIER=6000
BIT_RATE=12000
PACKET_SIZE=256
BLOCK_SIZE=16384
APPLICATION_START=0x08008000
FLASH_END=0x08100000
SECTORS={0x08000000,0x08004000,0x08008000,0x0800c000,
         0x08010000,0x08020000,0x08040000,0x08060000,
         0x08080000,0x080a0000,0x080c0000,0x080e0000}

class Encoder:
    def __init__(self, writer):
        self.writer=writer
        self.sample_index=0
        self.ratio=SAMPLE_RATE//BIT_RATE*2
    def modulate(self,symbols):
        symbols=np.asarray(symbols,dtype=np.int16)
        i=np.repeat(2*(symbols%2)-1,self.ratio)
        q=np.repeat(2*(symbols//2)-1,self.ratio)
        t=(np.arange(i.size,dtype=np.float64)+self.sample_index)/SAMPLE_RATE
        self.sample_index+=i.size
        phase=(2.0*math.pi*CARRIER)*t
        signal=(i*np.sin(phase)+q*np.cos(phase))/math.sqrt(2.0)
        samples=np.asarray(np.clip(signal,-1.0,1.0)*32767.0,dtype='<i2')
        self.writer.writeframesraw(samples.tobytes())
    def blank(self,seconds):
        symbols=np.zeros(int(seconds*BIT_RATE/8)*4,dtype=np.int16)
        for start in range(0,len(symbols),2048):
            self.modulate(symbols[start:start+2048])
    def packet(self,payload):
        if len(payload)!=PACKET_SIZE:
            payload+=b'\xff'*(PACKET_SIZE-len(payload))
        crc=zlib.crc32(payload)&0xffffffff
        data=bytes([0]*8+[0x99]*4+[0xcc]*4)+payload+crc.to_bytes(4,'big')
        symbols=np.empty(len(data)*4,dtype=np.uint8)
        for j,shift in enumerate((6,4,2,0)):
            symbols[j::4]=np.frombuffer(data,dtype=np.uint8)>>shift&3
        self.modulate(symbols)
    def encode(self,firmware):
        self.writer.writeframesraw(bytes(SAMPLE_RATE*2))
        self.blank(1.0)
        for start in range(0,len(firmware),BLOCK_SIZE):
            addr=APPLICATION_START+start
            block=firmware[start:start+BLOCK_SIZE].ljust(BLOCK_SIZE,b'\xff')
            for off in range(0,BLOCK_SIZE,PACKET_SIZE):
                self.packet(block[off:off+PACKET_SIZE])
            self.blank(3.5 if addr in SECTORS else 0.2)
        self.blank(5.0)

def convert(input_file,output_file):
    firmware=Path(input_file).read_bytes()
    if len(firmware)<8: raise ValueError('BIN missing STM32 vector table')
    if len(firmware)>FLASH_END-APPLICATION_START:
        raise ValueError('BIN exceeds conservative 1MiB flash limit')
    sp=int.from_bytes(firmware[:4],'little')
    pc=int.from_bytes(firmware[4:8],'little')
    if not (0x10000000<=sp<0x10020000 or 0x20000000<=sp<0x20040000):
        raise ValueError(f'Unexpected first stack pointer: 0x{sp:08x}')
    if not (pc&1) or not (APPLICATION_START<=(pc&~1)<FLASH_END):
        raise ValueError(f'Unexpected thumb entry point: 0x{pc:08x}')
    output_file=Path(output_file)
    output_file.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(output_file),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SAMPLE_RATE)
        Encoder(w).encode(firmware)
    with wave.open(str(output_file),'rb') as w:
        assert w.getnchannels()==1 and w.getsampwidth()==2
        assert w.getframerate()==SAMPLE_RATE and w.getnframes()>SAMPLE_RATE
    print(f'Encoded {len(firmware)} firmware bytes into {output_file} ({output_file.stat().st_size} bytes)')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware')
    parser.add_argument('-o','--output',required=True)
    args=parser.parse_args()
    convert(args.firmware,args.output)
