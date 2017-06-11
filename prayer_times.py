#!/usr/bin/env python
# coding: utf-8
# compatible with python 2.x and 3.x

import math
import re
import subprocess
import datetime
import dateutil.tz
import sys

"""
--------------------- Copyright Block ----------------------

praytimes.py: Prayer Times Calculator (ver 2.3)
Copyright (C) 2007-2011 PrayTimes.org

Python Code: Saleem Shafi, Hamid Zarrabi-Zadeh
Original js Code: Hamid Zarrabi-Zadeh

License: GNU LGPL v3.0

TERMS OF USE:
    Permission is granted to use this code, with or
    without modification, in any website or application
    provided that credit is given to the original work
    with a link back to PrayTimes.org.

This program is distributed in the hope that it will
be useful, but WITHOUT ANY WARRANTY.

PLEASE DO NOT REMOVE THIS COPYRIGHT BLOCK.


--------------------- Help and Manual ----------------------

User's Manual:
http://praytimes.org/manual

Calculation Formulas:
http://praytimes.org/calculation


------------------------ User Interface -------------------------

    getTimes (date, coordinates, timeZone [, dst [, timeFormat]])

    setMethod (method)       // set calculation method
    adjust (parameters)      // adjust calculation parameters
    tune (offsets)           // tune times by given offsets

    getMethod ()             // get calculation method
    getSetting ()            // get current calculation parameters
    getOffsets ()            // get current time offsets


------------------------- Sample Usage --------------------------

    >>> PT = PrayTimes('ISNA')
    >>> times = PT.getTimes((2011, 2, 9), (43, -80), -5)
    >>> times['sunrise']
    07:26

"""

# ----------------------- PrayTimes Class ------------------------


class PrayTimes():

    # ------------------------ Constants --------------------------

    # Time Names
    time_names = {
        'imsak': 'Imsak',
        'fajr': 'Fajr',
        'sunrise': 'Sunrise',
        'dhuhr': 'Dhuhr',
        'asr': 'Asr',
        'sunset': 'Sunset',
        'maghrib': 'Maghrib',
        'isha': 'Isha',
        'midnight': 'Midnight'
    }

    # Calculation Methods
    methods = {
        'MWL': {
            'name': 'Muslim World League',
            'params': {'fajr': 18, 'isha': 17}
        },
        'ISNA': {
            'name': 'Islamic Society of North America (ISNA)',
            'params': {'fajr': 15, 'isha': 15}
        },
        'Egypt': {
            'name': 'Egyptian General Authority of Survey',
            'params': {'fajr': 19.5, 'isha': 17.5}
        },
        'Makkah': {
            'name': 'Umm Al-Qura University, Makkah',
            # fajr was 19 degrees before 1430 hijri
            'params': {'fajr': 18.5, 'isha': '90 min'}
        },
        'Karachi': {
            'name': 'University of Islamic Sciences, Karachi',
            'params': {'fajr': 18, 'isha': 18}
        },
        'Tehran': {
            'name': 'Institute of Geophysics, University of Tehran',
            # isha is not explicitly specified in this method
            'params': {'fajr': 17.7, 'isha': 14, 'maghrib': 4.5, 'midnight': 'Jafari'}
        },
        'Jafari': {
            'name': 'Shia Ithna-Ashari, Leva Institute, Qum',
            'params': {'fajr': 16, 'isha': 14, 'maghrib': 4, 'midnight': 'Jafari'}
        }
    }

    # Default Parameters in Calculation Methods
    default_params = {
        'maghrib': '0 min', 'midnight': 'Standard'
    }

    # ---------------------- Default Settings --------------------

    calc_method = 'ISNA'

    # do not change anything here; use adjust method instead
    settings = {
        "imsak": '10 min',
        "dhuhr": '0 min',
        "asr": 'Standard',
        "highLats": 'NightMiddle'
    }

    time_format = '24h'
    time_suffixes = ['am', 'pm']
    invalid_time = '-----'

    num_iterations = 1
    offset = {}

    # ---------------------- Initialization -----------------------

    def __init__(self, method="ISNA"):
        # set methods defaults
        for method_name, config in self.methods.items():
            for name, value in self.default_params.items():
                if name not in config['params'] or config['params'][name] is None:
                    config['params'][name] = value

        # initialize settings
        self.calc_method = method if method in self.methods else 'ISNA'
        params = self.methods[self.calc_method]['params']
        for name, value in params.items():
            self.settings[name] = value

        # init time offsets
        for name in self.time_names:
            self.offset[name] = 0

    # -------------------- Interface Functions --------------------

    def set_method(self, method):
        if method in self.methods:
            self.adjust(self.methods[method].params)
            self.calc_method = method

    def adjust(self, params):
        self.settings.update(params)

    def tune(self, timeOffsets):
        self.offsets.update(timeOffsets)

    def get_method(self):
        return self.calc_method

    def get_settings(self):
        return self.settings

    def get_offsets(self):
        return self.offset

    def get_defaults(self):
        return self.methods

    # return prayer times for a given date
    def get_times(self, date, coords, timezone, dst=0, format=None):
        self.lat = coords[0]
        self.lng = coords[1]
        self.elv = coords[2] if len(coords) > 2 else 0

        if format is not None:
            self.time_format = format
        if type(date).__name__ == 'date':
            date = (date.year, date.month, date.day)

        self.timeZone = timezone + (1 if dst else 0)
        self.jDate = self.julian(date[0], date[1], date[2]) - self.lng / (15 * 24.0)
        return self.compute_times()

    # convert float time to the given format (see timeFormats)
    def get_formatted_time(self, time, format, suffixes=None):
        if math.isnan(time):
            return self.invalid_time
        if format == 'Float':
            return time
        if suffixes is None:
            suffixes = self.time_suffixes

        # add 0.5 minutes to round
        time = self.fixhour(time + 0.5 / 60)
        hours = math.floor(time)

        minutes = math.floor((time - hours) * 60)
        suffix = suffixes[0 if hours < 12 else 1] if format == '12h' else ''
        formattedTime = "%02d:%02d" % (hours, minutes) if format == "24h" else "%d:%02d" % ((hours + 11) % 12 + 1, minutes)
        return formattedTime + suffix

    # ---------------------- Calculation Functions -----------------------

    # compute mid-day time
    def mid_day(self, time):
        eqt = self.sun_position(self.jDate + time)[1]
        return self.fixhour(12 - eqt)

    # compute the time at which sun reaches a specific angle below horizon
    def sun_angle_time(self, angle, time, direction=None):
        try:
            decl = self.sun_position(self.jDate + time)[0]
            noon = self.mid_day(time)
            t = 1 / 15.0 * self.arccos((-self.sin(angle) - self.sin(decl) * self.sin(self.lat)) / (self.cos(decl) * self.cos(self.lat)))
            return noon + (-t if direction == 'ccw' else t)
        except ValueError:
            return float('nan')

    # compute asr time
    def asr_time(self, factor, time):
        decl = self.sun_position(self.jDate + time)[0]
        angle = -self.arccot(factor + self.tan(abs(self.lat - decl)))
        return self.sun_angle_time(angle, time)

    # compute declination angle of sun and equation of time
    # Ref: http://aa.usno.navy.mil/faq/docs/SunApprox.php
    def sun_position(self, jd):
        D = jd - 2451545.0
        g = self.fixangle(357.529 + 0.98560028 * D)
        q = self.fixangle(280.459 + 0.98564736 * D)
        L = self.fixangle(q + 1.915 * self.sin(g) + 0.020 * self.sin(2 * g))

        # R = 1.00014 - 0.01671 * self.cos(g) - 0.00014 * self.cos(2 * g)
        e = 23.439 - 0.00000036 * D

        RA = self.arctan2(self.cos(e) * self.sin(L), self.cos(L)) / 15.0
        eqt = q / 15.0 - self.fixhour(RA)
        decl = self.arcsin(self.sin(e) * self.sin(L))

        return (decl, eqt)

    # convert Gregorian date to Julian day
    # Ref: Astronomical Algorithms by Jean Meeus
    def julian(self, year, month, day):
        if month <= 2:
            year -= 1
            month += 12
        A = math.floor(year / 100)
        B = 2 - A + math.floor(A / 4)
        return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5

    # ---------------------- Compute Prayer Times -----------------------

    # compute prayer times at given julian date
    def compute_prayer_times(self, times):
        times = self.day_portion(times)
        params = self.settings

        imsak = self.sun_angle_time(self.eval(params['imsak']), times['imsak'], 'ccw')
        fajr = self.sun_angle_time(self.eval(params['fajr']), times['fajr'], 'ccw')
        sunrise = self.sun_angle_time(self.rise_set_angle(self.elv), times['sunrise'], 'ccw')
        dhuhr = self.mid_day(times['dhuhr'])
        asr = self.asr_time(self.asr_factor(params['asr']), times['asr'])
        sunset = self.sun_angle_time(self.rise_set_angle(self.elv), times['sunset'])
        maghrib = self.sun_angle_time(self.eval(params['maghrib']), times['maghrib'])
        isha = self.sun_angle_time(self.eval(params['isha']), times['isha'])

        return {
            'imsak': imsak, 'fajr': fajr, 'sunrise': sunrise, 'dhuhr': dhuhr,
            'asr': asr, 'sunset': sunset, 'maghrib': maghrib, 'isha': isha
        }

    # compute prayer times
    def compute_times(self):
        times = {
            'imsak': 5, 'fajr': 5, 'sunrise': 6, 'dhuhr': 12,
            'asr': 13, 'sunset': 18, 'maghrib': 18, 'isha': 18
        }
        # main iterations
        for i in range(self.num_iterations):
            times = self.compute_prayer_times(times)
        times = self.adjust_times(times)
        # add midnight time
        if self.settings['midnight'] == 'Jafari':
            times['midnight'] = times['sunset'] + self.time_diff(times['sunset'], times['fajr']) / 2
        else:
            times['midnight'] = times['sunset'] + self.time_diff(times['sunset'], times['sunrise']) / 2

        times = self.tune_times(times)
        return self.modify_formats(times)

    # adjust times in a prayer time array
    def adjust_times(self, times):
        params = self.settings
        tzAdjust = self.timeZone - self.lng / 15.0
        for t, v in times.items():
            times[t] += tzAdjust

        if params['highLats'] != 'None':
            times = self.adjust_high_lats(times)

        if self.is_min(params['imsak']):
            times['imsak'] = times['fajr'] - self.eval(params['imsak']) / 60.0
        # need to ask about 'min' settings
        if self.is_min(params['maghrib']):
            times['maghrib'] = times['sunset'] - self.eval(params['maghrib']) / 60.0

        if self.is_min(params['isha']):
            times['isha'] = times['maghrib'] - self.eval(params['isha']) / 60.0
        times['dhuhr'] += self.eval(params['dhuhr']) / 60.0

        return times

    # get asr shadow factor
    def asr_factor(self, asrParam):
        methods = {'Standard': 1, 'Hanafi': 2}
        return methods[asrParam] if asrParam in methods else self.eval(asrParam)

    # return sun angle for sunset/sunrise
    def rise_set_angle(self, elevation=0):
        elevation = 0 if elevation is None else elevation
        # an approximation
        return 0.833 + 0.0347 * math.sqrt(elevation)

    # apply offsets to the times
    def tune_times(self, times):
        for name, value in times.items():
            times[name] += self.offset[name] / 60.0
        return times

    # convert times to given time format
    def modify_formats(self, times):
        for name, value in times.items():
            times[name] = self.get_formatted_time(times[name], self.time_format)
        return times

    # adjust times for locations in higher latitudes
    def adjust_high_lats(self, times):
        params = self.settings
        # sunset to sunrise
        nightTime = self.time_diff(times['sunset'], times['sunrise'])
        times['imsak'] = self.adjust_HL_time(times['imsak'], times['sunrise'], self.eval(params['imsak']), nightTime, 'ccw')
        times['fajr'] = self.adjust_HL_time(times['fajr'], times['sunrise'], self.eval(params['fajr']), nightTime, 'ccw')
        times['isha'] = self.adjust_HL_time(times['isha'], times['sunset'], self.eval(params['isha']), nightTime)
        times['maghrib'] = self.adjust_HL_time(times['maghrib'], times['sunset'], self.eval(params['maghrib']), nightTime)
        return times

    # adjust a time for higher latitudes
    def adjust_HL_time(self, time, base, angle, night, direction=None):
        portion = self.night_portion(angle, night)
        diff = self.time_diff(time, base) if direction == 'ccw' else self.time_diff(base, time)
        if math.isnan(time) or diff > portion:
            time = base + (-portion if direction == 'ccw' else portion)
        return time

    # the night portion used for adjusting times in higher latitudes
    def night_portion(self, angle, night):
        method = self.settings['highLats']
        # midnight
        portion = 1 / 2.0
        if method == 'AngleBased':
            portion = 1 / 60.0 * angle
        if method == 'OneSeventh':
            portion = 1 / 7.0
        return portion * night

    # convert hours to day portions
    def day_portion(self, times):
        for i in times:
            times[i] /= 24.0
        return times

    # ---------------------- Misc Functions -----------------------

    # compute the difference between two times
    def time_diff(self, time1, time2):
        return self.fixhour(time2 - time1)

    # convert given string into a number
    def eval(self, st):
        val = re.split('[^0-9.+-]', str(st), 1)[0]
        return float(val) if val else 0

    # detect if input contains 'min'
    def is_min(self, arg):
        return isinstance(arg, str) and arg.find('min') > -1

    # ----------------- Degree-Based Math Functions -------------------

    def sin(self, d):
        return math.sin(math.radians(d))

    def cos(self, d):
        return math.cos(math.radians(d))

    def tan(self, d):
        return math.tan(math.radians(d))

    def arcsin(self, x):
        return math.degrees(math.asin(x))

    def arccos(self, x):
        return math.degrees(math.acos(x))

    def arctan(self, x):
        return math.degrees(math.atan(x))

    def arccot(self, x):
        return math.degrees(math.atan(1.0 / x))

    def arctan2(self, y, x):
        return math.degrees(math.atan2(y, x))

    def fixangle(self, angle):
        return self.fix(angle, 360.0)

    def fixhour(self, hour):
        return self.fix(hour, 24.0)

    def fix(self, a, mode):
        if math.isnan(a):
            return a

        a = a - mode * (math.floor(a / mode))
        return a + mode if a < 0 else a


# <bitbar.title>Prayer Times</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Furkan Üzümcü</bitbar.author>
# <bitbar.author.github>Furkanzmc</bitbar.author.github>
# <bitbar.desc>Displays the prayer time based on your lcoation.</bitbar.desc>
# <bitbar.image>https://drive.google.com/uc?export=download&id=0B2b4SnYRu-h_NHhfUmtMalB4RUU</bitbar.image>
# <bitbar.dependencies>python</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/Furkanzmc/BitBarPrayerTimes</bitbar.abouturl>

def main():
    is_remaining_disabled = False
    calculation_method = 'ISNA'
    if len(sys.argv) > 1:
        if "--help" in sys.argv:
            print(
                """
Available Args:
    --no-remaining: This will disable the remining time showing. This way you can increase the refresh rate of the script to 1 day.
    --calculation-method: Select the calculation method. The default is ISNA
        - Available options are:
        - MWL: Muslim World League
        - ISNA: Islamic Society of North America (ISNA)
        - Egypt: Egyptian General Authority of Survey
        - Makkah: Umm Al-Qura University, Makkah
        - Karachi: University of Islamic Sciences, Karachi'
        - Tehran: Institute of Geophysics, University of Tehran
        - Jafari: Shia Ithna-Ashari, Leva Institute, Qum

Example:
    prayer_times.py --calculation-method MWL
            """
            )
            return
        if "--no-remaining" in sys.argv:
            is_remaining_disabled = True
        elif "--calculation-method" in sys.argv:
            found_index = sys.argv.index("--calculation-method")
            if len(sys.argv) > found_index + 1:
                calculation_method = sys.argv[found_index + 1]

    prayTimes = PrayTimes(calculation_method)
    print('Prayer Times | dropdown=false')
    print("Calculation Method: %s" % (prayTimes.calc_method))
    is_current_time_passed = True
    latitude = None
    longitude = None

    localtz = dateutil.tz.tzlocal()
    localoffset = localtz.utcoffset(datetime.datetime.now(localtz))
    timezone_offset = localoffset.total_seconds() / 3600

    # If corelocationcli is installed, get the location
    # Get it from here: https://github.com/fulldecent/corelocationcli
    try:
        proc = subprocess.Popen(["/usr/local/bin/CoreLocationCLI", "-once"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = proc.communicate()
        latitude = float(output.split(" ")[0])
        longitude = float(output.split(" ")[1])
    except:
        pass

    if latitude is None or longitude is None:
        print("Cannot get the location through CoreLocationCLI. Please install it or type in custome location.")
    else:
        times = prayTimes.get_times(datetime.date.today(), (latitude, longitude), timezone_offset)
        for i in ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
            prayer_hour = int(times[i.lower()].split(":")[0])
            prayer_minute = int(times[i.lower()].split(":")[1])
            now = datetime.datetime.now()
            time_str = "%s.%s.%s %s:%s" % (now.year, now.month, now.day, prayer_hour, prayer_minute)
            prayer_date = datetime.datetime.strptime(time_str, '%Y.%m.%d %H:%M')

            delta = prayer_date - now
            remaining = ""

            color = "gray"
            if delta.seconds < 0:
                color = "#424242"
            elif is_current_time_passed and is_remaining_disabled is False:
                is_current_time_passed = False
                if is_remaining_disabled is False:
                    remaining_minutes = ":".join(str(delta).split(":")[:2])
                    remaining = " (" + str(remaining_minutes) + " Remaining)"
                    color = "#E53935" if remaining_minutes < 15 else "#4CAF50"
                else:
                    color = "#4CAF50"

            print(i + ': ' + times[i.lower()] + remaining + " | color=" + color)


if __name__ == "__main__":
    main()
