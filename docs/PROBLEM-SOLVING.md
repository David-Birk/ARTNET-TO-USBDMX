# Problem solving

## "config.json not found"

Run the setup wizard: `python3 setup-wizard.py`

## "cannot open shared object file: No such file or directory"

The file exists, but it was built for a different CPU. Compare `uname -m` with the table in [Libraries](INSTALL.md#libraries), and run the setup wizard again.

If your CPU is not listed, [build the library yourself](INSTALL.md#build-the-library-yourself).

## "Unable to open interface"

1. Check the serial number in `config.json`.
2. Try to run the script as root.
3. If that works, [set up the udev rule](INSTALL.md#run-without-root).

## The wizard does not find the interface

Unplug the interface before you press Enter, and plug it back in after that. If it still fails, enter the serial number by hand. This command shows it:

```bash
sudo dmesg | grep -i serialnumber
```

## No output from Art-Net or sACN

- Check that the universe number matches. Some software counts from 1 and some from 0.
- If your machine has more than one network card, enter the IP of the right one for sACN in the setup wizard.
- Check that your switch allows multicast for sACN.

## DMX input does not arrive on the network

Your switch or router might block broadcast. Change that setting, or enter the IP of the receiver as Art-Net target in the setup wizard.

## Still stuck?

Open an [issue](https://github.com/David-Birk/ARTNET-TO-USBDMX/issues) or send an email to PigcraftTV50@gmail.com.
