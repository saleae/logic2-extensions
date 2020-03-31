from math import sqrt

from saleae.range_measurements import DigitalMeasurer

EDGES_RISING = 'edgesRising'
EDGES_FALLING = 'edgesFalling'
# NOTE: currently f_avg = 1/T_avg, which is strictly speaking not the arithmetic mean of the frequency
FREQUENCY_AVG = 'frequencyAvg'
FREQUENCY_MIN = 'frequencyMin'
FREQUENCY_MAX = 'frequencyMax'
PERIOD_STD_DEV = 'periodStdDev'

class ClockStatsMeasurer(DigitalMeasurer):
    supported_measurements = [EDGES_RISING, EDGES_FALLING, FREQUENCY_AVG, PERIOD_STD_DEV, FREQUENCY_MIN, FREQUENCY_MAX]

    def __init__(self, requested_measurements):
        super().__init__(requested_measurements)
        # We always need rising/falling edges
        self.edges_rising = 0
        self.edges_falling = 0
        self.first_transition_type = None
        self.first_transition_time = None
        self.last_transition_of_first_type_time = None

        self.period_min = None
        self.period_max = None
        self.full_period_count = 0
        self.running_mean_period = 0
        self.running_m2_period = 0

    def process_data(self, data):
        for t, bitstate in data:
            if self.first_transition_type is None:
                self.first_transition_type = bitstate
                self.first_transition_time = t
            elif self.first_transition_type == bitstate:
                current_period = t - (self.last_transition_of_first_type_time if self.last_transition_of_first_type_time is not None else self.first_transition_time)
                self.last_transition_of_first_type_time = t

                if self.period_min is None or self.period_min > current_period:
                    self.period_min = current_period
                elif self.period_max is None or self.period_max < current_period:
                    self.period_max = current_period

                # This uses Welford's online algorithm for calculating a variance
                self.full_period_count += 1
                delta = current_period - self.running_mean_period
                self.running_mean_period += delta / self.full_period_count
                delta2 = current_period - self.running_mean_period
                self.running_m2_period += delta * delta2
            if bitstate:
                self.edges_rising += 1
            else:
                self.edges_falling += 1
    
    def measure(self):
        values = {}

        if EDGES_RISING in self.requested_measurements:
            values[EDGES_RISING] = self.edges_rising

        if EDGES_FALLING in self.requested_measurements:
            values[EDGES_FALLING] = self.edges_falling

        if FREQUENCY_AVG in self.requested_measurements:
            if self.first_transition_time is not None and self.last_transition_of_first_type_time is not None:
                # To make the frequency measurement insensitive to exactly where the measurement falls relative to the edge, we only use the
                # sample count of full periods in the range, not the count of samples on the edge.
                #
                # The period count will be the number of transition of the same type as the first transition minus one (fence post problem)
                period_count = (self.edges_rising if self.first_transition_type else self.edges_falling) - 1
                values[FREQUENCY_AVG] = float(period_count) / (self.last_transition_of_first_type_time - self.first_transition_time)

        if FREQUENCY_MIN in self.requested_measurements:
            if self.period_max is not None and self.period_max != 0:
                values[FREQUENCY_MIN] = 1 / self.period_max

        if FREQUENCY_MAX in self.requested_measurements:
            if self.period_min is not None and self.period_min != 0:
                values[FREQUENCY_MAX] = 1 / self.period_min

        if PERIOD_STD_DEV in self.requested_measurements:
            if self.full_period_count > 1:
                period_variance = self.running_m2_period / (self.full_period_count - 1)
                values[PERIOD_STD_DEV] = sqrt(period_variance)

        return values
