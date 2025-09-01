Uses raspberry pi with wifi and bluetooth for starting, finishing and recording race positions.

The RPi OS is standard 32bit lite version without desktop. It needs to have a few dependencies added:

  ## NB for serial to work you must first install pip and venv
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
  ## enable systemd service (also start, stop, restart for debugging
      systemctl --user enable race_timer.service

  ## NB also, you must set up serial on the pi config
      sudo raspi-config -> interface optn -> serial -> login[No], enabled[Yes]
  ## NB also, the pi must be set to auto login in raspi-config

  ## For the bluetooth headphones and audio to work you need to setup bluealsa
      sudo apt update
      sudo apt install bluez-alsa-utils
      /usr/bin/bluealsa -p a2dp-source -p a2dp-sink -p hfp-hr -p hsp-hf -p hfp-ag -p hsp-ag
      bluetoothctl
      # scan on ### <- NB the headphones need to have pairing turned on too, normally turn on and hold button
      # scan off ### once the device has been found
      # pair 1A:2B:3C:4D:5E:6F ### number shown when device found
      # trust 1A:2B:3C:4D:5E:6F ### or whatever id is
      # exit
      bluetoothctl devices
  ## copy paste id into - the above and following steps are done automatically when the timer runs but worth checking
      bluetoothctl connect 1A:2B:3C:4D:5E:6F
  ## also try
      aplay -D bluealsa audio/finish.wav
