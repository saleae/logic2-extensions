# This HLA takes a stream of bytes (preferably ascii characters) and combines individual frames into larger frames in an attempt to make text strings easier to read.
# For example, this should make reading serial log messages much easier in the software.
# It supports delimiting on special characters, and after a certain delay is detected between characters.
# It supports the I2C, SPI, and Serial analyzers, although it's most useful for serial port messages.

# Settings constants.
from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting
from saleae.data import GraphTimeDelta

MESSAGE_PREFIX_SETTING = 'Message Prefix (optional)'
PACKET_TIMEOUT_SETTING = 'Packet Timeout [s]'
PACKET_DELIMITER_SETTING = 'Packet Delimiter'

DELIMITER_CHOICES = {
    'New Line [\\n]': '\n',
    'Null [\\0]': '\0',
    'Space [\' \']': ' ',
    'Semicolon [;]': ';',
    'Tab [\\t]': '\t'
}


class TextMessages(HighLevelAnalyzer):

    temp_frame = None
    delimiter = '\n'

    # Settings:
    prefix = StringSetting(label='Message Prefix (optional)')
    packet_timeout = NumberSetting(label='Packet Timeout [s]', min=1E-6, max=1E4)
    delimiter_setting = ChoicesSetting(label='Packet Delimiter', choices=DELIMITER_CHOICES.keys())

    # Base output formatting options:
    result_types = {
        'error': {
            'format': 'Error!'
        },
    }

    def __init__(self):
        self.delimiter = DELIMITER_CHOICES.get(self.delimiter_setting, '\n')
        self.result_types["message"] = {
            'format': self.prefix + '{{data.str}}'
        }

    def clear_stored_message(self, frame):
        self.temp_frame = AnalyzerFrame('message', frame.start_time, frame.end_time, {
            'str': ''
        })

    def append_char(self, char):
        self.temp_frame.data["str"] += char

    def have_existing_message(self):
        if self.temp_frame is None:
            return False
        if len(self.temp_frame.data["str"]) == 0:
            return False
        return True

    def update_end_time(self, frame):
        self.temp_frame.end_time = frame.end_time

    def decode(self, frame: AnalyzerFrame):
        # This class method is called once for each frame produced by the input analyzer.
        # the "data" dictionary contents is specific to the input analyzer type. The readme with this repo contains a description of the "data" contents for each input analyzer type.
        # all frames contain some common keys: start_time, end_time, and type.

        # This function can either return nothing, a single new frame, or an array of new frames.
        # all new frames produced are dictionaries and need to have the required keys: start_time, end_time, and type
        # in addition, protocol-specific information should be stored in the "data" key, so that they can be accessed by rendering (using the format strings), by export, by the terminal view, and by the protocol search results list.
        # Not all of these are implemented yet, but we're working on it!

        # All protocols - use the delimiter specified in the settings.
        delimiters = [self.delimiter]  # [ "\0", "\n", "\r", " " ]
        # All protocols - delimit on a delay specified in the settings
        # consider frames further apart than this separate messages
        maximum_delay = GraphTimeDelta(second=self.packet_timeout or 0.5E-3)
        # I2C - delimit on address byte
        # SPI - delimit on Enable toggle. TODO: add support for the SPI analyzer to send Enable/disable frames, or at least a Packet ID to the low level analyzer.

        char = "unknown error."

        # setup initial result, if not present
        first_frame = False
        if self.temp_frame is None:
            first_frame = True
            self.clear_stored_message(frame)

        # handle serial data
        if frame.type == "data" and "value" in frame.data.keys():
            value = frame.data["value"][0]
            char = chr(value)

        # handle I2C address
        if frame.type == "address":
            value = frame.data["address"][0]
            # if we have an existing message, send it
            if self.have_existing_message() == True:
                ret = self.temp_frame
                self.clear_stored_message(frame)
                self.append_char("address: " + hex(value) + ";")
                return ret
            # append the address to the beginning of the new message
            self.append_char("address: " + hex(value) + ";")
            return None

        # handle I2C data byte
        if frame.type == "data" and "data" in frame.data.keys() and type(frame.data) is bytes:
            value = frame.data[0]
            char = chr(value)

        # handle I2C start condition
        if frame.type == "start":
            return

        # handle I2C stop condition
        if frame.type == "stop":
            if self.have_existing_message() == True:
                ret = self.temp_frame
                self.temp_frame = None
                return ret
            self.temp_frame = None
            return

        # handle SPI byte
        if frame.type == "result":
            char = ""
            if "miso" in frame.data.keys() and frame.data["miso"] != 0:
                char += chr(frame.data["miso"])
            if "mosi" in frame.data.keys() and frame.data["mosi"] != 0:
                char += chr(frame.data["mosi"])

        # If we have a timeout event, commit the frame and make sure not to add the new frame after the delay, and add the current character to the next frame.
        if first_frame == False and self.temp_frame is not None:
            if self.temp_frame.end_time + maximum_delay < frame.start_time:
                ret = self.temp_frame
                self.clear_stored_message(frame)
                self.append_char(char)
                return ret

        self.append_char(char)
        self.update_end_time(frame)

        # if the current character is a delimiter, commit it.
        if char in delimiters:
            ret = self.temp_frame
            # leave the temp_frame blank, so the next frame is the beginning of the next message.
            self.temp_frame = None
            return ret
