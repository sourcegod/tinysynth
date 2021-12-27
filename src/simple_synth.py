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
import time

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
        if osc_func is None:
            # returns blank sample
            return [0] * frame_count
        return [next(osc_func) for _ in range(frame_count)]

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
        self._beat_len = self._block_size * 4 # len of beat tone
        osc1 = gen_sine_osc(freq=880, amp=1, rate=self._rate)
        osc2 = gen_sine_osc(freq=440, amp=1, rate=self._rate)
        self._blank = self._get_zeros(self._block_size)
        self._rest_frames =0
        self._resting =0
        # self._osc_lst = [osc1, None, osc2, None, osc2, None, osc2, None]
        self._osc_lst = [osc1, osc2, osc2, osc2]
        self.set_bpm(bpm)

    #-------------------------------------------

    def reset(self):
        """ reset metronome object """
        self._curpos =0
        self._active =1
        self._osc_index =0
        self._loop_index =0

    #-------------------------------------------


    def set_bpm(self, bpm):
        if bpm <1and bpm > 8000: return
        # bpm =98
        self._tempo = float(self._nb_ticks  / bpm)
        nb_samples = int((self._tempo * self._rate / 1000) ) # for 8 sounds
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
            # if (self._osc_index % 2 == 0) and \
            if self._loop_index * self._block_size >= self._beat_len:
                # blank sample
                osc = None
            else:
                osc = self._osc_lst[self._osc_index]
            
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
        self._dur =0
        self._stop =0
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
        # print(f"frame_count: {frame_count}, _len: {self._len}")
        for _ in range(frame_count):
            if self._curpos >= self._len:
                if self._looping:
                    self._curpos =0
                else: # not looping
                    self._active =0
                    break
            if self._curpos < self._start: val=0
            elif self._stop >0 and self._curpos >= self._stop: val =0
            else: 
                val = next(osc_func)
            
            lst.append(val)
            self._curpos +=1
        
        if not lst: samp = np.zeros((frame_count))
        else: samp = np.array(lst) 
        return samp

    #-------------------------------------------

    def init_params(self, start=0, stop=0, _len=0, pos=0, looping=0):
        self._start = start
        self._stop = stop
        self._len = _len
        self._curpos = pos
        self._looping = looping
        self._active =1

    #-------------------------------------------
     
    def __iter__(self):
        return self

    #-------------------------------------------

    def __next__(self):
        return self._get_frames(self._osc, self._block_size)

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
        self._seq = None
        self._count =0


    #-------------------------------------------

    def get_mixData(self):
        nb_frames = 480 # self._block_size
        timeline = self._timeline
        time_len = timeline.len
        time_pos = timeline.pos
        if time_pos >= time_len:
            # print(f"pos:  {time_pos}, len: {time_len}, count: {self._count}")
            # return np.zeros((nb_frames,), dtype='int16')
            self._seq.reset_all()
            self._count +=1
            # print(f"pos: {timeline.pos}, count: {self._count}")
        
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
# dont forget to the real object to update timeline
        timeline.set_pos(timeline.pos + nb_frames)
# next(track) returns an array of samples, equivalent to track.get_next method
        samp_lst = [next(track) for track in self._track_lst if track.is_active()]
        samp = np.sum(samp_lst, axis=0) / len(samp_lst)
        # must multiply by 32767 before convert to int16
        samp = np.int16(samp * self._max_int16) # 32767
        # samp = np.int16(samp.clip(-self.max_amp, self.max_amp) * 32767)
        # Sound Device need array shape(-1, channels)
        return samp.reshape(-1, 1)

    #-------------------------------------------
    
    def get_mixTracks(self):
        return self._track_lst

    #-------------------------------------------

    def set_mixTracks(self, track_lst):
        self._track_lst = track_lst

    #-------------------------------------------

    def add_mixTrack(self, track):
        self._track_lst.append(track)

    #-------------------------------------------
     
#========================================

class SimpleSynth(object):
    def __init__(self, channels=1, rate=48000, blocksize=960):
        # Constants
        self._channels = channels
        self._rate = rate
        self._blocksize = blocksize
        self.amp_scale = 0.3
        self._stream = None
        self.max_amp = 0.8
        self._mix = Mixer()
        self._timeline = TimeLine()
        self._mix._timeline = self._timeline
        self._mix._seq = self

        self._running = True
        self._start_time =0


    #-------------------------------------------
    
    def get_devInfo(self):
        dev = sd.default.device
        info = sd.query_devices(dev)
        self.print_info(f"Device info:\n {info}")
        info = sd.query_hostapis()
        self.print_info(f"Device info:\n {info}")



    #-------------------------------------------

    def _init_stream(self):
        # Initialize the Stream object

        self._stream = sd.OutputStream(
            samplerate = self._rate,
            channels = self._channels,
            dtype = 'int16',
            blocksize = self._blocksize,
            )
        self._stream.start()

    #-------------------------------------------

    def _init_streamCback(self):
        """
        Initialize the Stream callback object
        """


        stream = sd.OutputStream(
            samplerate = self._rate,
            channels = self._channels,
            dtype = 'int16',
            blocksize = self._blocksize,
            callback=self._func_callback
            )

        return stream

    #-------------------------------------------
    
    def _func_callback(self, outdata, frame_count, time_t, status):
        """ callback function for output stream """
        # print(f"frame_count: {frame_count}")
        # print(f"status: {status}, {time_t.outputBufferDacTime}")
        samp = self._mix.get_mixData()
        outdata[:] = samp
        # self.get_timeFrames(samp)
        

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
        self._stream.write(samp)

    #-------------------------------------------

    def play(self):
        self._running = True
        self._stream = self._init_streamCback()
        self._total_frames =0
        self._count =0
        self.init_time()
        try:
            self._stream.start()
        except KeyboardInterrupt as err:
            self.stop()
    
    #-------------------------------------------
    

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()

    #-------------------------------------------

    def init_synth(self, bpm):
        self._blocksize = 480
        met = Metronome(self._rate, self._blocksize, bpm)
        freq = 220
        osc1  = SimpleOsc(freq, self._rate, self._blocksize)
        freq = 365
        osc2  = SimpleOsc(freq, self._rate, self._blocksize)
        freq = 880
        osc3  = SimpleOsc(freq, self._rate, self._blocksize)
        freq =  1760
        osc4  = PartOsc(freq, self._rate, self._blocksize)
        start = 200 * self._blocksize
        _len =  start *2 # 192000
        self._timeline.len = _len
        osc4.init_params(start=start, _len=_len, pos=0, looping=1)
        self._track_lst = [met, osc1, osc2, osc3, osc4]
        self._mix.set_mixTracks(self._track_lst)
        self._running = False

    #-------------------------------------------

    def init_time(self):
        self._start_time = time.time()

    #-------------------------------------------

    def get_timing(self):
        return time.time() - self._start_time

    #-------------------------------------------

    def get_timeFrames(self, samp):
        # """
        self._total_frames += samp.size
        self._count +=1
        if self._total_frames >= 192000:
            elapsed_time = self.get_timing()
            print(f"Elapsed time: {elapsed_time:0.3f}, in frames: {self._total_frames}, in {self._count} count")
            time.sleep(4)
            self._total_frames =0
            self.init_time()
        # """

    #-------------------------------------------

    def reset_all(self):
        [track.reset() for track in self._mix.get_mixTracks()]
        self._timeline.reset()


    #-------------------------------------------
 
    def get_pos(self):
        """ returns position from Simple Synth object """
        pos = self._timeline.pos
        timing = self.get_timing()
        msg = f"{pos} frames, {timing:0.3f} secs"
        self.print_info(msg)
    #-------------------------------------------

    def add_track(self):
        # self.init_time()
        pos = self._timeline.pos
        freq = 723 # G5
        osc  = PartOsc(freq, self._rate, self._blocksize)
        # start = pos
        # delay compensation
        start = pos - 8 * self._blocksize + 480 # empiric value
        stop = start + 3 * self._blocksize
        _len =   192 * self._blocksize
        osc.init_params(start=start, stop=stop, _len=_len, pos=0, looping=1)
        osc.set_active(0)
        self._mix.add_mixTrack(osc)
        after_pos = self._timeline.pos
        # print(f"timed: {self.get_timing():0.3f}")

        msg = f"Add track at pos: {pos}, after_pos: {after_pos}, start: {start}   frames"
        self.print_info(msg)

    #-------------------------------------------

    def init_tracks(self):
        if len(self._track_lst) >5: 
            self._track_lst = self._track_lst[:5]
            self._mix.set_mixTracks(self._track_lst)
            self.reset_all()

        msg = f"Init tracks frames"
        self.print_info(msg)

    #-------------------------------------------


    def print_info(self, msg):
        print(msg)

    #-------------------------------------------


#========================================

def main():
    synth = SimpleSynth()
    bpm = 120
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
                synth.play()
        elif key == "P":
            synth.reset_all()
        elif key == "s":
            if synth._running:
                synth.stop()
        elif key == "i":
            synth.get_devInfo()
        elif key == "q":
            synth.stop()
            print("Bye!!!")
            break
        elif key == "g":
            synth.get_pos()
        elif key == "a":
            synth.add_track()
        elif key == "d":
            synth.init_tracks()


#-------------------------------------------


if __name__ == "__main__":
    main()

#-------------------------------------------
