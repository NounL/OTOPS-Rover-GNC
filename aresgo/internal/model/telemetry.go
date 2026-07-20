// Defines the structure of rover telemetry: data flowing FROM the rover TO the Data UI.
// This mirrors the Data Interface (Fig 2) in the 2026 User Interface Guidelines.
package model

// DriveMotor is feedback from one SEW drive motor, delivered over EtherCAT.
// Guidelines call for these to be shown as simple text.
type DriveMotor struct {
	ID          int     `json:"id"`
	SpeedRPM    float64 `json:"speedRpm"`
	Direction   string  `json:"direction"`
	Status      string  `json:"status"`
	Temperature float64 `json:"temperature"`
}

// ArmJoint is feedback from one stepper + encoder on the arm, read by the Mega.
// Fields map to the firmware's DONE:<id>,POS:<pos>,ENC:<count> and R status output.
type ArmJoint struct {
	ID         int   `json:"id"`
	Position   int64 `json:"position"`
	Encoder    int64 `json:"encoder"`
	Remaining  int64 `json:"remaining"`
	Direction  int   `json:"direction"`
	Active     bool  `json:"active"`
}

type GPS struct {
	Latitude   float64 `json:"latitude"`
	Longitude  float64 `json:"longitude"`
	AltitudeM  float64 `json:"altitudeM"`
	Satellites int     `json:"satellites"`
	HasFix     bool    `json:"hasFix"`
}

type IMU struct {
	AccelX float64 `json:"accelX"`
	AccelY float64 `json:"accelY"`
	AccelZ float64 `json:"accelZ"`
	GyroX  float64 `json:"gyroX"`
	GyroY  float64 `json:"gyroY"`
	GyroZ  float64 `json:"gyroZ"`
}

// Environment holds the lowest-priority sensors per the guidelines.
// AirSensors is a slice because the firmware TODO calls for polling multiple gas sensors.
type Environment struct {
	PressurePa   float64 `json:"pressurePa"`
	TemperatureC float64 `json:"temperatureC"`
	SoilMoisture int     `json:"soilMoisture"`
	AirSensors   []int   `json:"airSensors"`
}

// LogEntry backs both the human-readable event log and the verbose debug log.
type LogEntry struct {
	Timestamp int64  `json:"timestamp"`
	Level     string `json:"level"`
	Message   string `json:"message"`
}

type TelemetryState struct {
	DriveMotors []DriveMotor `json:"driveMotors"`
	ArmJoints   []ArmJoint   `json:"armJoints"`
	GPS         GPS          `json:"gps"`
	IMU         IMU          `json:"imu"`
	Environment Environment  `json:"environment"`
	EventLog    []LogEntry   `json:"eventLog"`
	VerboseLog  []LogEntry   `json:"verboseLog"`
	// RoverLinkUp reports whether the Jetson bridge is currently pushing data.
	// False means the UI is showing stale values, which the operator must be able to see.
	RoverLinkUp bool  `json:"roverLinkUp"`
	Timestamp   int64 `json:"timestamp"`
}
