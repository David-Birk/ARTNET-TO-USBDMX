# Installation

## Install

1. Download the repository:

   ```bash
   git clone https://github.com/David-Birk/ARTNET-TO-USBDMX.git
   cd ARTNET-TO-USBDMX
   ```

2. Connect the interface.

3. Run the setup wizard:

   ```bash
   python3 setup-wizard.py
   ```

4. Start the script:

   ```bash
   python3 usbdmx-artnet.py
   ```

## Libraries

The script needs a compiled library that matches your CPU. The setup wizard selects it for you.

Check your CPU with `uname -m`.

| File | CPU | Required system library |
|---|---|---|
| `usbdmx.so` | aarch64 (such as 64-bit Raspberry Pi OS) | `libhidapi-libusb0` |
| `usbdmx-x86_64.so` | x86_64 (most PCs and laptops) | `libudev1` |

## Build the library yourself

Do this if you have a different CPU, or if the included library does not work.

```bash
sudo apt install build-essential pkg-config libudev-dev git
git clone https://github.com/fx5/usbdmx.git
cd usbdmx
make libusbdmx.so
```

Then enter the full path of `libusbdmx.so` as `library` in `config.json`.

## Run without root

Install the udev rule from the driver:

```bash
git clone https://github.com/fx5/usbdmx.git
sudo cp usbdmx/50-usbdmx.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

Then unplug the interface and plug it back in.

## Autostart

Run the setup wizard first. The service then starts the script at boot, and keeps retrying until the interface is connected.

1. Create the service file:

   ```bash
   sudo nano /etc/systemd/system/artnet-to-usbdmx.service
   ```

2. Paste this, and replace `YOUR_USER` with your username:

   ```ini
   [Unit]
   Description=Artnet to USB-DMX Autostart Service
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /home/YOUR_USER/ARTNET-TO-USBDMX/usbdmx-artnet.py
   WorkingDirectory=/home/YOUR_USER/ARTNET-TO-USBDMX
   User=YOUR_USER
   Restart=always
   RestartSec=5
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

3. Save with `Ctrl+O` and exit with `Ctrl+X`.

4. Enable and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now artnet-to-usbdmx.service
   ```

5. Check the status or the log:

   ```bash
   systemctl status artnet-to-usbdmx.service
   journalctl -u artnet-to-usbdmx.service -f
   ```
