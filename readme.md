# Currently Playing Track Info to File
## Rhythmbox plugin that generates TXT and/or JSON documents containing the currently playing track information.

As Rhythmbox plays, this plugin reads information about the currently playing track from the Rhythmbox Database, performs some formatting per the user's configuration settings, then outputs the information to either a `.txt` file, `.json` file or both.

User settings are configured by editing the file "[config.txt](https://github.com/FredGandt/Currently-Playing-Track-Info-to-File/blob/master/config.txt)".

`.txt` output formatting is configured using database property related and custom property templates. Edit "[format.txt](https://github.com/FredGandt/Currently-Playing-Track-Info-to-File/blob/master/format.txt)" to create your desired output, and add custom properties, for use in it, to "[custom-props.txt](https://github.com/FredGandt/Currently-Playing-Track-Info-to-File/blob/master/custom-props.txt)".

## Installation:
### On Linux Mint 19.3 Cinnamon 4.4.8 and similar:

1. Copy the files of this repository; use the "Clone or Download" button to get a .zip file, or copy elseways.
2. Unpack the .zip or drop the files into a folder named "CPTI2F" in the "plugins" folder at: "`/home/<user>/.local/share/rhythmbox/plugins`"
3. Right click the "[CPTI2F.py](https://github.com/FredGandt/Currently-Playing-Track-Info-to-File/blob/master/CPTI2F.py)" file > Select "Properties" > Go to "Permissions" > Check "Allow executing file as program"
4. Start Rhythmbox and goto "Tools" > "Plug-ins..." > "Currently Playing Track Info to File" and check the box to enable it.

### Debugging:

Open the terminal and type `rhythmbox -D CPTI2F` then Enter; Rhythmbox will start in debugging mode with output specifically about this plugin's behaviour. Some verbose debugging messages are commented out in the "[CPTI2F.py](https://github.com/FredGandt/Currently-Playing-Track-Info-to-File/blob/master/CPTI2F.py)" file; uncomment them to see more.

## License (carried over from [the origin of this fork](https://github.com/kflorence/rhythmbox-nowplaying-xml)):

Copyright (c) 2011 Kyle Florence

Released under the MIT license.
