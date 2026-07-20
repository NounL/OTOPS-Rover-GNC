// Mirrors aresgo/internal/model/telemetry.go. Keep both sides in sync.

export interface DriveMotor {
  id: number;
  speedRpm: number;
  direction: string;
  status: string;
  temperature: number;
}

export interface ArmJoint {
  id: number;
  position: number;
  encoder: number;
  remaining: number;
  direction: number;
  active: boolean;
}

export interface GPS {
  latitude: number;
  longitude: number;
  altitudeM: number;
  satellites: number;
  hasFix: boolean;
}

export interface IMU {
  accelX: number;
  accelY: number;
  accelZ: number;
  gyroX: number;
  gyroY: number;
  gyroZ: number;
}

export interface Environment {
  pressurePa: number;
  temperatureC: number;
  soilMoisture: number;
  airSensors: number[];
}

export interface LogEntry {
  timestamp: number;
  level: string;
  message: string;
}

export interface TelemetryState {
  driveMotors: DriveMotor[];
  armJoints: ArmJoint[];
  gps: GPS;
  imu: IMU;
  environment: Environment;
  eventLog: LogEntry[];
  verboseLog: LogEntry[];
  roverLinkUp: boolean;
  timestamp: number;
}
