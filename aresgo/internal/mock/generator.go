// Generates fake rover telemetry so the Data UI can be built and tested
// before the Jetson bridge and Arduino firmware are ready.
// Delete this package, or stop passing -mock, once real data flows in.
package mock

import (
	"fmt"
	"math"
	"math/rand"
	"time"

	"aresgo/internal/model"
	"aresgo/internal/telemetry"
)

// Ontario Tech campus, used as a plausible starting fix.
const (
	baseLat = 43.9450
	baseLon = -78.8960
)

var driveStatuses = []string{"OK", "OK", "OK", "WARN: TEMP"}

// Run feeds the telemetry state with synthetic readings until stopped.
// It writes through the same State.Update path the real bridge will use,
// so nothing downstream can tell the difference.
func Run(state *telemetry.State, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	start := time.Now()
	var tick int

	for range ticker.C {
		tick++
		elapsed := time.Since(start).Seconds()
		now := time.Now().UnixMilli()

		state.Update(model.TelemetryState{
			DriveMotors: mockDriveMotors(elapsed),
			ArmJoints:   mockArmJoints(elapsed),
			GPS:         mockGPS(elapsed),
			IMU:         mockIMU(elapsed),
			Environment: mockEnvironment(elapsed),
			Timestamp:   now,
		})

		// Occasional log lines exercise the UI's event and verbose panels.
		if tick%25 == 0 {
			state.AppendEvent(model.LogEntry{
				Timestamp: now,
				Level:     "info",
				Message:   fmt.Sprintf("MOCK: drive command acknowledged (seq %d)", tick/25),
			})
		}
		if tick%5 == 0 {
			state.AppendVerbose(model.LogEntry{
				Timestamp: now,
				Level:     "debug",
				Message: fmt.Sprintf("MOCK: S -> soil=%d%% air=%d pressure=%.0fPa",
					mockEnvironment(elapsed).SoilMoisture,
					mockEnvironment(elapsed).AirSensors[0],
					mockEnvironment(elapsed).PressurePa),
			})
		}
	}
}

func mockDriveMotors(elapsed float64) []model.DriveMotor {
	motors := make([]model.DriveMotor, 4)
	for i := range motors {
		// Phase-shift each wheel so the UI shows four distinct values.
		speed := 40 * math.Sin(elapsed*0.5+float64(i)*0.7)
		direction := "FORWARD"
		if speed < 0 {
			direction = "REVERSE"
		}
		motors[i] = model.DriveMotor{
			ID:          i + 1,
			SpeedRPM:    math.Abs(speed),
			Direction:   direction,
			Status:      driveStatuses[i],
			Temperature: 35 + 8*math.Sin(elapsed*0.2+float64(i)),
		}
	}
	return motors
}

func mockArmJoints(elapsed float64) []model.ArmJoint {
	joints := make([]model.ArmJoint, 5)
	for i := range joints {
		pos := int64(800 * math.Sin(elapsed*0.3+float64(i)*1.1))
		joints[i] = model.ArmJoint{
			ID:        i,
			Position:  pos,
			Encoder:   pos * 2,
			Remaining: 0,
			Direction: 1,
			Active:    math.Cos(elapsed*0.3+float64(i)) > 0.8,
		}
	}
	return joints
}

func mockGPS(elapsed float64) model.GPS {
	return model.GPS{
		Latitude:   baseLat + 0.0004*math.Sin(elapsed*0.05),
		Longitude:  baseLon + 0.0004*math.Cos(elapsed*0.05),
		AltitudeM:  120 + 3*math.Sin(elapsed*0.1),
		Satellites: 9,
		HasFix:     true,
	}
}

func mockIMU(elapsed float64) model.IMU {
	return model.IMU{
		AccelX: 0.4 * math.Sin(elapsed*1.3),
		AccelY: 0.4 * math.Cos(elapsed*1.1),
		AccelZ: 9.81 + 0.2*math.Sin(elapsed*2.0),
		GyroX:  2 * math.Sin(elapsed*0.9),
		GyroY:  2 * math.Cos(elapsed*0.7),
		GyroZ:  1.5 * math.Sin(elapsed*0.4),
	}
}

func mockEnvironment(elapsed float64) model.Environment {
	air := make([]int, 4)
	for i := range air {
		air[i] = 180 + int(60*math.Sin(elapsed*0.25+float64(i)*0.9)) + rand.Intn(5)
	}
	return model.Environment{
		PressurePa:   101325 + 200*math.Sin(elapsed*0.08),
		TemperatureC: 21 + 2*math.Sin(elapsed*0.15),
		SoilMoisture: 45 + int(15*math.Sin(elapsed*0.12)),
		AirSensors:   air,
	}
}
