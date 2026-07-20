#!/usr/bin/env python3
"""
rover_bridge.py -- runs on the Jetson, on the rover.

Reads the Arduino Mega over USB serial, turns its text output into the JSON
shape the Go ground station expects, and pushes it over WiFi to aresgo.

    [Mega] --USB serial--> [Jetson: this script] --WiFi/WebSocket--> [Go] --> [Browser]

Install:
    pip3 install pyserial websocket-client

Test the serial side alone first (no network needed):
    python3 rover_bridge.py --port /dev/ttyACM0 --no-ws

Then point it at the ground station:
    python3 rover_bridge.py --port /dev/ttyACM0 --server ws://192.168.1.50:8080/telemetry-in
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from typing import Any, Dict, List, Optional

import serial

try:
    import websocket  # websocket-client
except ImportError:
    websocket = None  # only needed when actually sending; --no-ws works without it


NUM_MOTORS = 5

# MPU6050 defaults: +/-2g accelerometer, +/-250 deg/s gyro. The firmware sends
# raw 16-bit counts, which are meaningless in a UI, so scale them here.
ACCEL_COUNTS_PER_G = 16384.0
GYRO_COUNTS_PER_DPS = 131.0


class Telemetry:
    """Accumulates the latest value of every field seen on the serial stream.

    The Mega interleaves three kinds of output on one port: replies to S and R,
    unsolicited raw GPS NMEA (readGPS() echoes it every loop), and DONE: lines
    when a move finishes. Rather than trying to read a clean response per
    command, every line is fed through here and recognised wherever it appears.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._arm = {
            i: {"id": i, "position": 0, "encoder": 0, "remaining": 0,
                "direction": 1, "active": False}
            for i in range(NUM_MOTORS)
        }
        self._gps = {"latitude": 0.0, "longitude": 0.0, "altitudeM": 0.0,
                     "satellites": 0, "hasFix": False}
        self._imu = {"accelX": 0.0, "accelY": 0.0, "accelZ": 0.0,
                     "gyroX": 0.0, "gyroY": 0.0, "gyroZ": 0.0}
        self._env = {"pressurePa": 0.0, "temperatureC": 0.0,
                     "soilMoisture": 0, "airSensors": []}
        self._events: List[Dict[str, Any]] = []
        self.lines_seen = 0
        self.lines_parsed = 0

    # -- feeding ----------------------------------------------------------

    def feed(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        with self._lock:
            self.lines_seen += 1
            if self._parse(line):
                self.lines_parsed += 1

    def _parse(self, line: str) -> bool:
        # Raw NMEA echoed by readGPS(). Only GGA carries fix/alt/satellites.
        if line.startswith("$") and "GGA" in line[:7]:
            return self._parse_gga(line)

        # M0:POS=800,REM=0,DIR=F,ACT=0   (reply to R)
        m = re.match(r"^M(\d+):POS=(-?\d+),REM=(-?\d+),DIR=([FR]),ACT=([01])$", line)
        if m:
            idx = int(m.group(1))
            if idx in self._arm:
                self._arm[idx].update(
                    position=int(m.group(2)),
                    remaining=int(m.group(3)),
                    direction=1 if m.group(4) == "F" else -1,
                    active=m.group(5) == "1",
                )
            return True

        # DONE:0,POS:800,ENC:1234  -- the only reliable source of encoder counts.
        m = re.match(r"^DONE:(\d+),POS:(-?\d+),ENC:(-?\d+)$", line)
        if m:
            idx = int(m.group(1))
            if idx in self._arm:
                self._arm[idx].update(position=int(m.group(2)),
                                      encoder=int(m.group(3)),
                                      remaining=0, active=False)
            self._event("info", f"Motor {idx} move complete at {m.group(2)}")
            return True

        if line.startswith("ACK:"):
            self._event("info", line)
            return True
        if line.startswith("ERR:"):
            self._event("error", line)
            return True

        # Sensor block from S.
        if line.startswith("Soil%:"):
            self._env["soilMoisture"] = _to_int(line.split(":", 1)[1])
            return True
        if line.startswith("AirRaw:"):
            self._env["airSensors"] = [_to_int(line.split(":", 1)[1])]
            return True
        if line.startswith("BMP_Pa:"):
            self._env["pressurePa"] = _to_float(line.split(":", 1)[1])
            return True
        if line.startswith("BMP_C:"):
            self._env["temperatureC"] = _to_float(line.split(":", 1)[1])
            return True
        if line.startswith("MPU Accel"):
            vals = _csv_ints(line.split(":", 1)[1], 3)
            if vals:
                self._imu.update(accelX=vals[0] / ACCEL_COUNTS_PER_G,
                                 accelY=vals[1] / ACCEL_COUNTS_PER_G,
                                 accelZ=vals[2] / ACCEL_COUNTS_PER_G)
            return True
        if line.startswith("MPU Gyro"):
            vals = _csv_ints(line.split(":", 1)[1], 3)
            if vals:
                self._imu.update(gyroX=vals[0] / GYRO_COUNTS_PER_DPS,
                                 gyroY=vals[1] / GYRO_COUNTS_PER_DPS,
                                 gyroZ=vals[2] / GYRO_COUNTS_PER_DPS)
            return True

        # Framing, banners, GPS_PPS, and the known-broken ENC: replies are
        # recognised but carry nothing we store.
        return False

    def _parse_gga(self, line: str) -> bool:
        f = line.split("*")[0].split(",")
        if len(f) < 10:
            return False
        try:
            quality = int(f[6]) if f[6] else 0
            self._gps["hasFix"] = quality > 0
            self._gps["satellites"] = int(f[7]) if f[7] else 0
            if f[9]:
                self._gps["altitudeM"] = float(f[9])
            lat = _nmea_degrees(f[2], f[3])
            lon = _nmea_degrees(f[4], f[5])
            if lat is not None:
                self._gps["latitude"] = lat
            if lon is not None:
                self._gps["longitude"] = lon
        except (ValueError, IndexError):
            return False
        return True

    def _event(self, level: str, message: str) -> None:
        self._events.append({"timestamp": int(time.time() * 1000),
                             "level": level, "message": message})

    # -- reading ----------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Build one packet. Drains the event list, because the Go side
        accumulates logs itself and resending them would duplicate entries."""
        with self._lock:
            events, self._events = self._events, []
            return {
                # SEW drive motors are on EtherCAT, not on the Mega, so this
                # bridge has nothing to report for them yet.
                "driveMotors": [],
                "armJoints": [dict(j) for j in self._arm.values()],
                "gps": dict(self._gps),
                "imu": dict(self._imu),
                "environment": dict(self._env, airSensors=list(self._env["airSensors"])),
                "eventLog": events,
                "verboseLog": [],
                "timestamp": int(time.time() * 1000),
            }


def _to_int(s: str) -> int:
    try:
        return int(float(s.strip()))
    except ValueError:
        return 0


def _to_float(s: str) -> float:
    try:
        return float(s.strip())
    except ValueError:
        return 0.0


def _csv_ints(s: str, count: int) -> Optional[List[int]]:
    parts = s.split(",")
    if len(parts) < count:
        return None
    try:
        return [int(p.strip()) for p in parts[:count]]
    except ValueError:
        return None


def _nmea_degrees(value: str, hemisphere: str) -> Optional[float]:
    """NMEA gives ddmm.mmmm; convert to signed decimal degrees."""
    if not value or not hemisphere:
        return None
    try:
        raw = float(value)
    except ValueError:
        return None
    degrees = int(raw // 100)
    minutes = raw - degrees * 100
    result = degrees + minutes / 60.0
    return -result if hemisphere in ("S", "W") else result


def serial_reader(ser: serial.Serial, tel: Telemetry, stop: threading.Event) -> None:
    """Continuously drains the serial port. Runs in its own thread so that
    unsolicited GPS and DONE: lines are never missed while the main thread
    is busy with the network."""
    while not stop.is_set():
        try:
            raw = ser.readline()
        except serial.SerialException as exc:
            print(f"[serial] read failed: {exc}", file=sys.stderr)
            stop.set()
            return
        if raw:
            tel.feed(raw.decode("utf-8", errors="replace"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Rover telemetry bridge (Jetson -> Go)")
    ap.add_argument("--port", default="/dev/ttyACM0", help="serial port of the Mega")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--server", default="ws://localhost:8080/telemetry-in",
                    help="aresgo telemetry-in WebSocket URL")
    ap.add_argument("--interval", type=float, default=0.5,
                    help="seconds between polls/sends (default 0.5)")
    ap.add_argument("--no-ws", action="store_true",
                    help="print packets instead of sending; use to test serial alone")
    args = ap.parse_args()

    if not args.no_ws and websocket is None:
        print("websocket-client not installed. Run: pip3 install websocket-client",
              file=sys.stderr)
        return 1

    print(f"[serial] opening {args.port} at {args.baud}")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.2)
    except serial.SerialException as exc:
        print(f"[serial] could not open {args.port}: {exc}", file=sys.stderr)
        return 1

    time.sleep(2.0)  # Mega resets when the port opens; wait for its banner.
    ser.reset_input_buffer()

    tel = Telemetry()
    stop = threading.Event()
    reader = threading.Thread(target=serial_reader, args=(ser, tel, stop), daemon=True)
    reader.start()

    try:
        if args.no_ws:
            run_print_only(ser, tel, args, stop)
        else:
            run_forwarding(ser, tel, args, stop)
    except KeyboardInterrupt:
        print("\n[bridge] stopping")
    finally:
        stop.set()
        ser.close()
    return 0


def poll(ser: serial.Serial) -> None:
    """Ask the Mega for sensors (S) and motor status (R)."""
    ser.write(b"S\n")
    ser.write(b"R\n")
    ser.flush()


def run_print_only(ser, tel, args, stop) -> None:
    print("[bridge] --no-ws: printing packets, not sending. Ctrl-C to stop.")
    while not stop.is_set():
        poll(ser)
        time.sleep(args.interval)
        packet = tel.snapshot()
        print(json.dumps(packet, indent=2))
        print(f"[bridge] serial lines seen={tel.lines_seen} parsed={tel.lines_parsed}")


def run_forwarding(ser, tel, args, stop) -> None:
    """Connect to Go and stream packets, reconnecting whenever the long-range
    WiFi link drops. Mirrors the browser-side reconnect loop in useWebSocket.ts."""
    backoff = 1.0
    sent = 0
    while not stop.is_set():
        try:
            print(f"[ws] connecting to {args.server}")
            ws = websocket.create_connection(args.server, timeout=5)
            print("[ws] connected")
            backoff = 1.0
            while not stop.is_set():
                poll(ser)
                time.sleep(args.interval)
                ws.send(json.dumps(tel.snapshot()))
                sent += 1
                if sent % 20 == 0:
                    print(f"[ws] sent {sent} packets "
                          f"(serial lines seen={tel.lines_seen} parsed={tel.lines_parsed})")
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"[ws] link down ({exc}); retrying in {backoff:.0f}s", file=sys.stderr)
            time.sleep(backoff)
            backoff = min(backoff * 2, 15.0)  # cap so recovery stays quick


if __name__ == "__main__":
    raise SystemExit(main())
