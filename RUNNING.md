# Running the Ground Station

How to start, check, and stop the ground station on a dev machine.

There are two things to run: the **Go backend** (`aresgo`) and the **web frontend**
(`aresui`). They are separate processes and each needs its own terminal.

---

## One-time setup

Needed once per machine.

| Tool | Check it exists | If missing |
| --- | --- | --- |
| Go 1.25+ | `go version` | `winget install GoLang.Go` (Windows) or https://go.dev/dl |
| Node 20+ | `node --version` | https://nodejs.org |

> **Windows:** after installing Go you must fully **quit and reopen VS Code** (not just
> open a new terminal tab). The integrated terminal inherits its PATH from the VS Code
> process, so a new tab in the same window still says `'go' is not recognized`.
>
> To fix the terminal you already have open, without restarting:
>
> ```powershell
> $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
> ```

Then install dependencies:

```bash
cd aresgo
go mod download

cd ../aresui
npm install
```

---

## Running it

### Terminal 1 — Go backend

```bash
cd aresgo
go run . -mock
```

You should see:

```
mock telemetry ENABLED - serving synthetic rover data
ground station listening on :8080
  control    ws://localhost:8080/ws
  rover in   ws://localhost:8080/telemetry-in
  data ui    ws://localhost:8080/telemetry
```

Run `go run .` (no flag) and it starts the same but serves no data until a real
rover connects, so the Data UI will sit on "Waiting for telemetry".

**Flags**

| Flag | Effect |
| --- | --- |
| `-mock` | Generate fake sensor/motor data. Use this until the Jetson bridge exists. |
| `-print-control` | Print the live control state ~60x/sec. Noisy; off by default. |
| `-addr :9090` | Listen on a different port. |

### Terminal 2 — Web frontend

```bash
cd aresui
npm run dev
```

Then open:

| Screen | URL |
| --- | --- |
| Control Interface (Fig 1) | http://localhost:5173/ |
| **Data Interface (Fig 2)** | **http://localhost:5173/#/data** |

Both screens are one Vite app on port 5173, split by the URL hash. They are meant
to run on two monitors, so open two browser windows rather than switching tabs.

---

## Checking it works

**Data UI** — open http://localhost:5173/#/data. With `-mock` running, the header
should read `GROUND STATION CONNECTED` and `ROVER LINK UP` (both dots green), and
the numbers should visibly move. If the dots are red, the Go backend isn't running.

**Control UI** — open http://localhost:5173/, click the page once so it has keyboard
focus, then hold `W`/`A`/`S`/`D` (drive) or the arrow keys (arm). The values change
while a key is held and snap back to `0.0000` on release. Start the backend with
`-print-control` to confirm the values are actually arriving in Go.

---

## Stopping it

Press `Ctrl+C` in each terminal. Stop both — the Go server keeps holding port 8080
otherwise, and the next `go run .` fails with "address already in use".

If a process was closed without `Ctrl+C` and port 8080 is stuck:

```powershell
# Windows: find the PID holding the port, then kill it
netstat -ano | findstr :8080
taskkill /PID <pid> /F
```

```bash
# macOS / Linux
lsof -ti:8080 | xargs kill
```

Same commands work for port 5173 (Vite).

---

## Ports and routes

| Port | What | Notes |
| --- | --- | --- |
| 8080 | Go backend | All three WebSocket routes live here |
| 5173 | Vite dev server | Frontend only; serves both UI screens |

| Route | Direction | Purpose |
| --- | --- | --- |
| `/ws` | browser → Go | Control commands (drive/arm/estop) |
| `/telemetry-in` | Jetson → Go | Rover pushes sensor + motor data **(no client yet)** |
| `/telemetry` | Go → browser | Data UI reads telemetry |

To point the frontend at a backend on another machine (e.g. the real ground station
over WiFi), create `aresui/.env`:

```
VITE_WS_BACKEND_URL=ws://192.168.1.50:8080/ws
VITE_WS_TELEMETRY_URL=ws://192.168.1.50:8080/telemetry
```

Restart `npm run dev` after editing `.env` — Vite only reads it at startup.

---

## Current state

Working end to end with **fake data only**. Still to be built:

- **Jetson bridge** — nothing connects to `/telemetry-in` yet. Needs a Python service
  that reads the Arduino over serial, parses it, and pushes JSON to that route.
  Note that `arm_pi_MotorsController.py`'s `parse_response_lines()` currently only
  understands `ACK:` / `DONE:` / `ENC:` and drops all sensor and motor-status output.
- **Control relay** — `/ws` stores commands in memory but does not forward them to
  the rover, so the Control UI does not yet move anything.
- **Firmware** — `arduino/controller.ino` has two compile errors (missing semicolon
  at line 41; undefined `b` / `c` at lines 156-158) and GPS emits unprompted NMEA
  that will interleave with command responses.

Once the bridge exists, drop `-mock` and the same Data UI shows real values with no
frontend changes.
