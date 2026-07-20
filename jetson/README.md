# Jetson Telemetry Bridge

Runs **on the Jetson, on the rover**. Reads the Arduino Mega over USB serial and
pushes telemetry over WiFi to the `aresgo` ground station.

```
[Mega] --USB serial--> [Jetson: rover_bridge.py] --WiFi--> [Go :8080] --> [Browser]
```

This whole folder is self-contained. To remove it from the repo: `rm -rf jetson/`

## Copy it to the Jetson

From your laptop:

```bash
scp jetson/rover_bridge.py <user>@<jetson-ip>:~/
```

Or just open the file and paste it into `nano rover_bridge.py` over RustDesk.

## One-time setup on the Jetson

```bash
pip3 install pyserial websocket-client
```

Find which port the Mega is on — plug it in and check:

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

Usually `/dev/ttyACM0`. If you get a permission error opening it:

```bash
sudo usermod -a -G dialout $USER    # then log out and back in
```

## Step 1 — test the serial side alone (do this first)

No network, no Go server needed. This proves the Jetson can read the Arduino and
build correct JSON before you add the WiFi hop:

```bash
python3 rover_bridge.py --port /dev/ttyACM0 --no-ws
```

You should see a JSON packet printed every half second, plus a line like
`serial lines seen=21 parsed=15`. Check that the numbers actually move when you
touch a sensor. If `parsed=0`, the script is connected but the Arduino isn't
replying — check the port and that the firmware is flashed.

## Step 2 — send it to the ground station

Find the ground station laptop's IP (on the laptop: `ipconfig` on Windows,
`ip addr` on Linux). Then on the Jetson:

```bash
python3 rover_bridge.py --port /dev/ttyACM0 --server ws://<laptop-ip>:8080/telemetry-in
```

You should see `[ws] connected`, then `[ws] sent 20 packets` every ~10s.
On the laptop, the Go server logs `telemetry-in: rover bridge connected`, and
the Data UI at <http://localhost:5173/data> shows live values with the link
indicator green.

**The ground station must be running first** (`cd aresgo && go run .` — no
`-mock`, or fake data will overwrite the real feed). See [RUNNING.md](../RUNNING.md).

If it can't connect, the usual cause is the laptop firewall blocking port 8080.
On Windows, allow it once:

```powershell
New-NetFirewallRule -DisplayName "aresgo" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

## Stopping it

`Ctrl-C`. The link goes red in the Data UI within ~3 seconds.

## Options

| Flag | Default | Meaning |
|---|---|---|
| `--port` | `/dev/ttyACM0` | serial port of the Mega |
| `--baud` | `115200` | must match the firmware |
| `--server` | `ws://localhost:8080/telemetry-in` | ground station URL |
| `--interval` | `0.5` | seconds between polls/sends |
| `--no-ws` | off | print packets instead of sending |

## Keeping it running after you close the terminal

For testing, `Ctrl-C` and rerunning is fine. To keep it alive across an SSH
disconnect:

```bash
sudo apt install tmux
tmux new -s bridge
python3 rover_bridge.py --port /dev/ttyACM0 --server ws://<laptop-ip>:8080/telemetry-in
# Ctrl-B then D to detach; `tmux attach -t bridge` to come back
```

Auto-start on boot (systemd) is worth doing once the bridge is proven, not before.

## Known gaps

These are firmware-side issues, not bridge bugs:

- **Encoder counts only update when a move finishes.** `ENC` in
  `arduino/controller.ino` is broken — the `ENC ALL` branch omits the motor id
  and the single-motor branch prints `ENC:,<count>`. The bridge therefore reads
  encoder values from `DONE:` lines instead, which only appear at the end of a
  move. Fixing the firmware's `ENC` output would give continuous counts.
- **`driveMotors` is always empty.** The SEW drive motors are on EtherCAT and
  are not wired to the Mega, so nothing on this serial link knows about them.
  That's a separate integration.
- **IMU values are scaled here, assuming MPU6050 defaults** (±2g, ±250°/s).
  If the firmware ever changes those ranges, update the constants at the top of
  `rover_bridge.py`.
