def gen_simple_sine(freq=440, rate=48000):
    increment = (2 * _pi * freq) / rate
    return (math.sin(v) for v in itertools.count(start=0, step=increment))

#-------------------------------------------
