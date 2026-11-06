# Configuration

## Setup wizard

Run the wizard to create or change your settings:

```bash
python3 setup-wizard.py
```

The wizard:

1. Selects the library for your CPU.
2. Asks you to unplug the interface and plug it back in, then reads the serial number.
3. Asks for the direction, protocol and number of universe 1 and 2.
4. Saves everything in `config.json`.

Restart the script after you change the settings.

## Directions

The interface has one DMX output and one DMX input, so each direction can only be used once.

| Direction | Data flow |
|---|---|
| `out` | Network to DMX output |
| `in` | DMX input to network |
| `off` | Not used |

## Universe numbers

| Protocol | Range |
|---|---|
| Art-Net | 0–32767 |
| sACN | 1–63999 |

## config.json

You can also edit the file by hand:

```json
{
  "serial": "0000800010011617",
  "library": "/home/YOUR_USER/ARTNET-TO-USBDMX/usbdmx-x86_64.so",
  "dmx_out": {"protocol": "sacn", "universe": 1},
  "dmx_in": {"protocol": "artnet", "universe": 1},
  "artnet_target_ip": "255.255.255.255",
  "sacn_interface_ip": "0.0.0.0",
  "sacn_source_id": "created by the setup wizard"
}
```

| Setting | Meaning |
|---|---|
| `serial` | Serial number of the interface |
| `library` | Full path of the library |
| `dmx_out` | Protocol and universe of the DMX output, or `null` when off |
| `dmx_in` | Protocol and universe of the DMX input, or `null` when off |
| `artnet_target_ip` | Where Art-Net from the DMX input is sent. The default is broadcast. |
| `sacn_interface_ip` | IP of the network card for sACN. `0.0.0.0` uses the system default. |
| `sacn_source_id` | ID that identifies this device as an sACN source. Do not change it. |

## sACN behavior

- The script joins the multicast group of the universe, and also accepts unicast.
- If several sources send the same universe, the highest priority wins.
- If a source stops, the last values stay on the output.
- The DMX input is sent by multicast at least once per second.

## Operating mode

The script uses interface mode 6: PC to DMX output, and DMX input to PC. To change it, edit the `SetInterfaceMode` calls in `usbdmx-artnet.py`.

| Mode | Function |
|---|---|
| 0 | Standby |
| 1 | DMX input to DMX output |
| 2 | PC to DMX output |
| 3 | DMX input and PC to DMX output |
| 4 | DMX input to PC |
| 5 | DMX input to DMX output, and DMX input to PC |
| 6 | PC to DMX output, and DMX input to PC |
| 7 | DMX input and PC to DMX output, and DMX input to PC |
