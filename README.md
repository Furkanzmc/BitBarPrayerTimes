# BitBarPrayerTimes
![image](https://drive.google.com/uc?export=download&id=0B2b4SnYRu-h_NHhfUmtMalB4RUU)

A script to show prayer times in BitBar.

Depends on [CoreLocationCli](https://github.com/fulldecent/corelocationcli) to get the device location. Make sure it is installed under `/usr/local/bin`.

Example script to use in a separate folder.

```
#!/bin/bash

chmod +x /Users/Furkanzmc/Development/GitHub/BitBarPrayerTimes/prayer_times.py && /Users/Furkanzmc/Development/GitHub/BitBarPrayerTimes/prayer_times.py
```

Save this script into your BitBar plugins directory and give necessary permissions using `chmod +x ~/BitBar/Plugins/BitBarPrayerTimes.sh`.

# Arguments

You can also use `prayer_times.py --help` to print the following text.

**--no-remaining:** This will disable the remining time showing. This way you can increase the refresh rate of the script to 1 day.

**--calculation-method:** Select the calculation method. The default is ISNA. Available options are:
- MWL: Muslim World League
- ISNA: Islamic Society of North America (ISNA)
- Egypt: Egyptian General Authority of Survey
- Makkah: Umm Al-Qura University, Makkah
- Karachi: University of Islamic Sciences, Karachi'
- Tehran: Institute of Geophysics, University of Tehran
- Jafari: Shia Ithna-Ashari, Leva Institute, Qum

**--bar-label:** This will be used if --no-remaining parameter is given. This way you can change the label that appears on the bar.

**Example:**

    prayer_times.py --calculation-method MWL

# Credits

Prayer time calculation is taken from [here](http://praytimes.org/code/git/?a=tree&p=PrayTimes&hb=HEAD&f=v2/python). I just formatted the code.
