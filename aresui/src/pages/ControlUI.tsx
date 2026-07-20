// Control Interface (Fig 1). Sends operator input to the rover.
import { useEffect } from 'react';
import { useGamepad } from '../hooks/useGamepad';
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
          <div style={{ background: '#1c1c1c', padding: '20px', borderRadius: '6px', border: '1px solid #333' }}>
            <h2>[ SUBSYSTEM: DRIVE ]</h2>
            <p>Velocity Vector : <span style={{ color: '#fff' }}>{telemetry.drive.velocity.toFixed(4)}</span></p>
            <p>Turn Rate Scalar: <span style={{ color: '#fff' }}>{telemetry.drive.turn.toFixed(4)}</span></p>
          </div>

          {/* Robotics Panel */}
          <div style={{ background: '#1c1c1c', padding: '20px', borderRadius: '6px', border: '1px solid #333' }}>
            <h2>[ SUBSYSTEM: ROBOTIC ARM ]</h2>
            <p>Shoulder Angle : <span style={{ color: '#fff' }}>{telemetry.arm.shoulder.toFixed(4)}</span></p>
            <p>Elbow Flexion   : <span style={{ color: '#fff' }}>{telemetry.arm.elbow.toFixed(4)}</span></p>
            <p>Gripper State  : <span style={{ color: '#fff' }}>
              {telemetry.arm.gripper === 1 ? 'OPENING' : telemetry.arm.gripper === -1 ? 'CLOSING' : 'NEUTRAL'}
            </span></p>
          </div>

          {/* Global Machine States */}
          <div style={{ background: '#1c1c1c', padding: '20px', borderRadius: '6px', border: '1px solid #333', gridColumn: 'span 2' }}>
            <h2>[ SYSTEM STATUS OVERVIEW ]</h2>
            <p>Operational Mode: <span style={{ color: '#fff' }}>{telemetry.mode}</span></p>
            <p>Emergency E-STOP: <span style={{ color: telemetry.estop ? '#ff4c4c' : '#4cff4c' }}>{telemetry.estop ? 'ENGAGED' : 'INACTIVE'}</span></p>
            <p>Frame Timestamp : <span style={{ color: '#888' }}>{telemetry.timestamp}</span></p>
          </div>
        </div>
      )}
    </div>
  );
}
