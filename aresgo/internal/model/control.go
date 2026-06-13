// Defines the structure of rover control state, subject to change
// TODO: Update based on actual control requirements. This is just a placeholder for now.
package model

type Drive struct {
	Velocity float64 `json:"velocity,omitempty"`
	Turn     float64 `json:"turn,omitempty"`
}

type Arm struct {
	Shoulder float64 `json:"shoulder,omitempty"`
	Elbow    float64 `json:"elbow,omitempty"`
	Gripper  float64 `json:"gripper,omitempty"`
}

type ControlState struct {
	Drive     Drive  `json:"drive"`
	Arm       Arm    `json:"arm"`
	Mode      string `json:"mode"`
	Estop     bool   `json:"estop"`
	Timestamp int64  `json:"timestamp"`
}
