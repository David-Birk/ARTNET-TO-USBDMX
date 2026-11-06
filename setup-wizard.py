"""First-time setup for usbdmx-artnet.py. Writes config.json next to this script."""
import glob
import json
import os
import platform
import time
import uuid

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
USB_DEVICES = "/sys/bus/usb/devices"
UDEV_RULE = "/etc/udev/rules.d/50-usbdmx.rules"
LIBRARIES = {"x86_64": "usbdmx-x86_64.so", "aarch64": "usbdmx.so"}
PLUG_TIMEOUT = 60
UNIVERSE_RANGES = {"artnet": (0, 32767), "sacn": (1, 63999)}
PROTOCOL_NAMES = {"artnet": "Art-Net", "sacn": "sACN"}


def ask_choice(prompt, choices):
    options = "/".join(choices)
    while True:
        answer = input(f"{prompt} [{options}]: ").strip().lower()
        if answer in choices:
            return answer
        print(f"Please enter one of: {options}")


def ask_number(prompt, low, high, default):
    while True:
        answer = input(f"{prompt} ({low}-{high}) [{default}]: ").strip()
        if not answer:
            return default
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        print(f"Please enter a number from {low} to {high}.")


def ask_text(prompt, default):
    return input(f"{prompt} [{default}]: ").strip() or default


def read_attribute(device, name):
    try:
        with open(os.path.join(device, name)) as attribute:
            return attribute.read().strip()
    except OSError:
        return ""


def connected_devices():
    return {os.path.dirname(path) for path in glob.glob(os.path.join(USB_DEVICES, "*", "idVendor"))}


def wait_for_new_device(known_devices):
    deadline = time.monotonic() + PLUG_TIMEOUT
    while time.monotonic() < deadline:
        for device in connected_devices() - known_devices:
            time.sleep(0.5)  # The attributes can appear shortly after the device.
            if read_attribute(device, "serial"):
                return device
        time.sleep(0.5)
    return None


def detect_serial():
    print("\n--- Interface ---")
    input("Unplug the interface from USB, then press Enter...")
    known_devices = connected_devices()
    print(f"Now plug it back in (waiting up to {PLUG_TIMEOUT} seconds)...")

    device = wait_for_new_device(known_devices)
    if device is None:
        print("No new USB device with a serial number was found.")
        return ask_text("Enter the serial number manually", "")

    serial = read_attribute(device, "serial")
    manufacturer = read_attribute(device, "manufacturer")
    product = read_attribute(device, "product")
    print(f"Found: {manufacturer} {product}, serial number {serial}")
    if ask_choice("Is this your interface?", ["y", "n"]) == "y":
        return serial
    return ask_text("Enter the serial number manually", "")


def ask_universe(slot, directions):
    print(f"\n--- Universe {slot} ---")
    direction = ask_choice("Direction", directions + ["off"])
    if direction == "off":
        return None, None

    protocol = ask_choice("Protocol", ["artnet", "sacn"])
    low, high = UNIVERSE_RANGES[protocol]
    default = slot - 1 if protocol == "artnet" else slot
    universe = ask_number(f"{PROTOCOL_NAMES[protocol]} universe number", low, high, default)
    return direction, {"protocol": protocol, "universe": universe}


def ask_universes():
    print("\nThe interface has one DMX output and one DMX input, so each direction can only be used once.")
    print("  out = network -> DMX output")
    print("  in  = DMX input -> network")

    while True:
        ports = {"out": None, "in": None}
        first_direction, first_port = ask_universe(1, ["out", "in"])
        remaining = [direction for direction in ("out", "in") if direction != first_direction]
        second_direction, second_port = ask_universe(2, remaining)

        if first_direction:
            ports[first_direction] = first_port
        if second_direction:
            ports[second_direction] = second_port
        if ports["out"] or ports["in"]:
            return ports["out"], ports["in"]
        print("At least one universe has to be active.")


def describe(port):
    if not port:
        return "off"
    return f"{PROTOCOL_NAMES[port['protocol']]} universe {port['universe']}"


def main():
    print("ARTNET-TO-USBDMX setup")

    previous = {}
    if os.path.exists(CONFIG_PATH):
        if ask_choice("config.json already exists. Replace it?", ["y", "n"]) == "n":
            return
        with open(CONFIG_PATH) as config_file:
            previous = json.load(config_file)

    library = LIBRARIES.get(platform.machine())
    if library is None:
        print(f"There is no included library for {platform.machine()}. See 'Included Libraries' in the README.")
        library_path = ask_text("Enter the full path of your own library", "")
    else:
        library_path = os.path.join(SCRIPT_DIR, library)
        print(f"Using library {library_path}")

    serial = detect_serial()
    dmx_out, dmx_in = ask_universes()

    artnet_target_ip = "255.255.255.255"
    if dmx_in and dmx_in["protocol"] == "artnet":
        artnet_target_ip = ask_text("\nArt-Net target IP (default is broadcast)", artnet_target_ip)

    sacn_interface_ip = "0.0.0.0"
    if "sacn" in (dmx_out or {}).get("protocol", "") + (dmx_in or {}).get("protocol", ""):
        sacn_interface_ip = ask_text("\nIP of the network card for sACN (default is the system default)", sacn_interface_ip)

    config = {
        "serial": serial,
        "library": library_path,
        "dmx_out": dmx_out,
        "dmx_in": dmx_in,
        "artnet_target_ip": artnet_target_ip,
        "sacn_interface_ip": sacn_interface_ip,
        "sacn_source_id": previous.get("sacn_source_id", str(uuid.uuid4())),
    }
    with open(CONFIG_PATH, "w") as config_file:
        json.dump(config, config_file, indent=2)

    print("\n--- Done ---")
    print(f"Serial number: {serial}")
    print(f"DMX output:    {describe(dmx_out)}")
    print(f"DMX input:     {describe(dmx_in)}")
    print(f"Saved to {CONFIG_PATH}")
    if not os.path.exists(UDEV_RULE):
        print("\nNo udev rule found, so you might have to run the script as root (see Problem Solving in the README).")
    print("\nStart it with: python3 usbdmx-artnet.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup cancelled, nothing was saved.")
