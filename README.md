# ARTNET-TO-USBDMX
This Python program allows you to use the Digital Enlightenment FX5-USBDMX interface as an Art-Net node.

![Picture not found](picture.png)


# Requirements:

A Linux-based system (e.g., Raspberry Pi) to run the script

The Digital Enlightenment FX5-USBDMX interface (other devices are not supported)

An external power supply for the interface if your machine’s USB ports do not provide sufficient power
(recommended: 9–12 V PSU)

# Included Libraries:

The script needs a compiled library that matches your CPU. Check your CPU with: uname -m

| File | CPU (uname -m) | Required system library |
|---|---|---|
| usbdmx.so | aarch64 (e.g. 64-bit Raspberry Pi OS) | libhidapi-libusb0 |
| usbdmx-x86_64.so | x86_64 (most PCs and laptops) | libudev1 |

If you use the wrong library, Python reports "cannot open shared object file: No such file or directory", even though the file exists.

usbdmx-x86_64.so was built from https://github.com/fx5/usbdmx (commit 684518e). See LICENSE-usbdmx.txt for its license.

For any other CPU, or if the included library does not work, build it yourself on the target machine:

    sudo apt install build-essential pkg-config libudev-dev git
    git clone https://github.com/fx5/usbdmx.git
    cd usbdmx
    make libusbdmx.so

Then enter the full path of the new libusbdmx.so as "library" in config.json.

# Setup:

Step 1: Download the repository e.g with git clone: git clone https://github.com/PigcraftTV/ARTNET-TO-USBDMX.git

Steo 2: Go into the directory: cd ARTNET-TO-USBDMX

Step 3: Connect your Interface to the Machine

Step 4: Run the setup wizard: python3 setup-wizard.py

     It finds the serial number when you plug the interface back in, then asks for the direction, protocol and number of each universe. The settings are saved in config.json.

Step 5: Now you can run the script with python3 usbdmx-artnet.py

You can run the setup wizard again at any time to change the settings.


# sACN

The script can use sACN (E1.31) instead of Art-Net, for the DMX output, the DMX input, or both. Choose this in the setup wizard.

The interface has one DMX output and one DMX input, so you can set up one universe per direction.

sACN universes start at 1. If your machine has more than one network card, enter the IP of the right one in the setup wizard.

If several sACN sources send the same universe, the highest priority wins. If a source stops, the last values stay on the output.

# Autostart

Wuth the following steps, your Rapberry PI will automaticly start the converter as soon as it boots and  the interface ist plugged in.

Step 1: Create the .service file: nano /etc/systemd/system/artnet-to-usbdmx.service and paste this:

[Unit]
Description=Artnet to USB-DMX Autostart Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/admin/artnet-to-usbdmx.py  <-- You need to change this path according to your user and script directory
WorkingDirectory=/home/admin
User=admin
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

(In Nano press Str + O to save and Str + X to exit)

Step 2: Activate, reload and start the service: sudo systemctl daemon-reload
                                                sudo systemctl enable artnet-to-usbdmx.service
                                                sudo systemctl start artnet-to-usbdmx.service


Step 3: You can enter the log/status with: systemctl status artnet-to-usbdmx.service or journalctl -u artnet-to-usbdmx.service -f



# Notes:

The script generally works without installing additional dependencies.

# Problem Solving:

If you only encounter issues with the USBDMX to Artnet function, you might need to change the Broadcast Setting in your Switch or Router. Otherwise you can directly put in your Destination IP for Unicast.

If the Script says, that it cant open the interface, try to run it as root. To use it without root, copy 50-usbdmx.rules from https://github.com/fx5/usbdmx to /etc/udev/rules.d/, run sudo udevadm control --reload-rules and reconnect the interface.

If you have problems or other issues, you can create a tab under "Issues" or send me an EMail: PigcraftTV50@gmail.com


Additionally, the operating mode can be customized directly within the source code.

