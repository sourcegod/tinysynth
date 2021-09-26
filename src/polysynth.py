#! /usr/bin/python3
"""
    polysynth module wrapper for midi and audio functions
    Date: Sun, 26/09/2021
    Author: Coolbrother
"""
import midutils as mid
import sounddevice as sd
import math
import itertools
import numpy as np

def get_sine_osc(freq=55,  amp=1, sample_rate=44100):
    incr = (2 * math.pi * freq) / sample_rate
    return (math.sin(v) * amp for v in itertools.count(start=0, step=incr))

#-------------------------------------------


class PolySynth(object):
    def __init__(self, amp_scale=0.3, max_amp=0.8, sample_rate=44100, num_samples=1024):
        # Initialize MIDI
        # midi.init()
        if mid.get_input_count() > 0:
            self.midi_input = mid.receive_from(1)
        else: 
            raise Exception("no midi inputs detected")
        
        # Constants
        self.num_samples = num_samples
        self.sample_rate = sample_rate
        self.amp_scale = amp_scale
        self.max_amp = max_amp
    
    def _init_stream(self, nchannels):
        # Initialize the Stream object

        self.stream = sd.OutputStream(
            samplerate = self.sample_rate,
            channels = nchannels,
            dtype = 'int16',
            blocksize = self.num_samples,
            )
        self.stream.start()

    #-------------------------------------------

   
    def _get_samples(self, notes_dict):
        # Return samples in int16 format
        samples = []
        for _ in range(self.num_samples):
            samples.append(
                [next(osc[0]) for _, osc in notes_dict.items()]
            )
        samples = np.array(samples).sum(axis=1) * self.amp_scale
        
        samples = np.int16(samples.clip(-self.max_amp, self.max_amp) * 32767)
        return samples.reshape(self.num_samples, -1)

    #-------------------------------------------

    def play(self, osc_function=get_sine_osc, close=False):
        # Check for release trigger, number of channels and init Stream
        tempcf = osc_function(1, 1, self.sample_rate)
        has_trigger = hasattr(tempcf, "trigger_release")
        tempsm = self._get_samples({-1: [tempcf, False]})
        nchannels = tempsm.shape[1]
        self._init_stream(nchannels)

        try:
            notes_dic = {}
            while True:
                if notes_dic:
                    # Play the notes
                    samples = self._get_samples(notes_dic)
                    self.stream.write(samples)
                    
                # getting midi messages 
                msg = self.midi_input.poll()
                if msg:
                    m_type = msg.type
                    # add or remove notes from notes_dic
                    # print("msg: ")
                    # print("msg: ", msg)
                    if m_type in ['note_on', 'note_off']:
                        m_note = msg.note
                        m_vel = msg.velocity
                        # Note Off
                        if m_type == "note_on" and m_vel == 0 and m_note in notes_dic:
                            if has_trigger:
                                notes_dic[m_note][0].trigger_release()
                                notes_dic[m_note][1] = True
                            else:
                                del notes_dic[m_note]
                                # print("Note_off: ", msg)
                        
                        # Note On
                        elif m_type == "note_on" and m_vel >0 and m_note not in notes_dic:
                            freq = mid.mid2freq(m_note)
                            notes_dic[m_note] = [
                                osc_function(freq=freq, amp=m_vel/127, 
                                sample_rate=self.sample_rate), 
                                False,
                            ]

                if has_trigger:
                    # Delete notes if ended
                    ended_notes = [k for k,o in notes_dic.items() if o[0].ended and o[1]]
                    for note in ended_notes:
                        del notes_dic[note]
                            
        except KeyboardInterrupt as err:
            self.stream.close()
            if close:
                self.midi_input.close()
            
    #-------------------------------------------

#========================================

if __name__ == "__main__":
    synth = PolySynth()
    synth.play()

