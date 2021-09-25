#python

class WaveAdder:
    def __init__(self, *oscillators):
        self.oscillators = oscillators
        self._len = len(oscillators)
    
    def __iter__(self):
        [iter(osc) for osc in self.oscillators]
        return self
    
    def __next__(self):
        return sum(next(osc) for osc in self.oscillators) / self._len