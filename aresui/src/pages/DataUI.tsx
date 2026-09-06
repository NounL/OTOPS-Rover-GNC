// Data Interface (Fig 2 of the 2026 User Interface Guidelines).
// Receive-only: shows sensor, motor and log data pushed from the rover.
import './DataUI.css';
import { useTelemetry } from '../hooks/useTelemetry';
import { type ArmJoint, type LogEntry } from '../types/telemetry';

const TELEMETRY_URL =
  import.meta.env.VITE_WS_TELEMETRY_URL || 'ws://localhost:8080/telemetry';

function formatTime(ms: number) {
  if (!ms) return '--:--:--';
  return new Date(ms).toLocaleTimeString('en-CA', { hour12: false });
}

function statusClass(status: string) {
  const upper = status.toUpperCase();
  if (upper.includes('FAULT') || upper.includes('ERR')) return 'status-bad';
  if (upper.includes('WARN')) return 'status-warn';
  return 'status-ok';
}

function LogPanel({ entries, emptyText }: { entries: LogEntry[]; emptyText: string }) {
  if (entries.length === 0) {
    return <div className="log-empty">{emptyText}</div>;
  }
  // Newest first so the operator reads the latest without scrolling.
  return (
    <>
      {[...entries].reverse().map((entry, i) => (
        <div key={`${entry.timestamp}-${i}`} className={`log-line log-level-${entry.level}`}>
          <span className="log-time">{formatTime(entry.timestamp)}</span>
          <span className="log-msg">{entry.message}</span>
        </div>
      ))}
    </>
  );
}

// Rough side-on view of the arm driven by encoder positions.
// Steps are mapped to degrees by STEPS_PER_DEG, which must be recalibrated
// against the real gearing once the arm is assembled.
const STEPS_PER_DEG = 8;

function ArmVisual({ joints }: { joints: ArmJoint[] }) {
  const angle = (index: number) => (joints[index]?.position ?? 0) / STEPS_PER_DEG;

  const shoulderDeg = angle(0);
  const elbowDeg = angle(1);
  const wristDeg = angle(2);

  const baseX = 250;
  const baseY = 185;

  const toRad = (deg: number) => (deg * Math.PI) / 180;

  // Each segment starts where the previous ended, accumulating rotation.
  const a1 = toRad(-60 + shoulderDeg);
  const shoulderX = baseX + 90 * Math.cos(a1);
  const shoulderY = baseY + 90 * Math.sin(a1);

  const a2 = a1 + toRad(70 + elbowDeg);
  const elbowX = shoulderX + 75 * Math.cos(a2);
  const elbowY = shoulderY + 75 * Math.sin(a2);

  const a3 = a2 + toRad(40 + wristDeg);
  const wristX = elbowX + 42 * Math.cos(a3);
  const wristY = elbowY + 42 * Math.sin(a3);

  return (
    <svg viewBox="0 0 500 260" preserveAspectRatio="xMidYMid meet">
      {/* chassis */}
      <rect x="150" y="185" width="200" height="46" rx="4" fill="none" stroke="#4b5563" strokeWidth="2" />
      {/* wheels */}
      {[180, 250, 320].map((cx) => (
        <circle key={cx} cx={cx} cy={239} r="17" fill="none" stroke="#4b5563" strokeWidth="2" />
      ))}
      {/* arm segments */}
      <line x1={baseX} y1={baseY} x2={shoulderX} y2={shoulderY} stroke="#c084fc" strokeWidth="4" strokeLinecap="round" />
      <line x1={shoulderX} y1={shoulderY} x2={elbowX} y2={elbowY} stroke="#a855f7" strokeWidth="4" strokeLinecap="round" />
      <line x1={elbowX} y1={elbowY} x2={wristX} y2={wristY} stroke="#8b5cf6" strokeWidth="3" strokeLinecap="round" />
      {/* joints */}
      <circle cx={baseX} cy={baseY} r="6" fill="#f3f4f6" />
      <circle cx={shoulderX} cy={shoulderY} r="5" fill="#f3f4f6" />
      <circle cx={elbowX} cy={elbowY} r="5" fill="#f3f4f6" />
      <circle cx={wristX} cy={wristY} r="4" fill="#fbbf24" />
    </svg>
  );
}

export default function DataUI() {
  const { telemetry, isConnected } = useTelemetry(TELEMETRY_URL);

  return (
    <div className="dataui">
      <header className="dataui-header">
        <div className="dataui-title">OTOPS &mdash; DATA INTERFACE</div>
        <div className="dataui-status">
          <span className="status-pill">
            <span className={`status-dot ${isConnected ? 'up' : 'down'}`} />
            GROUND STATION {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
          <span className="status-pill">
            <span className={`status-dot ${telemetry?.roverLinkUp ? 'up' : 'down'}`} />
            ROVER LINK {telemetry?.roverLinkUp ? 'UP' : 'DOWN'}
          </span>
          <span className="status-pill">LAST PACKET {formatTime(telemetry?.timestamp ?? 0)}</span>
        </div>
      </header>

      {!telemetry ? (
        <div className="dataui-waiting">
          Waiting for telemetry from {TELEMETRY_URL} &hellip;
        </div>
      ) : (
        <div className="dataui-grid">
          <section className="panel panel-visual">
            <div className="panel-title">Animated Visual Feedback</div>
            <div className="arm-visual">
              <ArmVisual joints={telemetry.armJoints} />
            </div>
            <div className="joint-readout">
              {telemetry.armJoints.map((joint) => (
                <span key={joint.id}>
                  J{joint.id} pos <b>{joint.position}</b> enc <b>{joint.encoder}</b>
                  {joint.active ? ' ▶' : ''}
                </span>
              ))}
            </div>
          </section>

          <section className="panel panel-motors">
            <div className="panel-title">Motor Data Feedback</div>
            <div className="panel-scroll">
              {telemetry.driveMotors.map((motor) => (
                <div className="motor-row" key={motor.id}>
                  <div className="motor-name">M{motor.id}</div>
                  <div className="motor-fields">
                    <span>
                      speed <b>{motor.speedRpm.toFixed(1)}</b> rpm
                    </span>
                    <span>
                      dir <b>{motor.direction}</b>
                    </span>
                    <span>
                      temp <b>{motor.temperature.toFixed(1)}</b>&deg;C
                    </span>
                    <span className={statusClass(motor.status)}>{motor.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel panel-events">
            <div className="panel-title">Human Readable Event Log</div>
            <div className="panel-scroll">
              <LogPanel entries={telemetry.eventLog} emptyText="No events yet." />
            </div>
          </section>

          <section className="panel panel-verbose">
            <div className="panel-title">Verbose Data Log</div>
            <div className="panel-scroll">
              <LogPanel entries={telemetry.verboseLog} emptyText="No debug output yet." />
            </div>
          </section>

          <section className="panel panel-sensors">
            <div className="panel-title">Sensor Data Feedback</div>
            <div className="panel-scroll">
              {/* Guidelines order: GPS first, IMU second, environmental last. */}
              <div className="sensor-group">
                <div className="sensor-group-title">GPS</div>
                <div className="sensor-line">
                  <span>Latitude</span>
                  <span>{telemetry.gps.latitude.toFixed(6)}</span>
                </div>
                <div className="sensor-line">
                  <span>Longitude</span>
                  <span>{telemetry.gps.longitude.toFixed(6)}</span>
                </div>
                <div className="sensor-line">
                  <span>Altitude</span>
                  <span>{telemetry.gps.altitudeM.toFixed(1)} m</span>
                </div>
                <div className="sensor-line">
                  <span>Satellites</span>
                  <span>{telemetry.gps.satellites}</span>
                </div>
                <div className="sensor-line">
                  <span>Fix</span>
                  <span className={telemetry.gps.hasFix ? 'status-ok' : 'status-bad'}>
                    {telemetry.gps.hasFix ? 'LOCKED' : 'NO FIX'}
                  </span>
                </div>
              </div>

              <div className="sensor-group">
                <div className="sensor-group-title">IMU</div>
                <div className="sensor-line">
                  <span>Accel X / Y / Z</span>
                  <span>
                    {telemetry.imu.accelX.toFixed(2)} / {telemetry.imu.accelY.toFixed(2)} /{' '}
                    {telemetry.imu.accelZ.toFixed(2)}
                  </span>
                </div>
                <div className="sensor-line">
                  <span>Gyro X / Y / Z</span>
                  <span>
                    {telemetry.imu.gyroX.toFixed(2)} / {telemetry.imu.gyroY.toFixed(2)} /{' '}
                    {telemetry.imu.gyroZ.toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="sensor-group">
                <div className="sensor-group-title">Environmental</div>
                {telemetry.environment.airSensors.map((value, i) => (
                  <div className="sensor-line" key={i}>
                    <span>Air sensor {i + 1}</span>
                    <span>{value}</span>
                  </div>
                ))}
                <div className="sensor-line">
                  <span>Soil moisture</span>
                  <span>{telemetry.environment.soilMoisture}%</span>
                </div>
                <div className="sensor-line">
                  <span>Pressure</span>
                  <span>{(telemetry.environment.pressurePa / 100).toFixed(1)} hPa</span>
                </div>
                <div className="sensor-line">
                  <span>Temperature</span>
                  <span>{telemetry.environment.temperatureC.toFixed(1)} &deg;C</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
