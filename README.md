# plugin-wake-word-precise
Use Mycroft Precise as a wake-word plugin

This module provides a Mycroft plugin module 
for the hotword_factory which supports the 
'hey_mycroft.tflite' model. It adds a dependency
for the tensorflow lite runtime, but other than
that its requirements should be satisfied by the
default Mycroft environment. 

This module must be pip installed into the 
Mycroft environment before use. It also currently
depends on changes to the hotword_factory.py file
which have not been committed yet. These changes
amount to adding the import at the top of the file
and adding the class to the list of available hot
word runners. 

The module installed is named 'hotword_precise_lite'
so for use with Mycroft this line must be added to the 
top of the hotword_factory.py file ...

from hotword_precise_lite.mycroft_hotword import TFLiteHotWord

And in the same file you must  modify the following class ...

class HotWordFactory:
    CLASSES = {
        "pocketsphinx": PocketsphinxHotWord,
        "precise": PreciseHotword,
        "hotword_precise_lite": TFLiteHotWord,
        "snowboy": SnowboyHotWord,
        "porcupine": PorcupineHotWord
    }


You must also change the 'mycroft.conf' config
file to use the plugin. If you copied the 
'hey_mycroft.tflite' model to your default local
Mycroft directory (~/.mycroft/precise/) These are 
the entries which will accomplish this ...

        "module": "hotword_precise_lite",
        "local_model_file": "hey_mycroft.tflite",

At this point Mycroft will probably require a 
reboot to pick up the changes.
