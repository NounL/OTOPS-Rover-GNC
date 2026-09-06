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
ADAPTER = "enx00249b8d4d1a"

UDP_HOST = "0.0.0.0"
UDP_PORT = 5999
COMMAND_TIMEOUT_S = 0.4  # no valid packet within this window -> motors forced to 0
HEARTBEAT_INTERVAL_S = 10.0  # while a diagnostic problem persists, re-announce it at this cadence


master = pysoem.Master()
running = True #used in threading

MAX_RPM = 4000 #Physical Limit of our Motors

motor_rpm = [0, 0, 0, 0]


# motor_rpm is now written by udp_listener_thread and read by
# processdata_thread, so both need to agree on the current value
# through a lock instead of racing on a bare global list.
motor_rpm_lock = threading.Lock()
last_command_time = 0.0

# ------------------------------------------------------------------
# Diagnostics-only state, read/written by diagnostics_thread() below.
# None of this feeds back into motor control - it exists purely so an
# operator can tell *why* the rover isn't moving:
#   last_packet_seen_time  - set on ANY UDP datagram, valid or not
#                             (distinguishes "nothing is arriving" from
#                             "stuff is arriving but rejected")
#   udp_packet_count        - total datagrams received
#   udp_malformed_count     - datagrams that failed to parse as a
#                             ControlState packet
#   last_wkc                - most recent actual EtherCAT working
#                             counter, compared against master.expected_wkc
#                             to catch bus-level communication problems
# ------------------------------------------------------------------
last_packet_seen_time = 0.0
udp_packet_count = 0
udp_malformed_count = 0
last_wkc = 0

# Set once udp_listener_thread successfully binds its socket. Lets main()
# tell the difference between "the listener is genuinely up" and "the thread
# died on startup" instead of unconditionally printing a ready message that
# was true before but may not be anymore (see the Address-already-in-use bug).
udp_bound_event = threading.Event()


#creates a thread to send and receive process data continuously at a fixed interval
def processdata_thread():
    global running, last_wkc

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
        # Recorded for diagnostics_thread() to compare against master.expected_wkc.
        last_wkc = master.receive_processdata(10000)

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
    global running, last_command_time, last_packet_seen_time, udp_packet_count, udp_malformed_count

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Lets this bind succeed promptly after a previous instance of this
    # script exits, instead of occasionally colliding with a socket still
    # winding down. Does NOT let two live processes both receive traffic -
    # it will not mask another process actively holding this port right now.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((UDP_HOST, UDP_PORT))
    except OSError as bind_err:
        # This used to be an unhandled exception: it killed this thread only,
        # while the rest of the script (EtherCAT, diagnostics, the main loop)
        # kept running and printed a "ready" message that was no longer true.
        # Fail loudly and shut the whole script down instead of pretending
        # to be operational with a dead command listener.
        print(f"[udp] FATAL: could not bind {UDP_HOST}:{UDP_PORT}: {bind_err}")
        print(f"[udp] something else already has this port. Find it with: sudo ss -ulpn | grep {UDP_PORT}")
        running = False
        return
    sock.settimeout(0.5)  # lets the loop notice `running` going False and exit

    udp_bound_event.set()
    print(f"[udp] listening on {UDP_HOST}:{UDP_PORT}")

    while running:
        try:
            data, _addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        except OSError:
            break

        # Recorded on every datagram, valid or not - this is what tells
        # diagnostics_thread() the difference between "nothing is reaching
        # this socket at all" and "packets are arriving but being rejected".
        last_packet_seen_time = time.time()
        udp_packet_count += 1

        try:
            packet = json.loads(data.decode("utf-8"))
            drive = packet["drive"]
            linear_velocity = float(drive["linear_velocity"])
            angular_velocity = float(drive["angular_velocity"])
            speed_scale = float(packet["speed_scale"])
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            udp_malformed_count += 1
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
            # Physical side confirmed on real hardware: motors 0 & 1 = right
            # side, motors 2 & 3 = left side (NOT the 0&2 / 1&3 grouping
            # inherited from the old keyboard controls - that grouping was
            # wrong and would have mixed up left/right target speeds during
            # a turn, even though it looked fine driving straight since
            # left == right whenever angular_velocity is 0).
            # Sign per motor confirmed empirically by driving the rover and
            # observing which wheels moved backwards - motors 0 and 2 need
            # their commanded RPM negated to spin the correct physical
            # direction, motors 1 and 3 do not.
            motor_rpm[0] = -right
            motor_rpm[1] = right
            motor_rpm[2] = -left
            motor_rpm[3] = left
            last_command_time = time.time()

    sock.close()
    print("[udp] listener stopped")


# ------------------------------------------------------------------
# Diagnostics thread. Read-only with respect to motor control - it never
# touches motor_rpm or master.slaves[i].output, it only reads state written
# by the other two threads and prints operator-facing warnings that explain
# *why* the rover isn't responding. Distinguishes three distinct failure
# points along the pipeline, checked every 0.5s and reported on change:
#   1. No UDP traffic is reaching this socket at all (network problem -
#      wrong IP/port, firewall, sender not running).
#   2. UDP traffic is arriving but failing to parse into a valid drive
#      command (payload shape/JSON key mismatch).
#   3. Valid drive commands are being applied to motor_rpm, but they
#      aren't making it to the physical motors (EtherCAT working counter
#      degraded, or a drive reporting fault/not-ready/STO-not-ok while
#      being commanded to move).
# ------------------------------------------------------------------
def diagnostics_thread():
    global running

    udp_arriving = None       # None = not yet evaluated (startup grace period)
    udp_parsing = None
    motors_responding = None

    # Last time each category printed anything, used to re-announce a
    # persisting problem every HEARTBEAT_INTERVAL_S instead of going silent
    # forever after the first warning (last_*_time == 0.0 at startup means
    # "never happened yet", not "0 seconds ago" - handled explicitly below).
    last_arriving_print = 0.0
    last_parsing_print = 0.0
    last_motors_print = 0.0

    while running:
        time.sleep(0.5)

        now = time.time()

        # ---- 1. Is any UDP traffic reaching the socket at all? ----
        arriving_now = last_packet_seen_time > 0 and (now - last_packet_seen_time) <= COMMAND_TIMEOUT_S
        if arriving_now != udp_arriving or (not arriving_now and now - last_arriving_print >= HEARTBEAT_INTERVAL_S):
            if arriving_now:
                print(f"[diag] UDP traffic detected on {UDP_HOST}:{UDP_PORT} "
                      f"({udp_packet_count} packet(s) seen so far)")
            else:
                since_desc = f"{now - last_packet_seen_time:.1f}s ago" if last_packet_seen_time > 0 else "since startup"
                print(f"[diag] WARNING: no UDP packets of any kind received ({since_desc}) "
                      f"on {UDP_HOST}:{UDP_PORT}. Check the sender is running and can reach "
                      f"this host/port (firewall, wrong IP, wrong port).")
            udp_arriving = arriving_now
            last_arriving_print = now

        # ---- 2. Is that traffic parsing into valid drive commands? ----
        if arriving_now:
            parsing_now = last_command_time > 0 and (now - last_command_time) <= COMMAND_TIMEOUT_S
            if parsing_now != udp_parsing or (not parsing_now and now - last_parsing_print >= HEARTBEAT_INTERVAL_S):
                if parsing_now:
                    print("[diag] UDP packets are parsing into valid drive commands")
                else:
                    print(f"[diag] WARNING: receiving UDP packets but none have parsed "
                          f"into a valid drive command recently "
                          f"({udp_malformed_count} malformed packet(s) so far this run). "
                          f"Check the sender's JSON matches the expected "
                          "{'drive': {'linear_velocity', 'angular_velocity'}, 'speed_scale'} shape.")
                udp_parsing = parsing_now
                last_parsing_print = now
        else:
            udp_parsing = None  # re-evaluate once traffic resumes

        # ---- 3. Are valid commands actually reaching the physical motors? ----
        wkc_ok = last_wkc >= master.expected_wkc
        with motor_rpm_lock:
            commanded = list(motor_rpm)

        slave_problems = []
        for i, s in enumerate(master.slaves):
            try:
                pi1 = struct.unpack_from("<H", bytes(s.input), 0)[0]
            except Exception:
                continue
            ready = bool(pi1 & (1 << 0))
            output_enabled = bool(pi1 & (1 << 1))
            fault = bool(pi1 & (1 << 4))
            sto_ok = bool(pi1 & (1 << 8))
            commanding_motion = abs(commanded[i]) > 0
            if fault or (commanding_motion and not (ready and output_enabled and sto_ok)):
                slave_problems.append(
                    f"motor {i} (commanded {commanded[i]:.0f} RPM): "
                    f"ready={ready} output_enabled={output_enabled} fault={fault} sto_ok={sto_ok}"
                )

        responding_now = wkc_ok and not slave_problems
        if responding_now != motors_responding or (not responding_now and now - last_motors_print >= HEARTBEAT_INTERVAL_S):
            if responding_now:
                print("[diag] EtherCAT link to motors OK - WKC nominal, all commanded drives ready")
            else:
                if not wkc_ok:
                    print(f"[diag] WARNING: EtherCAT working counter degraded "
                          f"(actual={last_wkc}, expected={master.expected_wkc}) - "
                          f"process data may not be reaching all slaves every cycle.")
                for line in slave_problems:
                    print(f"[diag] WARNING: {line} - this drive will not move even "
                          f"though a command is being sent to it.")
            motors_responding = responding_now
            last_motors_print = now


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

# start the diagnostics thread (UDP reception + motor forwarding health checks).
diag_thread = threading.Thread(target=diagnostics_thread, daemon=True)
diag_thread.start()

time.sleep(0.5)

# Only claim to be ready if udp_listener_thread actually got its socket bound -
# previously this printed unconditionally even if that thread had already
# died on startup (e.g. OSError: Address already in use).
if udp_bound_event.wait(timeout=2.0):
    print(f"[main] ready - listening for drive commands on udp {UDP_HOST}:{UDP_PORT}")
else:
    print("[main] WARNING: UDP command listener did not start - motors will "
          "never receive drive commands. Check the [udp] FATAL message above.")

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
    diag_thread.join(timeout=1)

    master.state = pysoem.INIT_STATE
    master.write_state()
    master.close()

    print("Closed adapter.")
