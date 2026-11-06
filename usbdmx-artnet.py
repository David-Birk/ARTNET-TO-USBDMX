import json
import os
import select
import socket
import ctypes
from datetime import datetime
import time
import uuid


# All settings are stored in config.json. Create it with: python3 setup-wizard.py
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
if not os.path.exists(CONFIG_PATH):
    raise SystemExit("config.json not found. Run the setup first: python3 setup-wizard.py")

with open(CONFIG_PATH) as config_file:
    config = json.load(config_file)

def configured_universe(direction: str, protocol: str):
    port = config[direction]
    if port and port["protocol"] == protocol:
        return port["universe"]
    return None

SERIAL_NUMBER = config["serial"].encode()
ARTNET_UNIVERSE_OUT = configured_universe("dmx_out", "artnet")
ARTNET_UNIVERSE_IN = configured_universe("dmx_in", "artnet")
ARTNET_TARGET_IP = config["artnet_target_ip"]
SACN_UNIVERSE_OUT = configured_universe("dmx_out", "sacn")
SACN_UNIVERSE_IN = configured_universe("dmx_in", "sacn")
SACN_INTERFACE_IP = config["sacn_interface_ip"]
SACN_SOURCE_ID = uuid.UUID(config["sacn_source_id"]).bytes
dll_path = config["library"]

_usbdmx = ctypes.CDLL(dll_path)
_usbdmx.OpenLink.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
_usbdmx.OpenLink.restype = ctypes.c_int
_usbdmx.SetInterfaceMode.argtypes = [ctypes.c_char_p, ctypes.c_int]
_usbdmx.SetInterfaceMode.restype = ctypes.c_int
_usbdmx.CloseLink.argtypes = [ctypes.c_char_p]
_usbdmx.CloseLink.restype = None

class FX5Interface:
    def __init__(self, serial: bytes):
        self.serial = serial
        self.dmx_in = ctypes.create_string_buffer(512)
        self.dmx_out = ctypes.create_string_buffer(512)

    def open(self):
        if _usbdmx.OpenLink(self.serial, self.dmx_out, self.dmx_in) == 0:
            raise IOError("Unable to open interface")
        _usbdmx.SetInterfaceMode(self.serial, 6)

    def close(self):
        _usbdmx.CloseLink(self.serial)

    def set_channels(self, channel_values: dict):
        """channel_values = {channel_index: value}"""
        for ch, val in channel_values.items():
            assert 0 <= ch <= 511
            assert 0 <= val <= 255
            self.dmx_out[ch] = val.to_bytes(1, "little")

fx5 = FX5Interface(SERIAL_NUMBER)
fx5.open()
letters = {
    "A": ["  A  ",
          " A A ",
          "AAAAA",
          "A   A",
          "A   A"],
    "R": ["RRRR ",
          "R   R",
          "RRRR ",
          "R R  ",
          "R  RR"],
    "T": ["TTTTT",
          "  T  ",
          "  T  ",
          "  T  ",
          "  T  "],
    "N": ["N   N",
          "NN  N",
          "N N N",
          "N  NN",
          "N   N"],
    "E": ["EEEEE",
          "E    ",
          "EEE  ",
          "E    ",
          "EEEEE"],
    "U": ["U   U",
          "U   U",
          "U   U",
          "U   U",
          " UUU "],
    "S": [" SSS ",
          "S    ",
          " SSS ",
          "    S",
          "SSSS "],
    "D": ["DDDD ",
          "D   D",
          "D   D",
          "D   D",
          "DDDD "],
    "M": ["M   M",
          "MM MM",
          "M M M",
          "M   M",
          "M   M"],
    "X": ["X   X",
          " X X ",
          "  X  ",
          " X X ",
          "X   X"],
    "<": ["  <  ",
          " <   ",
          "<    ",
          " <   ",
          "  <  "],
    ">": ["  >  ",
          "   > ",
          "    >",
          "   > ",
          "  >  "],
    "-": ["     ",
          "-----",
          "     ",
          "     ",
          "     "],
    " ": ["     ",
          "     ",
          "     ",
          "     ",
          "     "],
    "/": ["    /",
          "   / ",
          "  /  ",
          " /   ",
          "/    "],
    "B": [
          "BBBB ",
          "B   B",
          "BBBB ",
          "B   B",
          "BBBB "]

    
}

text = "ARTNET <-> USBDMX"

for i in range(5):
    line = ""
    for char in text:
        line += letters.get(char.upper(), ["     "]*5)[i] + "  "
    print(line)

print("Artnet <-> USBDMX by PigcraftTV")
print(f"[{datetime.now()}] Interface {SERIAL_NUMBER.decode()} opened, DMX-Out ready")

UDP_IP = ""
UDP_PORT = 6454
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind((UDP_IP, UDP_PORT))
print(f"[{datetime.now()}] Art-Net listener started on UDP port {UDP_PORT}")

SACN_PORT = 5568
SACN_SOURCE_TIMEOUT = 2.5
SACN_KEEPALIVE = 1.0
sacn_sock = None
sacn_send_sock = None
sacn_source = None
sacn_priority = 0
sacn_last_seen = 0.0
sacn_sequence = 0
sacn_last_sent = 0.0

def sacn_multicast_group(universe: int) -> str:
    return f"239.255.{universe >> 8}.{universe & 0xFF}"

if SACN_UNIVERSE_IN is not None:
    sacn_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if SACN_INTERFACE_IP != "0.0.0.0":
        sacn_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(SACN_INTERFACE_IP))
    print(f"[{datetime.now()}] sACN sender ready on universe {SACN_UNIVERSE_IN}")

if SACN_UNIVERSE_OUT is not None:
    sacn_group = sacn_multicast_group(SACN_UNIVERSE_OUT)
    sacn_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sacn_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sacn_sock.bind((UDP_IP, SACN_PORT))
    sacn_membership = socket.inet_aton(sacn_group) + socket.inet_aton(SACN_INTERFACE_IP)
    sacn_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, sacn_membership)
    print(f"[{datetime.now()}] sACN listener started on universe {SACN_UNIVERSE_OUT} ({sacn_group}:{SACN_PORT})")

def apply_dmx(dmx_data: bytes, protocol: str):
    changed_channels = {}
    for i, val in enumerate(dmx_data):
        if fx5.dmx_out[i] != val.to_bytes(1, "little"):
            fx5.dmx_out[i] = val.to_bytes(1, "little")
            changed_channels[i+1] = val

    if changed_channels:
        _usbdmx.SetInterfaceMode(fx5.serial, 6)
        print(f"[{datetime.now()}] {protocol} -> DMX, {len(changed_channels)} channels updated")

def parse_sacn(data: bytes):
    """Returns (source_id, priority, terminated, dmx_data), or None if the packet is not for us."""
    if len(data) < 126 or data[4:16] != b"ASC-E1.17\x00\x00\x00":
        return None
    if data[18:22] != b"\x00\x00\x00\x04" or data[40:44] != b"\x00\x00\x00\x02":
        return None
    if data[117] != 0x02 or data[118] != 0xA1:
        return None

    options = data[112]
    universe = int.from_bytes(data[113:115], "big")
    is_preview = options & 0x80
    if universe != SACN_UNIVERSE_OUT or is_preview or data[125] != 0:
        return None

    value_count = int.from_bytes(data[123:125], "big")
    return data[22:38], data[108], bool(options & 0x40), data[126:125+value_count][:512]

def handle_sacn(data: bytes):
    global sacn_source, sacn_priority, sacn_last_seen

    packet = parse_sacn(data)
    if packet is None:
        return

    source_id, priority, terminated, dmx_data = packet
    if terminated:
        if source_id == sacn_source:
            sacn_source = None
        return

    # With several sources the highest priority wins, on a tie the current source stays.
    now = time.monotonic()
    source_lost = now - sacn_last_seen > SACN_SOURCE_TIMEOUT
    if sacn_source is None or source_lost or source_id == sacn_source or priority > sacn_priority:
        sacn_source = source_id
        sacn_priority = priority
        sacn_last_seen = now
        apply_dmx(dmx_data, "sACN")

def send_artnet(universe: int, dmx_data: bytes):
    packet = bytearray()
    packet.extend(b"Art-Net\x00")
    packet.extend((0x5000).to_bytes(2, "little"))
    packet.extend((14).to_bytes(2, "little"))
    packet.extend((0).to_bytes(1, "big"))
    packet.extend((0).to_bytes(1, "big"))
    packet.extend(universe.to_bytes(2, "little"))
    packet.extend(len(dmx_data).to_bytes(2, "big")) 
    packet.extend(dmx_data)

    sock.sendto(packet, (ARTNET_TARGET_IP, UDP_PORT))

def send_sacn(universe: int, dmx_data: bytes):
    global sacn_sequence

    total_length = 126 + len(dmx_data)
    packet = bytearray()
    # Root layer
    packet.extend((0x0010).to_bytes(2, "big"))
    packet.extend((0).to_bytes(2, "big"))
    packet.extend(b"ASC-E1.17\x00\x00\x00")
    packet.extend((0x7000 | (total_length - 16)).to_bytes(2, "big"))
    packet.extend((4).to_bytes(4, "big"))
    packet.extend(SACN_SOURCE_ID)
    # Framing layer
    packet.extend((0x7000 | (total_length - 38)).to_bytes(2, "big"))
    packet.extend((2).to_bytes(4, "big"))
    packet.extend(b"USBDMX".ljust(64, b"\x00"))
    packet.extend((100).to_bytes(1, "big"))
    packet.extend((0).to_bytes(2, "big"))
    packet.extend(sacn_sequence.to_bytes(1, "big"))
    packet.extend((0).to_bytes(1, "big"))
    packet.extend(universe.to_bytes(2, "big"))
    # DMP layer
    packet.extend((0x7000 | (total_length - 115)).to_bytes(2, "big"))
    packet.extend(b"\x02\xa1")
    packet.extend((0).to_bytes(2, "big"))
    packet.extend((1).to_bytes(2, "big"))
    packet.extend((len(dmx_data) + 1).to_bytes(2, "big"))
    packet.extend(b"\x00")
    packet.extend(dmx_data)

    sacn_sequence = (sacn_sequence + 1) % 256
    sacn_send_sock.sendto(packet, (sacn_multicast_group(universe), SACN_PORT))

last_in_state = bytes(512)
listen_sockets = [sock] if sacn_sock is None else [sock, sacn_sock]

while True:

    ready_sockets, _, _ = select.select(listen_sockets, [], [], 0.01)

    if sacn_sock in ready_sockets:
        data, addr = sacn_sock.recvfrom(1024)
        handle_sacn(data)

    data = None
    if sock in ready_sockets:
        data, addr = sock.recvfrom(1024)

    if data and data[:8] == b"Art-Net\x00":
        opcode = int.from_bytes(data[8:10], "little")
        if opcode == 0x5000:  # OpDmx
            universe = int.from_bytes(data[14:16], "little")
            if universe == ARTNET_UNIVERSE_OUT:
                length = int.from_bytes(data[16:18], "big")
                apply_dmx(data[18:18+length], "Artnet")

    dmx_in_bytes = bytes(fx5.dmx_in.raw)
    dmx_in_changed = dmx_in_bytes != last_in_state
    last_in_state = dmx_in_bytes

    if dmx_in_changed and ARTNET_UNIVERSE_IN is not None:
        send_artnet(ARTNET_UNIVERSE_IN, dmx_in_bytes)
        print(f"[{datetime.now()}] DMX In -> Artnet sent ({len(dmx_in_bytes)} channels)")

    # sACN receivers drop a source after 2.5 seconds, so keep sending without changes too.
    now = time.monotonic()
    if SACN_UNIVERSE_IN is not None and (dmx_in_changed or now - sacn_last_sent >= SACN_KEEPALIVE):
        send_sacn(SACN_UNIVERSE_IN, dmx_in_bytes)
        sacn_last_sent = now
        if dmx_in_changed:
            print(f"[{datetime.now()}] DMX In -> sACN sent ({len(dmx_in_bytes)} channels)")
#Code with Copyright by PigcraftTV 2025



