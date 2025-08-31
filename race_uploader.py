import requests
import glob
import os
import time
 
# URL for yeadonsailingclub.co.uk...
URL = 'https://eldwick.org.uk/yeadontest/yeadon_post_data.php'
HEADERS = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)' }
DELAY = 60
DEBUG = True
""" NB for requests to work you must first install pip and venv
   sudo apt install python3-pip python3-venv
## create an evironment to use 
   python3 -m venv /home/pi/venv
   source /home/pi/venv/bin/activate
   python -m pip install requests
## for systemd to work then use this in /home/pi/.config/systemd/user/race_uploader.service
   [Unit]
   Description=Race Uploader
   [Service]
   ExecStart=/home/pi/venv/bin/python /home/pi/race_uploader.py
   Restart=always
   [Install]
   WantedBy=default.target
##
   systemctl --user enable race_uploader.service
"""
while True: # running headless, started with systemd so no breaking out
   try:
      for f_name in glob.glob("/home/pi/*.json"):
      #for f_name in glob.glob("/home/patrick/python/yeadon_race_timer/*.json"):
         if DEBUG:
            print(f_name) # debug
         with open(f_name, "r") as f:
            data = f.read() # file will have been saved with json.dump so doesn't need to be jsoned here
            req = requests.post(URL, headers=HEADERS, data=data, timeout=5.0)
            if req.status_code == 200:
               os.remove(f_name) # only delete if uploaded successfully
               print(req.text) # debug message
            else:
               if DEBUG:
                  print('returned status ', req.status_code) # debug
   except Exception as e:
      # could be Timeout or more likely ConnectionError or anything else
      # no special handling for different errors, just have to keep trying
      if DEBUG:
         print(e)
   time.sleep(DELAY)

