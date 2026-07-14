import pysoem
import struct
import time
import threading
import keyboard

# Configuration

#Windows ASIX adapter name 
ADAPTER = r"\Device\NPF_{4C4F1C80-D6FF-4175-8AE3-05DFE9FB0CA2}" 

master = pysoem.Master()
running = True #used in threading

# Current commanded RPMs
left_rpm = 0
right_rpm = 0

RPM_STEP = 200
MAX_RPM = 4000 #Physical Limit of our Motors

motor_rpm = [0, 0, 0, 0]

#creates a thread to send and receive process data continuously at a fixed interval
def processdata_thread():
    global running
    global motor_rpm

    while running:

        for i in range(4):
            master.slaves[i].output = make_cmd(
                motor_rpm[i]
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

time.sleep(0.5)

print("""
Controls:
W = Forward
S = Reverse
A = Left Turn
D = Right Turn
Q = Pivot Left
E = Pivot Right
SPACE = Stop
ESC = Exit
""")

try:
    while True:

        if keyboard.is_pressed("w"):
            left_rpm += RPM_STEP
            right_rpm += RPM_STEP
            time.sleep(0.15)

        elif keyboard.is_pressed("s"):
            left_rpm -= RPM_STEP
            right_rpm -= RPM_STEP
            time.sleep(0.15)

        elif keyboard.is_pressed("a"):
            left_rpm -= RPM_STEP
            right_rpm += RPM_STEP
            time.sleep(0.15)

        elif keyboard.is_pressed("d"):
            left_rpm += RPM_STEP
            right_rpm -= RPM_STEP
            time.sleep(0.15)

        elif keyboard.is_pressed("q"):
            left_rpm = -200
            right_rpm = 200
            time.sleep(0.15)

        elif keyboard.is_pressed("e"):
            left_rpm = 200
            right_rpm = -200
            time.sleep(0.15)

        elif keyboard.is_pressed("space"):
            left_rpm = 0
            right_rpm = 0
            time.sleep(0.15)

        elif keyboard.is_pressed("esc"):
            break

        # Limit RPM
        left_rpm = max(-MAX_RPM, min(MAX_RPM, left_rpm))
        right_rpm = max(-MAX_RPM, min(MAX_RPM, right_rpm))

        # Update desired speeds only
        motor_rpm[0] = left_rpm
        motor_rpm[1] = right_rpm
        motor_rpm[2] = left_rpm
        motor_rpm[3] = right_rpm

        for i in range(4):

            m = motor_data[i]
            r = motor_rpm[i]

            print(
                f"--------------------------------\n"
                f"Motor {i} | "
                f"Target: {r['target_rpm']:5d} rpm | "
                f"Actual: {r['actual_rpm']:5d} rpm | "
                f"Current: {m['current_a']:5.1f} A | "
                f"Fault: {'YES' if m['fault'] else 'NO'} | "
                f"Warning: {'YES' if m['warning'] else 'NO'} | "
                f"Ready: {'YES' if m['ready'] else 'NO'} | "
                f"Output: {'YES' if m['output_enabled'] else 'NO'} | "
                f"STO: {'YES' if m['sto_ok'] else 'NO'} | "
                f"FCB: {m['fcb']}"
        )

        time.sleep(0.02)

finally:

    print("\nStopping motors...")

    stop = make_stop()

    for s in master.slaves:
        s.output = stop

    time.sleep(1)

    running = False
    t.join(timeout=1)

    master.state = pysoem.INIT_STATE
    master.write_state()
    master.close()

    print("Closed adapter.")