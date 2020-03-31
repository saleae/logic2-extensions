import math

import numpy

from saleae.range_measurements import AnalogMeasurer

VOLTAGE_RMS = 'voltageRms'

class VoltageStatisticsMeasurer(AnalogMeasurer):
    supported_measurements = [VOLTAGE_RMS]

    def __init__(self, requested_measurements):
        super().__init__(requested_measurements)
        self.voltage_square = None

        if VOLTAGE_RMS in self.requested_measurements:
            self.voltage_square = 0

    def process_data(self, data):
        if self.voltage_square is not None:
            square_sum = numpy.average(numpy.square(data.samples))
            self.voltage_square += (square_sum - self.voltage_square) * (data.sample_count / (self.processed_sample_count + data.sample_count))
    
    def measure(self):
        values = {}

        if self.voltage_square is not None:
            values[VOLTAGE_RMS] = math.sqrt(self.voltage_square)

        return values

