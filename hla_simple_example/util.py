# This HLA only supports the I2C analyzer results, and will produce a single frame for every transaction. (from start condition to stop condition).
# It demonstrates a custom format string, and how to parse frames produced by the I2C analyzer.


class I2cHla():

    temp_frame = None

    def __init__(self):
        pass

    def get_capabilities(self):
        pass

    def set_settings(self, settings):
        return {
            'result_types': {
                'error': {
                    'format': 'Error!'
                },
                "hi2c": {
                    'format': 'address: {{data.address}}; data[{{data.count}}]: [ {{data.data}} ]'
                }
            }
        }

    def decode(self, data):
        # set our frame to an error frame, which will eventually get over-written as we get data.
        if self.temp_frame is None:
            self.temp_frame = {
                "type": "error",
                "start_time": data["start_time"],
                "end_time": data["end_time"],
                "data": {
                    "address": "error",
                    "data": "",
                    "count": 0
                }
            }

        if data["type"] == "start" or (data["type"] == "address" and self.temp_frame["type"] == "error"):
            self.temp_frame = {
                "type": "hi2c",
                "start_time": data["start_time"],
                "data": {
                    "data": "",
                    "count": 0
                }
            }

        if data["type"] == "address":
            address_byte = data["data"]["address"][0]
            self.temp_frame["data"]["address"] = hex(address_byte)

        if data["type"] == "data":
            data_byte = data["data"]["data"][0]
            self.temp_frame["data"]["count"] += 1
            if len(self.temp_frame["data"]["data"]) > 0:
                self.temp_frame["data"]["data"] += ", "
            self.temp_frame["data"]["data"] += hex(data_byte)

        if data["type"] == "stop":
            self.temp_frame["end_time"] = data["end_time"]
            # "end_time": data["end_time"],
            new_frame = self.temp_frame
            self.temp_frame = None
            return new_frame
