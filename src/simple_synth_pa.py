#! /usr/bin/python3
"""
    Simple synth midi and audio, with Portaudio and mido for midi object
    Date: Sat, 25/09/2021
    Author: Coolbrother
"""

import math
import numpy as np
import pyaudio
import midutils
import itertools
import mido
import time

_pi = math.pi
_rate = 44100
_channels =1
_blocksize =1024
_amp =1
hz = midutils.note2freq
mid2freq = midutils.mid2freq

# """
stream = pyaudio.PyAudio().open(
            rate=44100,
            channels=1,
            format=pyaudio.paInt16,
            output=True,
            frames_per_buffer=512
            )
# """

def get_sine_osc(freq=55,  amp=1, rate=44100):
    incr = (2 * _pi * freq) / rate
    return (math.sin(v) * amp for v in itertools.count(start=0, step=incr))

#-------------------------------------------

def get_samples(notes_dic, num_samples=256):
    return [sum( [int(next(osc) * 32767) \
            for _, osc in notes_dic.items()]) \
            for _ in range(num_samples)]

#-------------------------------------------

def play(samp):
    samp = np.int16(samp).tobytes()
    stream.write(samp)
    pass

#-------------------------------------------

def stop():
    sream.stop()

#-------------------------------------------

def receive_from(port=0):
    """
    Get incoming messages - nonblocking interface
    with cb_func as callback
    """

    portname = ""
    inputnames = mido.get_input_names()
    try:
        portname = inputnames[port]
    except IndexError:
        print("Error: Midi Port {} is not available".format(port))
    
    if portname:
        print("inportname: ",portname)
        inport = mido.open_input(portname)
        
        """
        while 1:
            msg = inport.receive()
            print("voici: ", msg)
        """

    return inport

#-----------------------------------------


def play_midi():
    midi_input = receive_from(1)
    
    try:
        notes_dic = {}
        while True:
            if notes_dic:
                # play the notes
                
                samp = get_samples(notes_dic, num_samples=_blocksize)
                # print("type: ", type(samp))
                samp = np.int16(samp).tobytes() # for pyaudio module
                stream.write(samp)

            msg = midi_input.poll()
            if msg:
                m_type = msg.type
                # add or remove notes from notes_dic
                # print("msg: ")
                if m_type in ['note_on', 'note_off']:
                    m_note = msg.note
                    m_vel = msg.velocity
                    if m_type == "note_on" and m_vel == 0 and m_note in notes_dic:
                        # print("Note_off: ", msg)
                        del notes_dic[m_note]
                    elif m_type == "note_on" and m_vel >0 and m_note not in notes_dic:
                        # print("Note_on: ", msg)
                        freq = mid2freq(m_note)
                        notes_dic[m_note] = get_sine_osc(freq, amp=m_vel/127)
        
    except KeyboardInterrupt as err:
        print("Stoping...")

#-------------------------------------------

def main():
    _osc = get_sine_osc(freq=440)
    iter(_osc)
    samp = [int(next(_osc) * 32767) for _ in range(44100 * 2)]
    # play(samp)
    play_midi()
    stop()


#-------------------------------------------

if __name__ == "__main__":
    main()
    input("Press Enter...")
