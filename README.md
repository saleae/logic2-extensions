# Logic 2 Examples

## High Level Protocol Analyzers

Saleae High Level Analyzers (HLAs) allow you to write python code that processes a stream of protocol frames, and produces a new stream of protocol frames.

### Example Projects

  - [Gyroscope HLA](./hla_gyroscope)
  - [Simple HLA](./hla_simple_example)


*HLAs require the Saleae Logic software version 2.2.6 or newer.*

*The High Level Analyzer API is likely to change dramatically over the next few months. Always check for updated samples and documentation at [discuss.saleae.com](https://discuss.saleae.com/).*

HLAs require two files, an `extension.json` file, and a python source file.

the `extension.json` file looks like so, and can include one or more HLAs.

```json
{
    "version": "0.0.1",
    "apiVersion": "1.0.0",
    "author": "Mark \"cool guy\" Garrison",
    "name": "Marks Utilities",
    "extensions": {
        "Fancy I2C": {
            "type": "HighLevelAnalyzer",
            "entryPoint": "util.I2cHla"
        },
        "Text Messages": {
            "type": "HighLevelAnalyzer",
            "entryPoint": "util.TextMessages"
        }
    }
}
```

The "extensions" object should contain one key for each HLA class you would like to write. the "entryPoint" key contains the python file name, a dot, and the python class name, allowing you to write multiple HLAs in a single python file, or separate python files. (i.e. `"fileName.className"`)

To write a HLA, you need to provide a single python class which implements these methods:

```py
class Hla():
  def __init__(self):
    pass

  def get_capabilities(self):
    pass

  def set_settings(self, settings):
    pass

  def decode(self, data):
    return data
```

This example has no settings, and will simply copy the frames from the input analyzer to the output. It also provides no display template, so the default display template will be used.

`def get_capabilities(self):` isn't used yet, but will eventually support exposing selectable settings to the user.

`def set_settings(self, settings):` will eventually accept the user's settings, but for now the provided `settings` argument will be an empty object.

`def set_settings(self, settings):` can also optionally return an object that describes how to format the output frames for display in the software. There should be one entry for every frame "type" your HLA produces.

`def decode(self, data):` is called once for every frame passed to the HLA from the attached analyzer. It can return nothing, a single frame, or an array of frames.

both the input and the output frames share a common shape. The type is always a python dictionary with the following shape.

```py
{
  "type": "error/address/data/start/stop/etc...",
  "start_time": 0.0052,
  "end_time": 0.0076,
  "data": {
    ...
  }
}
```

For output frames, the "type" key is used to locate the correct format string, if formatting strings are provided by the `set_settings` function return value.

"start_time" and "end_time" show the range of time of the frame, in seconds, relative to the start of the recording. (This is still the case even if a trigger is used, these times will not be relative to trigger time zero)

The "data" key can contain any number of keys, and then can be accessed in the custom format string for the given frame type.

Example:

```py
# Format strings
def set_settings(self, settings):
  return {
      "result_types": {
          "error": {
              "format": "Error!"
          },
          "i2c": {
              "format": "address: {{data.address}}; data[{{data.count}}]: [ {{data.data}} ]"
          }
      }
  }
```

```py
# Example frame of type "error":
def decode(self, data):
  return {
    "type": "error",
    "start_time": 0.0052,
    "end_time": 0.0076,
   "data": {}
  }

# Example frame of type "i2c":
def decode(self, data):
  return {
    "type": "i2c",
    "start_time": 0.0052,
    "end_time": 0.0076,
   "data": {
     "address": 17,
      "data": "0x17, 0x23, 0xFA",
      "count": 3
   }
  }
```

## Input Frame Types

At launch, we've included HLA support for our Serial, I2C, and SPI analyzers. All of the other analyzers we include with our application cannot be used with HLAs yet, but we will quickly add support.

### Serial format

```py
{
  "type": "data",
  "start_time": 0.0052,
  "end_time": 0.0076,
  "data": {
    "value": 42,
    "parity_error": False,
    "framing_error": False,
    "address": False, # only used in Serial MP/MDB mode.
  }
}
```

### I2C format

```py
# Start Condition
{
  "type": "start",
  "start_time": 0.0052,
  "end_time": 0.0076,
  "data": {
  }
}
# Stop Condition
{
  "type": "stop",
  "start_time": 0.0052,
  "end_time": 0.0076,
  "data": {
  }
}
# Address Byte
{
  "type": "address",
  "start_time": 0.0052,
  "end_time": 0.0076,
  "data": {
    "address": 42
  }
}
# Data Byte
{
  "type": "data",
  "start_time": 0.0052,
  "end_time": 0.0076,
  "data": {
    "data": 42
  }
}
```

### SPI Format

```py
{
  "type": "result",
  "start_time": 0.0052,
  "end_time": 0.0076,
  "data": {
    "msio": 42,
    "mosi": 42
  }
}
```

## Feedback Welcome!

The HLA API is far from complete. We expect to dramatically expand this in the near future, as well as add support for custom measurements for analog and digital channels. Feedback is welcome. Please direct it to [discuss.saleae.com](https://discuss.saleae.com/).
