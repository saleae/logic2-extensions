gyro_register_map = {
    0x20: 'CTRL_REG1',
    0x21: 'CTRL_REG2',
    0x22: 'CTRL_REG3',
    0x23: 'CTRL_REG4',
    0x24: 'CTRL_REG5',
    0x25: 'REFERENCE',
    0x26: 'OUT_TEMP',
    0x27: 'STATUS_REG',
    0x28: 'OUT_X_L',
    0x29: 'OUT_X_H',
    0x2A: 'OUT_Y_L',
    0x2B: 'OUT_Y_H',
    0x2C: 'OUT_Z_L',
    0x2D: 'OUT_Z_H',
    0x2E: 'FIFO_CTRL_REG',
    0x2F: 'FIFO_SRC_REG',
    0x30: 'INT1_CFG',
    0x31: 'INT1_SRC',
    0x32: 'INT1_TSH_XH',
    0x33: 'INT1_TSH_XL',
    0x34: 'INT1_TSH_YH',
    0x35: 'INT1_TSH_YL',
    0x36: 'INT1_TSH_ZH',
    0x37: 'INT1_TSH_ZL',
    0x38: 'INT1_DURATION',
}


class Transaction:
    is_multibyte_read: bool
    is_read: bool
    start_time: float
    end_time: float
    address: int
    data: bytearray

    def __init__(self, start_time):
        self.start_time = start_time
        self.data = bytearray()
        self.is_multibyte_read = False


class Gyro():
    def __init__(self):
        self.current_transaction = None
        self.last_write_transaction = None

    def get_capabilities(self):
        pass

    def set_settings(self, settings):
        return {
            'result_types': {
                'transaction': {
                    'format': '{{data.angular_rate}}'
                    # 'format': '{{data.registers}}'
                }
            }
        }

    def decode(self, frame):
        type = frame['type']
        if type == 'start':
            self.current_transaction = Transaction(frame['start_time'])
        elif type == 'stop' and self.current_transaction:
            self.current_transaction.end_time = frame['end_time']

            if self.current_transaction.is_read:
                if self.last_write_transaction is None:
                    self.current_transaction = None
                    return

                registers = {}
                register_address = self.last_write_transaction.data[0]
                for byte in self.current_transaction.data:
                    registers[gyro_register_map[register_address]] = byte
                    register_address += 1

                def get_axis(axis):
                    low_register = 'OUT_' + axis + '_L'
                    high_register = 'OUT_' + axis + '_H'
                    if low_register in registers and high_register in registers:
                        low = registers[low_register]
                        high = registers[high_register]
                        value = (high << 8) + low
                        if value >= 32768:
                            value = value - 65536
                        return (float(value) / 32768.0) * 180
                    return None

                angular_rate_str = ''
                for axis in ('X', 'Y', 'Z'):
                    axis_value = get_axis(axis)
                    if axis_value is not None:
                        angular_rate_str += ' ' + axis + ':' + \
                            '{0:.2f}'.format(axis_value)

                register_str = ''
                for name, value in registers.items():
                    register_str += ' ' + name + ':' + str(value)

                new_frame = {
                    'type': 'transaction',
                    'start_time': self.last_write_transaction.start_time,
                    'end_time': self.current_transaction.end_time,
                    'data': {
                        'registers': register_str,
                        'angular_rate': angular_rate_str,
                    }
                }

                self.current_transaction = None

                return new_frame
            else:
                self.last_write_transaction = self.current_transaction

        if self.current_transaction is not None:
            if type == 'address':
                address = frame['data']['address'][0]
                self.current_transaction.address = address
                self.current_transaction.is_read = (address & 0x01) == 1
            elif type == 'data':
                byte = frame['data']['data'][0]
                if not self.current_transaction.is_read and len(self.current_transaction.data) == 0:
                    self.current_transaction.is_multibyte_read = (
                        byte & 0x80) != 0

                    # Remove upper bit
                    byte = byte & 0x7F

                self.current_transaction.data.append(byte)
