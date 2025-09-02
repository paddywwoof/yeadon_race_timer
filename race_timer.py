""" See required setup for various dependencies and systemd:
    a) in comments for check_gps()
    b) connect_headphones()
""" 
import time
import json
import serial # requires pip install serial
import subprocess
from datetime import datetime, timedelta
from threading import Thread

from race_times import race_times
from race_sequence import race_sequence

LATLON_DELAY = 5 # do we need this? Can let it run flat out as serial read blocking
CLOCKSET_DELAY = 3600 # every hour
SAVE_DELAY = 10 # six times per minute -> 300 positions per race
#VOL_CONTROL = "'Aeropex by AfterShokz - A2DP Playback Volum'"
#VOL_CONTROL = "'Bluetooth music - A2DP'"
VOL_CONTROL = "'G01 - A2DP'"
DEBUG = True

class RaceTimer:
    def __init__(self):
        self.seq = 0
        self.racing = False
        self.tm = datetime.now()
        self.id = self.get_mac_address().replace(":", "")[-4:] # this is just last 4 of 12 alphanumeric char
        self.last_clockset = 0.0
        self.lat = 53.8673147 #default value at club house
        self.lon = -1.6768643
        self.race_data = {"uid": self.id, "race": 000000-0000, "locations":[]}
        self.next_race = None
        self.headphones_connected = False
        self.connect_headphones() # this only works if headphones switched on first but saves delay playing first msg
        self.volume_set = False
        self.last_updated_race_times = None # just in case left on over night

        self.thread1 = Thread(target=self.check_gps)
        self.thread1.start()
        self.thread2 = Thread(target=self.add_to_history)
        self.thread2.start()
        self.thread3 = Thread(target=self.check_sequence)
        self.thread3.start()

    def check_gps(self):
        """ NB for serial to work you must first install pip and venv
            sudo apt install python3-pip python3-venv
        ## create an evironment to use 
            python3 -m venv /home/pi/venv
            source /home/pi/venv/bin/activate
            python -m pip install pyserial
        ## for systemd to work then use this in /home/pi/.config/systemd/user/race_timer.service
            [Unit]
            Description=Race Timer
            [Service]
            ExecStart=/home/pi/venv/bin/python /home/pi/race_timer.py
            Restart=always
            [Install]
            WantedBy=default.target
        ##
            systemctl --user enable race_timer.service

        # NB also, you must set up serial on the pi config
            sudo raspi-config -> interface optn -> serial -> login[No], enabled[Yes]
        # NB also, the pi must be set to auto login in raspi-config
        """
        # reset system time done as part of this using GPS time
        # does the moving average and other filtering
        last_five_lat = [self.lat] * 5
        last_five_lon = [self.lon] * 5
        ser = serial.Serial('/dev/ttyS0') # TODO set to correct GPIO pin: GPIO15/pin10
        # could also be /dev/ttyAMA0, /dev/serial0 or /dev/serial1
        # NB raspi-config -> interface optn -> serial -> login[No], enabled[Yes]
        while True:
            # running headless so no mechanism to break out of this
            line = ser.readline().split(b',') # block indefinitely waiting for data - chip
            if line[0] == b'$GPGGA' and len(line[2]) > 5: #TODO $GPRMC too with direction and velocity?
                lat = float(line[2][:2]) + float(line[2][2:]) / 60.0
                lon = float(line[4][:3]) + float(line[4][3:]) / 60.0
                if line[5] == b'W':
                    lon *= -1
                last_five_lat = last_five_lat[-4:] # discard oldest readings NB last_five must be at least 5 long
                last_five_lon = last_five_lon[-4:] # discard oldest readings
                last_five_lat.append(lat)
                last_five_lon.append(lon)
                median_reading = sorted(last_five_lat)[2]
                self.lat = median_reading
                median_reading = sorted(last_five_lon)[2]
                self.lon = median_reading
                if DEBUG:
                    print(line)
                # autosync stops this working, should be accurate enough if turned on near wifi!
                #if time.time() - self.last_clockset > CLOCKSET_DELAY:
                #    h = line[1][:2]
                #    m = line[1][2:4]
                #    s = line[1][4:]
                #    subprocess.run(["timedatectl", "set-time", f"'{h}:{m}:{s}'"])
                # shouldn't need sleep because of blocking serial.readline()

    def add_to_history(self):
        # run as background thread add time/position to race_data object
        while True:
            if self.racing:
                self.race_data["locations"].append([int(time.time()), round(self.lat, 8), round(self.lon, 8)]) # reduce file size a bit by round()
            time.sleep(SAVE_DELAY)

    def check_sequence(self):
        this_start = None
        this_finish = None
        next_sound_tm = None
        while True: # threaded function so will run and not be breakable
            self.tm = datetime.now()

            if self.last_updated_race_times is None or (self.tm - self.last_updated_race_times) > timedelta(hours=6):
                for r in race_times:
                    r.update_time_to_today()
                self.last_updated_race_times = self.tm

            if self.seq >= len(race_sequence):
                # race has now ended, save data to disk and get ready for next race,
                # shouldn't get here without starting and finishing a race
                file_name = self.make_file_name(this_start)
                self.race_data["race"] = self.make_dtm_str(this_start)
                with open(file_name, "w") as f:
                    json.dump(self.race_data, f)
                self.race_data = []
                self.racing = False
                self.seq = 0
                this_start = None
                this_finish = None

            if this_start is None:
                for r in race_times:
                    if self.tm < r.time: # consequently the race times must be in ascending order
                        this_start = r.time
                        this_finish = this_start + timedelta(seconds=r.duration)
                        break # first race start where now is before start i.e. next race identified
            else:
                if next_sound_tm is None:
                    next_sound_tm = this_start if race_sequence[self.seq][1] == "s" else this_finish
                    next_sound_tm += timedelta(seconds=race_sequence[self.seq][0])
                if self.tm > next_sound_tm:
                    self.racing = True
                    self.play_sound(race_sequence[self.seq][2])
                    next_sound_tm = None
                    self.seq += 1
            time.sleep(0.1)

    def connect_headphones(self):
        """ on the RPi you need to set up previously
        sudo apt update
        sudo apt install bluez-alsa-utils
        /usr/bin/bluealsa -p a2dp-source -p a2dp-sink -p hfp-hr -p hsp-hf -p hfp-ag -p hsp-ag
        bluetoothctl
        # scan on ### <- the headphones need to have pairing turned on too
        # scan off ### once the device has been found
        # pair 1A:2B:3C:4D:5E:6F ### number shown when device found
        # trust 1A:2B:3C:4D:5E:6F ### or whatever id is
        # exit
        bluetoothctl devices
        # copy paste id into
        bluetoothctl connect AA:BB:CC:DD:EE:FF
        """
        result = subprocess.run(["bluetoothctl", "devices"], capture_output=True)
        headphones_id = result.stdout.split()[1].decode('utf8') # make sure there's only one bluetooth device in list!
        result = subprocess.run(["bluetoothctl", "connect", headphones_id], capture_output=True)
        last_words = result.stdout.decode('utf8').split()[-2:]
        if last_words == ["Connection", "successful"]:
            self.headphones_connected = True
        if DEBUG:
            print("headphone", result.stdout)
            print(" --> conected ", self.headphones_connected)

    def make_file_name(self, dtm: datetime):
        # Now use just last four characters of mac address as ID
        dtm_str = self.make_dtm_str(dtm)
        if DEBUG:
            print("filename", dtm_str, self.id, "json")
        return f"{dtm_str}-{self.id}.json"
    
    def make_dtm_str(self, dtm: datetime):
        return dtm.strftime("%y%m%d-%H%M") # i.e. 250813-1400

    def play_sound(self, file_name: str):
        if not self.headphones_connected:
            self.connect_headphones()
        if not self.volume_set:
            self.set_volume(50)
            self.volume_set = True
        subprocess.run(["aplay", "-D", "bluealsa", f"audio/{file_name}"])

    def set_volume(self, volume: int):
        """ too loud at 100%, turn down to 50
        the const VOL_CONTROL will be specific to the type of headphones. To find the string to use
        amixer -D bluealsa
        the string will have something relating to volume NB single quotes as part of string
        """
        subprocess.run(["amixer", "-D", "bluealsa", "--", "sset", VOL_CONTROL, f"{volume}%"]) # TODO check if successful?

    def get_mac_address(self):
        # use this as ID for this RPi
        # TODO no failure mode or try/catch
        result = subprocess.run(["ifconfig"], capture_output=True)
        ix = result.stdout.find(b"ether")
        if DEBUG:
            print(result.stdout[ix:])
        return result.stdout[ix:].split()[1].decode("utf8")

rt = RaceTimer()

while True: # stop the applicaiton from closing
    time.sleep(1.0)