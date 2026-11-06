# ARTNET-TO-USBDMX

Use the Digital Enlightenment FX5-USBDMX interface as an Art-Net and sACN node.

![Picture not found](picture.png)

## Features

- Network to DMX output, and DMX input to network
- Art-Net or sACN (E1.31) for each direction
- Setup wizard that finds your interface automatically
- Runs on x86_64 and 64-bit ARM Linux, such as a Raspberry Pi

## Requirements

- A Linux machine with Python 3
- A Digital Enlightenment FX5-USBDMX interface (other devices are not supported)
- A 9–12 V power supply for the interface, if your USB port does not provide enough power

## Quick start

```bash
git clone https://github.com/David-Birk/ARTNET-TO-USBDMX.git
cd ARTNET-TO-USBDMX
python3 setup-wizard.py
python3 usbdmx-artnet.py
```

## Documentation

- [Installation and autostart](docs/INSTALL.md)
- [Configuration](docs/CONFIGURATION.md)
- [Problem solving](docs/PROBLEM-SOLVING.md)
- [Code of conduct](docs/CODE-OF-CONDUCT.md)
- [License](docs/LICENSE.md)

## Support

Open an [issue](https://github.com/David-Birk/ARTNET-TO-USBDMX/issues) or send an email to PigcraftTV50@gmail.com.
