#! /usr/bin/env python3
"""
    Player for oscillators
    Date: Thu, 09/09/2021
    Author: Coolbrother
"""
import numpy as np
import sounddevice as sd
from oscillators import (
        SineOscillator,
        SawtoothOscillator,
        SquareOscillator,
        TriangleOscillator,
        )
# from wave_adder import WaveAdder
from wave_adder_recode import WaveAdder
from adsr_envelope import ADSREnvelope
from chain import Chain
from panner import Panner
from modulated_volume import ModulatedVolume
from modulated_panner import ModulatedPanner
import midutils
import math
import itertools
import polysynth as pl


_pi = math.pi
_rate = 44100
_channels =1
_buffersize =1024
_amp =1
sd.default.samplerate = _rate
hz = midutils.note2freq
mid2freq = midutils.mid2freq

#_gen = SineOscillator(freq=440)

"""
_gen = WaveAdder(
        SineOscillator(freq=440),
        SineOscillator(freq=540),
        SineOscillator(freq=640),
        SineOscillator(freq=740),
        )
"""

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
"""

"""
_osc = Chain(
    SineOscillator(),
    Panner(r=0.35)
)
iter(_osc)
next(_osc)
print(f"osc.r: {_osc.r}")
"""

"""
_gen = WaveAdder(
    ModulatedOscillator(
        SineOscillator(hz("A2")),
        ADSREnvelope(0.01, 0.1, 0.4),
        amp_mod=amp_mod
    ),
    ModulatedOscillator(
        SineOscillator(hz("A2") + 3),
        ADSREnvelope(0.01, 0.1, 0.4),
        amp_mod=amp_mod
    ),
    Chain(
        ModulatedOscillator(
            TriangleOscillator(hz("C4")),
            ADSREnvelope(0.5),
            amp_mod=amp_mod
        ),
        Panner(0.7)
    ),
    Chain(
        ModulatedOscillator(
            TriangleOscillator(hz("E3")),
            ADSREnvelope(0.5),
            amp_mod=amp_mod
        ),
        Panner(0.3)
    ),
    stereo=True
)
"""
# gen3
"""
_gen = WaveAdder(
    Chain(
        WaveAdder(
            SineOscillator(hz("A2")),
            SineOscillator(hz("C3")), # A2+3
        ),
        ModulatedVolume(
            ADSREnvelope(0.01, 0.1, 0.4),
        )
    ),
    Chain(
        WaveAdder(
            Chain(
                TriangleOscillator(hz("C4")),
                Panner(0.7)
            ),
            Chain(
                TriangleOscillator(hz("E3")),
                Panner(0.3)
                ), stereo=True
        ),
        ModulatedVolume(
            ADSREnvelope(0.5)
        )
    ),
    stereo=True
)
"""

# gen4
# """
_gen = WaveAdder(
    Chain(
        WaveAdder(
            SineOscillator(hz("A2")),
            SineOscillator(hz("C3")), # A2+3
        ),
        ModulatedVolume(
            ADSREnvelope(0.01, 0.1, 0.4),
        )
    ),

    Chain(
        WaveAdder(
                TriangleOscillator(hz("C4")),
                SquareOscillator(hz("G4")),
                # Panner(0.7)
        ),
    ),
    
    ModulatedVolume(
            ADSREnvelope(0.5)
    ),
)
# """


"""
iter(_gen)
_wavs = [next(_gen) for _ in range(44100 * 5)] # 5 seconds
"""


# """
stream = sd.OutputStream(
            samplerate=_rate,
            channels=_channels,
            dtype='int16',
            blocksize=_buffersize,
            clip_off=True,
            )
# """


def get_sine_osc(freq=55,  amp=1, rate=44100):
    incr = (2 * _pi * freq) / rate
    return (math.sin(v) * amp for v in itertools.count(start=0, step=incr))


#-------------------------------------------

def get_samples0(osc):
    # convert float value from (-1, 1) to integer (-32768, 32767)
    return [int(next(osc) * 32767) for i in range(256)]

#-------------------------------------------

def get_samples(notes_dic, num_samples=256):
    return [sum( [int(next(osc) * 32767) \
            for _, osc in notes_dic.items()]) \
            for _ in range(num_samples)]

#-------------------------------------------


def osc_func(freq, amp, sample_rate):
    return iter(
        Chain(
            TriangleOscillator(freq=freq,
                    amp=amp, sample_rate=sample_rate),
            ModulatedPanner(
                SineOscillator(freq/100,
                    phase=90, sample_rate=sample_rate)
            ),
            ModulatedVolume(
                ADSREnvelope(0.01,
                    release_duration=0.001, sample_rate=sample_rate)
            )
        )
    )

#-------------------------------------------

def play(samp):
    sd.play(samp)
    sd.wait()

#-------------------------------------------

def stop():
    sd.stop()

#-------------------------------------------


def play_midi():
    synth = pl.PolySynth()
    synth.play(osc_func=osc_func)

    
    """
    midi_input = midutils.receive_from(1)
    
    try:
        notes_dic = {}
        while True:
            if notes_dic:
                # play the notes
                
                samp = get_samples(notes_dic, num_samples=_buffersize)
                # print("type: ", type(samp))
                samp = np.int16(samp) # for sounddevice module
                stream.write(samp)

            msg = midi_input.poll()
            if msg:
                m_type = msg.type
                # add or remove notes from notes_dic
                # print("msg: ")
                # print("msg: ", msg)
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

    """

#-------------------------------------------

def main():
    stream.start()
    # play(_wavs)
    # play_midi()
    test()
    # stop()

#-------------------------------------------

def test():
    # """
    osc = get_sine_osc(freq=880)
    notes_dic = {69: osc}
    stream.start()
    while True:
        samp = get_samples(notes_dic, 256)
        # samp = np.int16(samp).tobytes() # for pyaudio module
        samp = np.int16(samp) # for sounddevice module
        print("type: ", type(samp))
        stream.write(samp)
        # sd.play(samp, blocking=True)
        # sd.wait()
    # time.sleep(1)
    # """

#-------------------------------------------

if __name__ == "__main__":
    main()
    input("Press a key...")
