#! /usr/bin/python3
"""
    Test for continious sound
    Date: Thu, 09/12/2021

    Author: Coolbrother
"""
import midutils as mid
import sounddevice as sd
import math
import itertools
import numpy as np

def gen_sine_osc(freq=55,  amp=1, rate=48000):
    incr = (2 * math.pi * freq) / rate
    return (math.sin(v) * amp for v in itertools.count(start=0, step=incr))

#-------------------------------------------


class SimpleSynth(object):
    def __init__(self, channels=1, rate=48000, blocksize=1024):
        # Constants
        self._channels = channels
        self._rate = rate
        self._blocksize = blocksize
        self.amp_scale = 0.3
        self.max_amp = 0.8
    
    def _init_stream(self):
        # Initialize the Stream object

        self.stream = sd.OutputStream(
            samplerate = self._rate,
            channels = self._channels,
            dtype = 'int16',
            blocksize = self._blocksize,
            )
        self.stream.start()

    #-------------------------------------------

   
    def _get_samples(self, notes_dict):
        # Return samples in int16 format
        samples = []
        for _ in range(self._blocksize):
            samples.append(
                [next(osc) for _, osc in notes_dict.items()]
            )
        samples = np.array(samples).sum(axis=1) * self.amp_scale
        
        samples = np.int16(samples.clip(-self.max_amp, self.max_amp) * 32767)
        return samples.reshape(self._blocksize, -1)

    #-------------------------------------------

    def play(self, osc_func):
        self._init_stream()

        try:
            notes_dic = {}
            while True:
                if notes_dic:
                    # Play the notes
                    samples = self._get_samples(notes_dic)
                    self.stream.write(samples)
                    
                if not notes_dic:
                    # Note On
                    m_note = 69
                    freq = mid.mid2freq(m_note)
                    notes_dic[m_note] = osc_func(freq=freq, amp=1, rate=self._rate)

        except KeyboardInterrupt as err:
            self.stream.close()
           
    #-------------------------------------------

#========================================

if __name__ == "__main__":
    synth = SimpleSynth()
    synth.play(gen_sine_osc)

    #-------------------------------------------
