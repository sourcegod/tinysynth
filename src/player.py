#! /usr/bin/env python3
"""
    Player for oscillators
    Date: Thu, 09/09/2021
    Author: Coolbrother
"""
import numpy as np
from oscillators import (
        SineOscillator,
        SawtoothOscillator,
        SquareOscillator,
        TriangleOscillator,
        )
from wave_adder import WaveAdder
import sounddevice as sd

_rate = 44100
_amp =1
sd.default.samplerate = _rate
#_gen = SineOscillator(freq=440)

"""
_gen = WaveAdder(
        SineOscillator(freq=440),
        SineOscillator(freq=540),
        SineOscillator(freq=640),
        SineOscillator(freq=740),
        )
"""

_gen = WaveAdder(
    SineOscillator(freq=440),
    TriangleOscillator(freq=220, amp=0.8),
    SawtoothOscillator(freq=110, amp=0.6),
    SquareOscillator(freq=55, amp=0.4),
    )

iter(_gen)
_wavs = [next(_gen) for _ in range(44100 * 5)] # 5 seconds
# _wavs = np.array(_wavs)
# _wavs = np.int16(_wavs * _amp * (2**15 - 1))

def play(samp):
    sd.play(samp)
    sd.wait()

#-------------------------------------------

def stop():
    sd.stop()

#-------------------------------------------

def main():
    play(_wavs)
    stop()

#-------------------------------------------

if __name__ == "__main__":
    main()
    input("Press a key...")
