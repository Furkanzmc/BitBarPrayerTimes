# BitBarPrayerTimes
![image](https://drive.google.com/uc?export=download&id=0B2b4SnYRu-h_NHhfUmtMalB4RUU)

A script to show prayer times in BitBar.

Depends on [CoreLocationCli](https://github.com/fulldecent/corelocationcli) to get the device location. Make sure it is installed under `/usr/local/bin`.

Example script to use in a separate folder.

```
#!/bin/bash

chmod +x /Users/Furkanzmc/Development/GitHub/BitBarPrayerTimes/prayer_times.py && /Users/Furkanzmc/Development/GitHub/BitBarPrayerTimes/prayer_times.py
```

Save this script into your BitBar plugins directory and give necessary permissions using `chmod +x ~/BitBar/Plugins/BitBarPrayerTimes.sh` .

# Credits

Prayer time calculation is taken from [here](http://praytimes.org/code/git/?a=tree&p=PrayTimes&hb=HEAD&f=v2/python)
