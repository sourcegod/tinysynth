#! /usr/bin/env python3
"""
    Player for oscillators
    Date: Thu, 09/09/2021
    Author: Coolbrother
"""
import numpy as np
from sine_oscillator import SineOscillator

import sounddevice as sd

_rate = 44100
_amp =1
sd.default.samplerate = _rate
_gen = SineOscillator(freq=440)
iter(_gen)
_wavs = [next(_gen) for _ in range(44100 * 2)]
# wavs = np.array(wavs)
# wavs = np.int16(wavs * _amp * (2**15 - 1))
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
