#! /usr/bin/env python3
"""
    Player for oscillators and itertools
    Date: Thu, 09/09/2021
    Author: Coolbrother
"""
import numpy as np
import math
import itertools
import sounddevice as sd
_pi = math.pi
_rate = 48000
_channels =1
_stream = None
_blocksize = 1024
_amp =1
sd.default.samplerate = _rate

def gen_simple_sine(freq=440, rate=48000):
    increment = (2 * _pi * freq) / rate
    return (math.sin(v) for v in itertools.count(start=0, step=increment))

#-------------------------------------------

def play(samp):
    sd.play(samp)
    sd.wait()

#-------------------------------------------

def stop():
    sd.stop()

#-------------------------------------------

def _init_stream():
    # Initialize the Stream object
    global _stream

    _stream = sd.OutputStream(
        samplerate = _rate,
        channels = _channels,
        dtype = 'int16',
        blocksize = _blocksize,
        )
    _stream.start()

#-------------------------------------------

def close_stream():
    _stream.close()

#-------------------------------------------

def test():
    _init_stream()
    _gen = gen_simple_sine()
    _wavs = [next(_gen) for _ in range(4800)]
    # convert _wavs to int16
    samp = np.array(_wavs) * 32667
    samp = np.int16(samp) 
    while 1:
        # print("dtype: ", samp.dtype, samp.size)
        # print("samp: ", samp)
        _stream.write(samp)
        # sd.play(_wavs, blocking=True)

#-------------------------------------------

def main():
    # play(_wavs)
    test()
    # stop()
    close_stream()

#-------------------------------------------

if __name__ == "__main__":
    main()
    input("Press a key...")
