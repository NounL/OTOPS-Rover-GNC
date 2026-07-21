# Simulating the Arduino on the Jetson (no hardware needed)

**Goal:** test the real, unmodified `rover_bridge.py` end-to-end — serial parsing
and the WebSocket push to Go — without a physical Arduino. We do this by creating
a fake serial port pair and writing Arduino-shaped text into one end, while
`rover_bridge.py` reads the other end exactly like it would `/dev/ttyACM0`.

Nothing about `rover_bridge.py` is modified or mocked. Only the "Arduino" is fake.

```
[fake_arduino.py] --writes text--> /tmp/fake_arduino <==socat==> /tmp/fake_jetson_port <--rover_bridge.py reads
```

---

## Step 1 — Install socat (one time)

```bash
sudo apt install socat
```

## Step 2 — Create the virtual serial pair

Open a terminal (or `tmux` session — recommended so it survives SSH drops) and run:

```bash
socat -d -d pty,raw,echo=0,link=/tmp/fake_arduino pty,raw,echo=0,link=/tmp/fake_jetson_port
```

Leave this running. It should print two lines confirming both PTY paths were created.
This process must stay alive for the whole test — it's the "virtual USB cable."

## Step 3 — Create the fake Arduino script

Save this as `fake_arduino.py` on the Jetson (same folder as `rover_bridge.py` is fine):

```python
#!/usr/bin/env python3
"""
fake_arduino.py -- pretends to be the Mega for testing rover_bridge.py.

Listens on the /tmp/fake_arduino end of the socat pair, replies to S/R/ENC/M
commands in the exact text format the real firmware would use, and echoes
unsolicited GPS NMEA lines every loop (matching the real firmware's behavior).

Usage:
    python3 fake_arduino.py --port /tmp/fake_arduino
"""
import argparse
import random
import time
import threading

import serial


def gga_line():
    # Fake but well-formed GGA sentence: lat/lon in NMEA ddmm.mmmm format.
    lat = 4380.1234 + random.uniform(-0.001, 0.001)
    lon = 07890.5678 + random.uniform(-0.001, 0.001)
    sats = random.randint(6, 12)
    alt = 150.0 + random.uniform(-1, 1)
    return f"$GPGGA,123519,{lat:.4f},N,{lon:.4f},W,1,{sats:02d},0.9,{alt:.1f},M,0.0,M,,*47"


def gps_echo_loop(ser, stop):
    while not stop.is_set():
        ser.write((gga_line() + "\n").encode())
        time.sleep(1.0)


def handle_command(ser, line, motor_state):
    line = line.strip()
    if not line:
        return

    if line == "S":
        ser.write(f"Soil%:{random.randint(20, 60)}\n".encode())
        ser.write(f"AirRaw:{random.randint(100, 400)}\n".encode())
        ser.write(f"BMP_Pa:{101300 + random.uniform(-50, 50):.1f}\n".encode())
        ser.write(f"BMP_C:{22.0 + random.uniform(-1, 1):.1f}\n".encode())
        ser.write(f"MPU Accel X,Y,Z:{random.randint(-500,500)},{random.randint(-500,500)},{16384+random.randint(-200,200)}\n".encode())
        ser.write(f"MPU Gyro  X,Y,Z:{random.randint(-50,50)},{random.randint(-50,50)},{random.randint(-50,50)}\n".encode())
        return

    if line == "R":
        for i in range(5):
            st = motor_state[i]
            d = "F" if st["direction"] >= 1 else "R"
            ser.write(f"M{i}:POS={st['position']},REM={st['remaining']},DIR={d},ACT={1 if st['active'] else 0}\n".encode())
        return

    if line == "ENC":
        # Deliberately reproduce the REAL firmware bug: ENC ALL omits ids.
        vals = ",".join(str(motor_state[i]["encoder"]) for i in range(5))
        ser.write(f"ENC:{vals}\n".encode())
        return

    if line.startswith("ENC,"):
        # Also reproduce the real bug: single-motor reply has no id either.
        ser.write(b"ENC:,0\n")
        return

    if line == "!":
        for st in motor_state.values():
            st["active"] = False
            st["remaining"] = 0
        ser.write(b"ACK:ESTOP\n")
        return

    m = line.split(",")
    if len(m) == 4 and m[0] == "M":
        try:
            idx, direction, steps = int(m[1]), int(m[2]), int(m[3])
        except ValueError:
            ser.write(b"ERR: unknown command\n")
            return
        if idx not in motor_state:
            ser.write(b"ERR: unknown command\n")
            return
        ser.write(b"ACK:\n")
        st = motor_state[idx]
        st["direction"] = direction
        st["remaining"] = steps
        st["active"] = True

        def finish(idx=idx, steps=steps, direction=direction):
            time.sleep(0.8)
            st = motor_state[idx]
            st["position"] += steps if direction >= 1 else -steps
            st["encoder"] = st["position"]
            st["remaining"] = 0
            st["active"] = False
            ser.write(f"DONE:{idx},POS:{st['position']},ENC:{st['encoder']}\n".encode())

        threading.Thread(target=finish, daemon=True).start()
        return

    ser.write(b"ERR: unknown command\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/tmp/fake_arduino")
    ap.add_argument("--baud", type=int, default=115200)
    args = ap.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.2)
    print(f"[fake_arduino] listening on {args.port}")

    motor_state = {i: {"id": i, "position": 0, "encoder": 0, "remaining": 0,
                        "direction": 1, "active": False} for i in range(5)}

    stop = threading.Event()
    threading.Thread(target=gps_echo_loop, args=(ser, stop), daemon=True).start()

    buf = b""
    try:
        while True:
            chunk = ser.read(1)
            if not chunk:
                continue
            buf += chunk
            if buf.endswith(b"\n"):
                handle_command(ser, buf.decode(errors="replace"), motor_state)
                buf = b""
    except KeyboardInterrupt:
        print("\n[fake_arduino] stopping")
    finally:
        stop.set()
        ser.close()


if __name__ == "__main__":
    main()
```

Install its one dependency (same as `rover_bridge.py` needs):
```bash
pip3 install pyserial
```

## Step 4 — Run the fake Arduino (second terminal / tmux pane)

```bash
python3 fake_arduino.py --port /tmp/fake_arduino
```

Leave this running too. It'll sit quietly, replying only when polled.

## Step 5 — Run the real rover_bridge.py against the fake port (third terminal / tmux pane)

First, test serial parsing alone — **no network needed**:
```bash
python3 rover_bridge.py --port /tmp/fake_jetson_port --no-ws
```

You should see JSON print every ~0.5s with real-looking values, and
`serial lines seen=X parsed=Y` where `parsed` is going up and roughly keeping
pace with `seen`. If `parsed=0`, something in the fake Arduino's text format
doesn't match what the parser expects — copy the printed error/packet and we'll
debug it.

**This step alone proves the entire parsing pipeline is correct**, independent
of any real hardware ever showing up.

## Step 6 — Once you have the GNC laptop, forward it over the network

Get the laptop's IP (`ipconfig` on Windows). On the laptop, start Go **without**
`-mock`:
```bash
cd aresgo
go run .
```

On the Jetson, point the bridge at the real Go server instead of printing locally:
```bash
python3 rover_bridge.py --port /tmp/fake_jetson_port --server ws://<laptop-ip>:8080/telemetry-in
```

You should see `[ws] connected` on the Jetson and `telemetry-in: rover bridge
connected` in the Go server's logs. Open `http://<laptop-ip>:5173/data` (or
`localhost:5173/data` on the laptop itself) — the Data UI should show live,
changing values and a green link indicator.

If it can't connect, it's almost always the laptop firewall blocking port 8080:
```powershell
New-NetFirewallRule -DisplayName "aresgo" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

---

## Recap: what this does and doesn't prove

**Proves:**
- `rover_bridge.py`'s parser is correct against the documented serial protocol
- The full chain Jetson → Go `/telemetry-in` → `/telemetry` → Data UI works over
  a real network link, with real (simulated) packets, not `-mock`

**Doesn't prove:**
- Anything about the real Arduino/firmware, since it isn't flashed or wired yet
- Anything about the SEW/EtherCAT drive motors (separate integration,
  `driveMotors` stays empty either way)

When the real Arduino is finally flashed and connected tomorrow, the only thing
that changes is the `--port` flag — swap `/tmp/fake_jetson_port` for the real
`/dev/ttyACM0`. Everything downstream is already proven.

## Cleanup

Ctrl-C all three processes (fake_arduino, socat, rover_bridge). The `/tmp/fake_arduino`
and `/tmp/fake_jetson_port` symlinks disappear when socat exits.
