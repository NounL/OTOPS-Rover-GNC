from ast import If

import pysoem
import struct
import time
import threading
import socket
import json
import signal


# Configuration

# ------------------------------------------------------------------
# this used to be a Windows Npcap adapter GUID. On the Jetson
# this must be the Linux interface name for the USB-to-Ethernet
# adapter wired to the SEW EtherCAT chain. Find it with `ip link show`
# then set it here.
# ------------------------------------------------------------------
ADAPTER = "CHANGE_ME_TO_LINUX_INTERFACE_NAME"

UDP_HOST = "0.0.0.0"
UDP_PORT = 5999
COMMAND_TIMEOUT_S = 0.4  # no valid packet within this window -> motors forced to 0


master = pysoem.Master()
running = True #used in threading

MAX_RPM = 4000 #Physical Limit of our Motors

motor_rpm = [0, 0, 0, 0]


# motor_rpm is now written by udp_listener_thread and read by
# processdata_thread, so both need to agree on the current value
# through a lock instead of racing on a bare global list.
motor_rpm_lock = threading.Lock()
last_command_time = 0.0


#creates a thread to send and receive process data continuously at a fixed interval
def processdata_thread():
    global running

    while running:

        # If no valid UDP command has been
        # received recently (link dropped, sender crashed, etc.),
        # force every motor to 0 
        with motor_rpm_lock:
            if time.time() - last_command_time > COMMAND_TIMEOUT_S:
                current_rpm = [0, 0, 0, 0]
            else:
                current_rpm = list(motor_rpm)
        # --------------------------------------------------------

        for i in range(4):
            master.slaves[i].output = make_cmd(
                current_rpm[i]
            )

        master.send_processdata()
        master.receive_processdata(10000)

        time.sleep(0.005)

motor_data = []

for _ in range(4):
    motor_data.append({
        "target_rpm": 0,
        "actual_rpm": 0,
        "current_a": 0.0,
        "pi1": 0,
        "pi2": 0,
        "pi3": 0,
        "fault": False,
        "warning": False,
        "ready": False,
        "output_enabled": False,
        "sto_ok": False,
        "fcb": 0,
        "raw_pi": [0]*16
    })

# Function to control the RPM of the motors based on RPM values and send the appropriate commands to the slaves. 
# It also handles user input to adjust the RPMs in real-time.
def make_cmd(rpm):
    data = bytearray(32)

    # PO1
    struct.pack_into("<H", data, 0, 0x0083)

    # PO2
    struct.pack_into("<h", data, 2, int(rpm))

    # PO3
    struct.pack_into("<H", data, 4, 1000)

    # PO4
    struct.pack_into("<H", data, 6, 1000)

    # PO5
    struct.pack_into("<H", data, 8, 1)

    return bytes(data)

#Stop the Motors
def make_stop():
    data = bytearray(32)
    struct.pack_into("<H", data, 0, 0x0000)
    return bytes(data)


# UDP listener thread. Receives the ControlState JSON packets
# sent ~60x/sec by aresgo (see aresgo/internal/model/control.go),
# applies "drive" to the motors, and ignores arm (those
# fields are for the Mega's steppers, not the SEW EtherCAT drives).
def udp_listener_thread():
    global running, last_command_time

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_HOST, UDP_PORT))
    sock.settimeout(0.5)  # lets the loop notice `running` going False and exit

    print(f"[udp] listening on {UDP_HOST}:{UDP_PORT}")

    while running:
        try:
            data, _addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except OSError:
            break

        try:
            packet = json.loads(data.decode("utf-8"))
            drive = packet["drive"]
            linear_velocity = float(drive["linear_velocity"])
            angular_velocity = float(drive["angular_velocity"])
            speed_scale = float(packet["speed_scale"])
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            # Malformed/partial packet - drop it and keep listening.
            continue

        # Defensive clamp on the inputs themselves, independent of the
        # RPM clamp below - a bad/spoofed sender should never be able
        # to request more than full scale in either direction.
        linear_velocity = max(-1.0, min(1.0, linear_velocity))
        angular_velocity = max(-1.0, min(1.0, angular_velocity))
        speed_scale = max(0.0, min(1.0, speed_scale))

        # Differential drive: left/right RPM from linear + angular velocity.
        left = (linear_velocity - angular_velocity) * speed_scale * MAX_RPM
        right = (linear_velocity + angular_velocity) * speed_scale * MAX_RPM

        # Re-implements the RPM clamp that used to live in the keyboard loop.
        left = max(-MAX_RPM, min(MAX_RPM, left))
        right = max(-MAX_RPM, min(MAX_RPM, right))

        with motor_rpm_lock:
            # Left/right grouping kept as-is from the old keyboard controls:
            # motors 0 & 2 = left side, motors 1 & 3 = right side.
            motor_rpm[0] = left
            motor_rpm[2] = left
            motor_rpm[1] = right
            motor_rpm[3] = right
            last_command_time = time.time()

    sock.close()
    print("[udp] listener stopped")


def handle_shutdown_signal(signum, frame):
    global running
    print(f"\n[main] received signal {signum}, shutting down...")
    running = False

signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)
# ------------------------------------------------------------------

''' Main program starts here'''


# Establish Connection to the EtherCAT network by opening the specified adapter and configuring the master and slaves. 
print("Opening adapter...")

master.open(ADAPTER)

print("Adapter opened!")


#See amount of Slaves found and print it out
num = master.config_init()
if num <= 0:
    raise RuntimeError("No slaves found.")

print(f"Found {num} slave(s).")

# Map the process data for each slave and set up watchdog timers to ensure that the slaves are responsive.
iomap = master.config_map()
print("IO map size:", iomap)

# for each loop to set watchdog timers for each slave, 
# which will trigger if the master fails to send process data within the specified time interval.
for s in master.slaves:
    try:
        s.set_watchdog("processdata", 1000.0)
    except:
        pass


#if the master successfully reaches the SAFEOP state, 
# it will proceed to send valid process data to the slaves before requesting the OP state.
#Ensure Movisuite is Closed
if master.state_check(pysoem.SAFEOP_STATE,500000) != pysoem.SAFEOP_STATE:
    raise RuntimeError("SAFEOP failed")

# Send valid PDOs before OP
for _ in range(200):
    for s in master.slaves:
        s.output = bytes(len(s.output))

    master.send_processdata()
    master.receive_processdata(10000)
    time.sleep(0.005)

# Request OP
master.state = pysoem.OP_STATE
master.write_state()

for _ in range(200):
    master.send_processdata()
    master.receive_processdata(10000)
    for i, s in enumerate(master.slaves):

        pi = struct.unpack("<16H", bytes(s.input))

        motor_data[i]["raw_pi"] = list(pi)

        motor_data[i]["pi1"] = pi[0]
        motor_data[i]["pi2"] = pi[1]
        motor_data[i]["pi3"] = pi[2]

        #
        # Actual RPM
        #
        motor_data[i]["actual_rpm"] = \
            struct.unpack_from("<h", s.input, 2)[0]

        #
        # Current
        #
        # Adjust scaling if necessary
        #
        motor_data[i]["current_a"] = \
            pi[2] / 10.0

        #
        # Decode status bits
        #
        pi1 = pi[0]

        motor_data[i]["ready"] = bool(pi1 & (1 << 0))
        motor_data[i]["output_enabled"] = bool(pi1 & (1 << 1))
        motor_data[i]["warning"] = bool(pi1 & (1 << 3))
        motor_data[i]["fault"] = bool(pi1 & (1 << 4))
        motor_data[i]["sto_ok"] = bool(pi1 & (1 << 8))

        motor_data[i]["fcb"] = \
            (pi1 >> 10) & 0x07

    master.read_state()

    if all(
            s.state == pysoem.OP_STATE
            for s in master.slaves
    ):
        break

    time.sleep(0.005)

master.read_state()


for i, s in enumerate(master.slaves):

    pi1 = struct.unpack_from("<H", s.input, 0)[0]

    ready = bool(pi1 & (1 << 0))
    output_enabled = bool(pi1 & (1 << 1))
    sto_ok = bool(pi1 & (1 << 8))

    print(
        f"Motor {i}: "
        f"Ready={ready} "
        f"Output={output_enabled} "
        f"STO={sto_ok}"
    )

if not all(
        s.state == pysoem.OP_STATE
        for s in master.slaves
):
    raise RuntimeError("Not all slaves reached OP.")

print("Reached OP!")
print("Expected WKC:", master.expected_wkc)

# Start cyclic PDO thread
t = threading.Thread(target=processdata_thread,daemon=True)
t.start()

# start the UDP command listener thread.
udp_thread = threading.Thread(target=udp_listener_thread, daemon=True)
udp_thread.start()

time.sleep(0.5)

# replaces the old keyboard `while True: keyboard.is_pressed(...)`
# loop. There's no interactive input anymore - this just keeps the
# process alive while processdata_thread and udp_listener_thread do
# the real work, until a signal (Ctrl-C / service stop) flips `running`
# to False. The `finally` block below used to pair with a `try` that
# contained the keyboard loop; that pairing is preserved here.
print(f"[main] ready - listening for drive commands on udp {UDP_HOST}:{UDP_PORT}")

try:
    while running:
        time.sleep(0.1)
finally:

    print("\nStopping motors...")

    stop = make_stop()

    for s in master.slaves:
        s.output = stop

    time.sleep(1)

    running = False
    t.join(timeout=1)
    udp_thread.join(timeout=1)

    master.state = pysoem.INIT_STATE
    master.write_state()
    master.close()

    print("Closed adapter.")
