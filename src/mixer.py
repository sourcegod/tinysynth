#! /usr/bin/python3
"""
    Simple Synth
    Test for mixer multiple sounds
    Date: Wed, 15/12/2021

    Author: Coolbrother
"""
import sounddevice as sd
import math
import itertools
import numpy as np
import midutils as mid

def gen_sine_osc(freq=55,  amp=1, rate=48000):
    incr = (2 * math.pi * freq) / rate
    return (math.sin(v) * amp for v in itertools.count(start=0, step=incr))

#-------------------------------------------


class BaseObj(object):
    def __init__(self):
        self._rate =0
        self._block_size =0
        self._channels =1
        self.max_amp = 0.8

    #-------------------------------------------

    def _get_zeros(self, frame_count):
        # Return zeros mples in int16 format
        samp = np.zeros((frame_count), dtype='float64')
        return samp # samp.reshape(frame_count, -1)

    #-------------------------------------------
 
    def _get_frames(self, osc_func, frame_count):
        # Return samples in int16 format
        samp = [next(osc_func) for _ in range(frame_count)]
        samp = np.array(samp) 
        # samp = np.int16(samp.clip(-self.max_amp, self.max_amp) * 32767)
        return samp # samples.reshape(frame_count, -1)

    #-------------------------------------------

#========================================

class Metronome(BaseObj):
    def __init__(self, rate=48000, block_size=960, bpm=120):
        # Constants
        self._rate = rate
        self._block_size = block_size
        self.max_amp = 0.8
        self._nb_ticks = 60_000 # in milisec
        self._tempo =0
        self._bpm =1
        self._osc_index =0
        self._loop_index =0
        self._nb_loops =0 
        self._beat_len = self._block_size * 2 # len of beat tone
        osc1 = gen_sine_osc(freq=880, amp=1, rate=self._rate)
        osc2 = gen_sine_osc(freq=440, amp=1, rate=self._rate)
        self._blank = self._get_zeros(self._block_size)
        self._osc_lst = [osc1, None, osc2, None, osc2, None, osc2, None]
        self.set_bpm(bpm)

    #-------------------------------------------
  
    def set_bpm(self, bpm):
        if bpm <1and bpm > 8000: return
        self._tempo = float(self._nb_ticks  / bpm)
        nb_samples = int((self._tempo * self._rate / 1000) / 2) # for 8 sounds
        self._nb_loops = int(nb_samples / self._block_size)
        self._loop_index =0
        self._osc_index =0
        self._bpm = bpm


    #-------------------------------------------

   
    def __iter__(self):
        self._loop_index =0
        self._osc_index =0
        return self

    #-------------------------------------------

    def __next__(self):
        try:
                if (self._osc_index % 2 == 0) and \
                        self._loop_index * self._block_size >= self._beat_len:
                    osc = None
                else:
                    osc = self._osc_lst[self._osc_index]
                
                if self._loop_index +1 < self._nb_loops:
                    self._loop_index +=1
                else:
                    self._loop_index =0
                    if self._osc_index +1 < len(self._osc_lst):
                        self._osc_index +=1
                    else:
                        self._osc_index =0
                
                if osc is None: 
                    samp = self._blank
                else:
                    samp = self._get_frames(osc, self._block_size)
                return samp
        
        except IndexError:
            print("Index Error")
            pass


    #-------------------------------------------

    def get_next(self):
        return self.__next__()

    #-------------------------------------------

#========================================

class SineOsc(BaseObj):
    def __init__(self, freq=440, rate=48000, block_size=960):
        # Constants
        self._rate = rate
        self._block_size = block_size
        self._freq = freq
        self.max_amp = 0.8
        self._osc = gen_sine_osc(freq=self._freq, amp=1, rate=self._rate)

    #-------------------------------------------
  
    def __iter__(self):
        return self

    #-------------------------------------------

    def __next__(self):
        try:
                
            samp = self._get_frames(self._osc, self._block_size)
            return samp
        
        except IndexError:
            print("Index Error")
            pass


    #-------------------------------------------

    def get_next(self):
        return self.__next__()

    #-------------------------------------------

#========================================

class SimpleSynth(object):
    def __init__(self, channels=1, rate=48000, blocksize=960):
        # Constants
        self._channels = channels
        self._rate = rate
        self._blocksize = blocksize
        self.amp_scale = 0.3
        self.max_amp = 0.8
        self._samp_lst = []
    
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

    def _get_frames(self, osc_func, frame_count):
        # Return samples in int16 format
        samples = [next(osc_func) for _ in range(frame_count)]
        samples = np.array(samples)
        samples = np.int16(samples.clip(-self.max_amp, self.max_amp) * 32767)
        return samples # samples.reshape(frame_count, -1)

    #-------------------------------------------

    def _get_zeros(self, frame_count):
        # Return zeros mples in int16 format
        return np.zeros((frame_count), dtype='int16')

    #-------------------------------------------


    def _get_mixData(self):
        samp_lst = [samp.get_next() for samp in self._samp_lst]
        samp = (np.sum(samp_lst, axis=0) / len(samp_lst))
        # must multiply by 32767 before convert to int16
        samp = np.int16(samp * 32767)
        # samp = np.int16(samp.clip(-self.max_amp, self.max_amp) * 32767)
        return samp

    #-------------------------------------------

    def play(self, bpm):
        self._init_stream()
        met = Metronome(self._rate, self._blocksize, bpm)
        freq = 220
        osc1  = SineOsc(freq, self._rate, self._blocksize)
        freq = 365
        osc2  = SineOsc(freq, self._rate, self._blocksize)
        freq = 880
        osc3  = SineOsc(freq, self._rate, self._blocksize)
        self._samp_lst = [met, osc1, osc2, osc3]

        try:
            count =0
            while True:
                samp = self._get_mixData()
                self.stream.write(samp)
                count +=1                
        except KeyboardInterrupt as err:
            self.stream.close()
           
    #-------------------------------------------

#========================================

def main():
    synth = SimpleSynth()
    notes_dic =  {}
    rate = 48000
    osc_func = gen_sine_osc
    # C4, E4, G4, A4, C5, G5, C6
    notes_lst = [60, 64, 67, 69, 72, 79, 84]
    for num in notes_lst:
        freq = mid.mid2freq(num)
        notes_dic[num] = osc_func(freq, amp=0.5, rate=rate)
    bpm = 120
    synth.play(bpm)

#-------------------------------------------


if __name__ == "__main__":
    main()
    #-------------------------------------------
