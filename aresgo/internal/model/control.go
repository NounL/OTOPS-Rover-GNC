// Defines the structure of rover control state, subject to change

package model

type Mode string

const (
	ModeDrive Mode = "DRIVE"
	ModeArm   Mode = "ARM"
)

// DriveStruct holds normalized differential drive inputs for SEW motors.
type DriveStruct struct {
	LinearVelocity  float64 `json:"linear_velocity"`  // Y-Axis (-1.0 to +1.0)
	AngularVelocity float64 `json:"angular_velocity"` // X-Axis (-1.0 to +1.0)
}

// ArmStruct holds joint inputs for 5-DOF NEMA steppers. Cant control more than two joints at once.
type ArmStruct struct {
	Base     float64 `json:"base"`     // Rotation speed(-1.0 to +1.0)
	Shoulder float64 `json:"shoulder"` // Rotation speed(-1.0 to +1.0)
	Elbow    float64 `json:"elbow"`    // Rotation speed(-1.0 to +1.0)
	Wrist    float64 `json:"wrist"`    // Rotation speed(-1.0 to +1.0)
	Gripper  float64 `json:"gripper"`  // Open (+1.0) / Close (-1.0)
}

// ControlState is the full packet sent over UDP on every tick. Includes speedscale modifier
type ControlState struct {
	Mode       Mode        `json:"mode"`        // "DRIVE" or "ARM"
	SpeedScale float64     `json:"speed_scale"` // Global velocity scaling factor (e.g., 0.1 to 1.0)
	Drive      DriveStruct `json:"drive"`       // Always present
	Arm        ArmStruct   `json:"arm"`         // Always present
	Timestamp  int64       `json:"timestamp"`   // Unix timestamp in milliseconds
}
