# Logic 2 Examples


## API changelog

Logic 2.2.6

- Very first release of extensions, starting with High Level Analyzers!

Logic 2.2.9

- Added python measurements as a new type of extension
- Added settings support to HLAs.

## High Level Protocol Analyzers

Saleae High Level Analyzers (HLAs) allow you to write python code that processes a stream of protocol frames, and produces a new stream of protocol frames.

### Example Projects

  - [Gyroscope HLA](./hla_gyroscope)
  - [Simple HLA](./hla_simple_example)


*HLAs require the Saleae Logic software version 2.2.6 or newer. HLA settings were introduced in 2.2.9*

## Development Process

Starting a new HLA is easy! First, install and open the latest version of the Logic software. Then, open the new extensions sidebar panel.

From there, click the "+" button in the upper right. This will open the "Create an Extension" dialog. Here you can either create a new extension from a template, or load an existing extension from disk.

To create a high level analyzer, select "HighLevelAnalyzer" from the dropdown, and press "Save As...". This will create a new folder with a basic extension with the name you provide.

This will also load your extension into the software. To see it in action, capture some data that contains protocol data. (Serial, I2C, or SPI).

Then, add the correct analyzer for your data (Serial, I2C, and SPI are supported). Once you've configured the built-in analyzer to decode the raw bytes of your capture, you can add your new HLA. From the same add analyzer menu, now locate your new HLA. It will probably be 4th in the list, right under Serial, I2C, and SPI.

This will open the settings for your HLA. Right now there is only one, the input analyzer. There, you need to select the low-level analyzer you added earlier, Serial, I2C or SPI. Then press finish.

The default HLA template will just copy the frames from the input analyzer to the output. Because it doesn't come with a format string (described below), the bubble text you will see on screen will probably look like this: '{type:"data", data:{value:10,...}}'. This conveniently shows you the data format of the input analyzer that you selected, which you will need to access in your HLA. The data format for your input analyzer is also documented below.

Next, open the *.py file you just created in your [favorite text editor](https://code.visualstudio.com/). Use the documentation below to get started! To reload your HLA, you can simply right-click on the instance on the analyzers sidebar, and select "Reload Source Files". This will cause your python file to be re-loaded and re-run over the captured data.

If an error occurs while running your python code, the error message and stack trace will be displayed in a notification.

We're still working on every part of the HLA system, including the development experience. Keep an eye out for updates!

## Extension File Layout

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

## Python API Documentation

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

`def get_capabilities(self):` this user implemented function exposes user-editable settings through the UI. If the HLA does not expose settings, it should be implemented with `pass`

`def set_settings(self, settings):` this function does two things. First, if user editable settings were made available with `get_capabilities`, then the user selections will be passed here through the `settings` argument

second, `def set_settings(self, settings):` can optionally return an object that describes how to format the output frames for display in the software. There should be one entry for every frame "type" your HLA produces.

Lastly, `def set_settings(self, settings):` is called right before `decode` is passed frames from the input analyzer. Any time the HLA is restarted, for instance if the input analyzer changes, or if the user edits any of the HLA's settings, this function will be called again. You should consider this function a reset for your HLA, and clear out any internal state from the previous run here.

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

## Exposing Settings through the UI

Logic 2.2.9 introduced user editable settings to the API.

First, the `get_capabilities` function can optionally return a dictionary of settings to show the user.

This function is called once when loading the HLA.

There are tree types of settings. "string", "number", and "choices".

"string" is what is sounds like. It shows a text box to the user and allows them to enter a string.

"number" allows the user to enter a floating point number. Optionally, a minimum and maximum can be enforced.

"choices" lets the user select one of a set of items through a drop down menu.

These settings are returned in a dictionary from the `def get_capabilities(self):` function like so:

```py
  def get_capabilities(self):
    return {
      'settings': {
          'First Setting Label': {
              'type': 'string'
          },
          'Another Setting': {
              'type': 'number',
              'minimum': 1E-6,
              'maximum': 1E4
          },
          'Pick one of the following': {
              'type': 'choices',
              'choices': ('Option A', 'Option B')
          }
      }
  }
```

Specifically, the return value is a dictionary with a single key "settings".

The value of "settings" is another dictionary, where each key is the label of a setting entry that will be displayed to the user.

Each entry is a dictionary.

"string" settings should contain a single key, "type", with the value "string"

"number" settings should contain a key, "type", with the value "number", and optionally supports two more keys, "minimum" and "maximum".

"choices" settings should contain a key, "type", with the value "choices", and anther key, "choices", that should contain an array of strings.

Note, there are no indexes or Ids used in the settings system. The string label of the setting is used as the identifier.

In the case of the "choices" type, the selected string entry will be passed back as the selected entry.

Once the user has made there selections, their entries will be passed into the `def set_settings(self, settings):` method.

For example, the "settings" argument in `set_settings` could be:

```py
settings = {
  'First Setting Label': 'this is a string from the UI!',
  'Another Setting': 42,
  'Pick one of the following': 'Option B'
}
```

Here is an example of how to read this in your HLA:

```py
  def set_settings(self, settings):
    if 'First Setting Label' in settings.keys():
      self.setting1 = settings['First Setting Label']
    if 'Another Setting' in settings.keys():
      self.setting2 = settings['Another Setting']
    if 'Pick one of the following' in settings.keys():
      self.setting3 = settings['Pick one of the following']
```

Note - it's highly recommended to first check settings for each key before reading it. This is because that if you change your analyzer's settings, the UI might try to load the now out-of-date settings from the previous capture automatically, when it migrates analyzers and HLAs from one capture to another.

Another helpful pattern is to hold the specific settings names in global variables, to help avoid typos.

For example:

```py
STRING_SETTING_LABEL = 'First Setting Label'
# ....
  def get_capabilities(self):
    return {
      'settings': {
          STRING_SETTING_LABEL: {
              'type': 'string'
          },
      }
  }
  def set_settings(self, settings):
    if STRING_SETTING_LABEL in settings.keys():
      self.setting1 = settings[STRING_SETTING_LABEL]
```

To access user edited settings in the `def decode(self, data)` method, first save them in class member variables.

## HLA life Cycle

Your HLA class will be constructed the moment the user adds your HLA, even if no data has been captured yet.

Immediately on construction, `get_capabilities` will be called a single time. It will only be called once for the lifetime of the HLA class.

`set_settings` may be called zero or more times:

- If a user adds your HLA, but cancels before selecting an input analyzer or settings, then `set_settings` will never be called.
- `set_settings` is called when the user saves their analyzer settings, after first adding the HLA or after editing its settings.
- `set_settings` is called automatically when the user opens a new tab, and your HLA was in use on the previous tab. Their previous settings automatically passed in. This also happens when opening the application if your HLA was in use at the end of the previous application run. It's also called automatically if the user loads a saved capture that included your HLA.

`set_settings` indicates that your HLA should reset internal state and prepare for new frames. This could indicate just new settings, but it could also indicate that the input analyzer has changed, or one of the settings of the input analyzer has changed. The exact frames passed in might not be the same as the previous run.

Instances of your HLA class are NOT re-used between captures or tabs. Each capture will have its own instance of your class. Instances can be created before a capture starts, or after a capture has been completed.

The python file on disk is freshly read right before constructing the HLA class.

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
