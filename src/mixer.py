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
import threading

#-----------------------------------------


def limit_value(val, min_val=0, max_val=127):
    if val < min_val: return min_val
    if val > max_val: return max_val
    return val

#-----------------------------------------

def gen_sine_osc(freq=55,  amp=1, rate=48000):
    incr = (2 * math.pi * freq) / rate
    return (math.sin(v) * amp for v in itertools.count(start=0, step=incr))

#-------------------------------------------

class MyThread(threading.Thread):
    def __init__(self, sleep_time=0.1):
        """ call base class constructor """
        super().__init__()
        self._stop_event = threading.Event()
        self._sleep_time = sleep_time

    #-------------------------------------------

    def run(self):
        """main control loop"""
        while not self._stop_event.isSet():
            #do work
            print("hi")
            self._stop_event.wait(self._sleep_time)

    #-------------------------------------------

    def join(self, timeout=None):
        """set stop event and join within a given time period"""
        self._stop_event.set()
        super().join(timeout)

    #-------------------------------------------
           
#========================================

"""
    t = MyThread()
    t.start()
    time.sleep(5)
    t.join(1) #wait 1s max
"""


class BaseSynth(object):
    def __init__(self):
        self._rate =0
        self._block_size =0
        self._channels =1
        self.max_amp = 0.8
        self._max_int16 = 32767
        self._active =1
        self._start =0
        self._len =0
        self._curpos =0
        self._looping =0


    #-------------------------------------------

    def _get_zeros(self, frame_count):
        # Return zeros mples in int16 format
        samp = np.zeros((frame_count), dtype='float64')
        return samp # samp.reshape(frame_count, -1)

    #-------------------------------------------
 
    def _get_frames(self, osc_func, frame_count):
        # Return samples in int16 format
        samp = [next(osc_func) for _ in range(frame_count)]
        # samp = np.array(samp) 
        # samp = np.int16(samp.clip(-self.max_amp, self.max_amp) * 32767)
        return samp # samples.reshape(frame_count, -1)

    #-------------------------------------------
    
    def is_active(self):
        return self._active

    #-------------------------------------------

    def set_active(self, active):
        self._active = active

    #-------------------------------------------

    def reset(self):
        self._curpos =0
        self._active =1

    #-------------------------------------------


#========================================

class Metronome(BaseSynth):
    def __init__(self, rate=48000, block_size=960, bpm=120):
        super().__init__()
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
        self._rest_frames =0
        self._resting =0
        self._osc_lst = [osc1, None, osc2, None, osc2, None, osc2, None]
        self.set_bpm(bpm)

    #-------------------------------------------
  
    def set_bpm(self, bpm):
        if bpm <1and bpm > 8000: return
        # bpm =98
        self._tempo = float(self._nb_ticks  / bpm)
        nb_samples = int((self._tempo * self._rate / 1000) / 2) # for 8 sounds
        (self._nb_loops, rest_frames) = divmod(nb_samples, self._block_size)
        print(f"nb_loops: {self._nb_loops}, rest_frames: {rest_frames}")
        self._rest_frames = self._get_zeros(rest_frames)
        # self._nb_loops = 12
        self._loop_index =0
        self._osc_index =0
        self._bpm = bpm


    #-------------------------------------------

   
    def __iter__(self):
        return self

    #-------------------------------------------

    def __next__(self):
        """
        # TODO: recoding this part, for better tick precision
        if self._resting:
            self._resting =0
            print("len rest_frames: ", self._rest_frames.size)
            return self._rest_frames
        """

        try:
            if (self._osc_index % 2 == 0) and \
                    self._loop_index * self._block_size >= self._beat_len:
                osc = None
                # osc = self._osc_lst[self._osc_index]
            else:
                osc = self._osc_lst[self._osc_index]
                # osc = None
            
            if self._loop_index +1 < self._nb_loops:
                self._loop_index +=1
            else:
                self._loop_index =0
                if self._rest_frames.size >0:
                    self._resting =1
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

class SimpleOsc(BaseSynth):
    def __init__(self, freq=440, rate=48000, block_size=960):
        super().__init__()
        # Constants
        self._rate = rate
        self._block_size = block_size
        self._freq = freq
        self.max_amp = 0.8
        self._osc = gen_sine_osc(freq=self._freq, amp=1, rate=self._rate)
        self.curframes =0
        self.maxframes =0

    #-------------------------------------------
  
    def __iter__(self):
        return self

    #-------------------------------------------

    def __next__(self):
        samp = self._get_frames(self._osc, self._block_size)
        return samp

    #-------------------------------------------

    def get_next(self):
        return self.__next__()

    #-------------------------------------------

#========================================

class PartOsc(BaseSynth):
    def __init__(self, freq=440, rate=48000, block_size=960):
        super().__init__()
        # Constants
        self._rate = rate
        self._block_size = block_size
        self._freq = freq
        self.max_amp = 0.8
        self._osc = gen_sine_osc(freq=self._freq, amp=1, rate=self._rate)
        self._start =0
        self._len =0
        self._curpos =0
        self._looping =0

    #-------------------------------------------
  
    def _get_frames(self, osc_func, frame_count):
        """
        Returns samples array
        from PartOsc object
        """
        lst = []
        for _ in range(frame_count):
            if self._curpos >= self._len:
                if self._looping:
                    self._curpos =0
                else: # not looping
                    self._active =0
                    break
            if self._curpos < self._start: val=0
            else: 
                # if self._curpos == self._start: print("curpos: ", self._curpos)
                val = next(osc_func)
            
            lst.append(val)
            self._curpos +=1
        
        if not lst: samp = np.zeros((frame_count))
        else: samp = np.array(lst) 
        return samp

    #-------------------------------------------

    def init_params(self, start=0, _len=0, pos=0, looping=0):
        self._start = start
        self._len = _len
        self._curpos = pos
        self._looping = looping
        self._active =1
        self._active =1

    #-------------------------------------------
     
    def __iter__(self):
        return self

    #-------------------------------------------

    def __next__(self):
        samp = self._get_frames(self._osc, self._block_size)
        return samp

    #-------------------------------------------

#========================================

class TimeLine(object):
    """ TimeLine manager """
    def __init__(self):
        self._start =0
        self._dur =0
        self._stop =0
        self._curpos =0
        self._len =0

    #-----------------------------------------
    
    def get_start(self):
        """
        return TimeLine start
        from TimeLine object
        """

        return self._start
    
    #-----------------------------------------

    def set_start(self, start=0):
        """
        set TimeLine start
        from TimeLine object
        """

        self._start = start
    
    #-----------------------------------------

    def get_dur(self):
        """
        return TimeLine duration
        from TimeLine object
        """

        return self._dur
    
    #-----------------------------------------

    def set_dur(self, dur):
        """
        set TimeLine duration
        from TimeLine object
        """

        self._dur = dur
    
    #-----------------------------------------

    def get_pos(self):
        """
        return TimeLine position
        from TimeLine object
        """

        return self._curpos
    
    #-----------------------------------------

    def set_pos(self, pos):
        """
        set TimeLine position
        from TimeLine object
        """

        # limit pos range
        # pos = limit_value(pos, 0, self._dur)
        if pos <0: pos =0
        elif pos > self._len: pos = self._len
        self._curpos = pos

    #-----------------------------------------

    def get_len(self):
        """
        return TimeLine length
        from TimeLine object
        """

        return self._len
    
    #-----------------------------------------

    def set_len(self, _len):
        """
        set TimeLine length
        from TimeLine object
        """

        self._len = _len

    #-----------------------------------------

    def reset(self):
        """
        reset timeline position
        from TimeLine object
        """

        self._curpos =0

    #-----------------------------------------


    start = property(get_start, set_start)
    dur = property(get_dur, set_dur)
    pos = property(get_pos, set_pos)
    len = property(get_len, set_len)

    #-----------------------------------------

#========================================



class Mixer(BaseSynth):
    def __init__(self, rate=48000, channels=1, block_size=960):
        super().__init__()
        self._rate = rate
        self._channels = channels
        self._block_size = block_size
        self._track_lst = []
        self._timeline = None
        self._count =0


    #-------------------------------------------

    def get_mixData(self):
        nb_frames = self._block_size
        timeline = self._timeline
        time_len = timeline.len
        time_pos = timeline.pos
        if time_pos >= time_len:
            # print(f"pos:  {time_pos}, len: {time_len}, count: {self._count}")
            # return np.zeros((nb_frames,), dtype='int16')
            timeline.reset()
            # self._count +=1
        
        """
        if tim_pos < tim_len:
            finishing =0
            delta = tim_len - tim_pos
            if delta < nb_frames:
                nb_frames = delta
                finishing =1
        else: # tim_pos >= tim_len
            return
        """

        timeline.set_pos(time_pos + nb_frames)
# next(track) returns an array of samples, equivalent to track.get_next method
        samp_lst = [next(track) for track in self._track_lst if track.is_active()]
        samp = np.sum(samp_lst, axis=0) / len(samp_lst)
        # must multiply by 32767 before convert to int16
        samp = np.int16(samp * self._max_int16) # 32767
        # samp = np.int16(samp.clip(-self.max_amp, self.max_amp) * 32767)
        return samp

    #-------------------------------------------
    
    def get_mixTracks(self):
        return self._track_lst

    #-------------------------------------------

    def set_mixTracks(self, track_lst):
        self._track_lst = track_lst

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
        self._mix = Mixer()
        self._timeline = TimeLine()
        self._mix._timeline = self._timeline

        self._running = True

    #-------------------------------------------
    
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

    def write_data(self, samp):
        self.stream.write(samp)

    #-------------------------------------------

    def play(self, bpm):
        self._total_frames =0
        self._init_stream()
        met = Metronome(self._rate, self._blocksize, bpm)
        freq = 220
        osc1  = SimpleOsc(freq, self._rate, self._blocksize)
        freq = 365
        osc2  = SimpleOsc(freq, self._rate, self._blocksize)
        freq = 880
        osc3  = SimpleOsc(freq, self._rate, self._blocksize)
        freq = 1760
        osc4  = PartOsc(freq, self._rate, self._blocksize)
        start = 96 * self._blocksize
        _len = 192 * self._blocksize
        osc4.init_params(start=start, _len=_len, pos=0, looping=1)
        self._mix.set_mixTracks(
                [met, osc1, osc2, osc3, osc4]
                )

        t = threading.currentThread()
        try:
            # while self._running:
            while getattr(t, "do_run", True):
                samp = self._mix.get_mixData()
                self.write_data(samp)
                self._total_frames += samp.size
                # print("total frames: ",  self._total_frames)
                # self.stream.write(samp)
        except KeyboardInterrupt as err:
            self.stop()
    #-------------------------------------------
    

    def stop(self):
        self._running = False
        self.stream.close()

    #-------------------------------------------

    def init_synth(self, bpm):
        self._init_stream()
        met = Metronome(self._rate, self._blocksize, bpm)
        freq = 220
        osc1  = SimpleOsc(freq, self._rate, self._blocksize)
        freq = 365
        osc2  = SimpleOsc(freq, self._rate, self._blocksize)
        freq = 880
        osc3  = SimpleOsc(freq, self._rate, self._blocksize)
        freq = 1760
        osc4  = PartOsc(freq, self._rate, self._blocksize)
        start = 96 * self._blocksize
        _len = 192 * self._blocksize
        self._timeline.len = _len
        osc4.init_params(start=start, _len=_len, pos=0, looping=1)
        freq = 723 # G5
        osc5  = PartOsc(freq, self._rate, self._blocksize)
        start =0
        _len =  3 * self._blocksize
        osc5.init_params(start=start, _len=_len, pos=0, looping=0)
        self._mix.set_mixTracks(
                [met, osc1, osc2, osc3, 
                    osc4, osc5]
                )
        self._running = False

    #-------------------------------------------
 
    def play_thread(self):
        self._total_frames =0
        t = threading.currentThread()
        self._running = True
        try:
            while getattr(t, "do_run", True):
                samp = self._mix.get_mixData()
                self.write_data(samp)
                self._total_frames += samp.size
                # print("total frames: ",  self._total_frames)
        except KeyboardInterrupt as err:
            self.stop()

    #-------------------------------------------

    def stop_thread(self):
        self._running = False

    #-------------------------------------------

    def restart(self):
        [track.reset() for track in self._mix.get_mixTracks()]
        self._timeline.reset()

    #-------------------------------------------
           
#========================================

def main():
    synth = SimpleSynth()
    bpm = 120
    # synth.play(bpm)
    synth.init_synth(bpm)

    valStr = ""
    savStr = ""

    while 1:
        key = ""
        valStr = input("-> ")
        if valStr == '': valStr = savStr
        else: savStr = valStr
        key = valStr
        if valStr == " ":
            key = valStr
        if key == "p":
            if not synth._running:
                thr = threading.Thread(target=synth.play_thread, args=())
                thr.start()
        elif key == "P":
            synth.restart()
        elif key == "s":
            if synth._running:
                thr.do_run = False
                synth.stop_thread()

        elif key == "q":
            thr.do_run = False
            # synth.stop()
            break

#-------------------------------------------


if __name__ == "__main__":
    main()
    #-------------------------------------------
