// Control Interface (Fig 1). Sends operator input to the rover.
import { useEffect } from 'react';
import { useGamepad } from '../hooks/useGamepadreplacement';
import { useWebSocket } from '../hooks/useWebSocket';

export default function ControlUI() {
  const telemetry = useGamepad();
  const backendUrl = import.meta.env.VITE_WS_BACKEND_URL || 'ws://localhost:8080/ws';
  const { isConnected, sendControlMessage } = useWebSocket(backendUrl);

  useEffect(() => {
    // If we aren't connected to the network, don't start a timer
    if (!isConnected) return;

    // Set up a strict clock needs to be below 16ms to match animationframes (scales with fps)
    // Interval is currently set to 15ms for 60hz, lower it if your display
    // refresh rate is higher than 60hz
    const networkTimer = setInterval(() => {
      if (telemetry) {
        sendControlMessage(telemetry);
      }
    }, 15);
    return () => {
      clearInterval(networkTimer);
    };
  }, [telemetry, isConnected]);

  return (
    <div>
      {!telemetry ? (
        <div></div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
          
          {/* Drive Panel */}

          <div style={{ background: '#0d86a1', padding: '20px', borderRadius: '6px', border: '5px solid #bc8400' }}>
            <h2>[ SUBSYSTEM: DRIVE ]</h2>
          <p>
            Linear Velocity :
            <span style={{ color: telemetry.drive.linear_velocity !== 0 ? "#00ff66" : "#fff" }}>
              {telemetry.drive.linear_velocity.toFixed(4)}
            </span>
          </p>
          <p>
            Angular Velocity:
            <span style={{ color: telemetry.drive.angular_velocity !== 0 ? "#00ff66" : "#fff" }}>
              {telemetry.drive.angular_velocity.toFixed(4)}
            </span>
          </p>
          </div>

          {/* Robotics Panel */}
          <div style={{ background: '#0d86a1', padding: '20px', borderRadius: '6px', border: '5px solid #bc8400' }}>
            <h2>[ SUBSYSTEM: ROBOTIC ARM ]</h2>
            <p>Base    : <span style={{ color: telemetry.arm.base !== 0 ? "#00ff66" : "#fff"}}>{telemetry.arm.base.toFixed(4)}</span></p>
            <p>Elbow   : <span style={{ color: telemetry.arm.elbow !== 0 ? "#00ff66" : '#fff' }}>{telemetry.arm.elbow.toFixed(4)}</span></p>
            <p>Rotate   : <span style={{ color: telemetry.arm.rotate !== 0 ? "#00ff66" : '#fff' }}>{telemetry.arm.rotate.toFixed(4)}</span></p>
            <p>Wrist   : <span style={{ color: telemetry.arm.wrist !== 0 ? "#00ff66" : '#fff' }}>{telemetry.arm.wrist.toFixed(4)}</span></p>
            <p>Gripper : <span style={{ color: telemetry.arm.gripper !== 0 ? "#00ff66" : '#fff' }}>
              {telemetry.arm.gripper > 0 ? 'STATIC' : telemetry.arm.gripper < 0 ? 'CLOSING' : 'NEUTRAL'}
            </span></p>
          </div>

          {/* Global Machine States */}
          <div style={{ background: '#0d86a1', padding: '20px', borderRadius: '6px', border: '5px solid #bc8400' , gridColumn: 'span 2' }}>
            <h2>[ SYSTEM STATUS OVERVIEW ]</h2>
            <p>Operational Mode: <span style={{ color: '#fff' }}>{telemetry.mode}</span></p>
            <p>Speed Scale     : <span style={{ color: '#fff' }}>{telemetry.speed_scale.toFixed(2)}</span></p>
            <p>Frame Timestamp : <span style={{ color: '#fff' }}>{telemetry.timestamp}</span></p>
          </div>
          <div style={{ textAlign: 'left', background: '#868686', color: '#fff', padding: '20px', borderRadius: '6px', border: '5px solid #bc8400' , gridColumn: 'span 2' }}>
            <h2>Controls</h2>
            <p>(A) - toggle between DRIVE mode and ARM mode  </p>
            <h4>DRIVE mode </h4>
            <p>L STICK move FWD / REV  </p>
            <p>R STICK turn LEFT / RIGHT</p>
            <p>RB / LB      increment / decrement the global speed scale</p>
            <h4>ARM mode</h4>
            <p>(X) - cycle L STICK motor</p>
            <p>(B) - cycle R STICK motor </p>
            <p>L3 / R3      (stick click) zero out that stick's axis/axes; stays zeroed until the stick is physically moved again</p>
          </div>
        </div>
      )}
    </div>
  );
}
