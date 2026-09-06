// Holds the most recent telemetry received from the rover so any number of
// Data UI browsers can read it concurrently.
package telemetry

import (
	"sync"
	"time"

	"aresgo/internal/model"
)

// Logs are capped so a long mission cannot grow memory without bound.
const (
	maxEventLog   = 100
	maxVerboseLog = 500
	// If nothing arrives from the rover within this window the link is
	// reported as down, so the UI can flag that values are stale.
	linkTimeout = 3 * time.Second
)

type State struct {
	mu       sync.RWMutex
	value    model.TelemetryState
	lastRecv time.Time
}

func NewState() *State {
	return &State{
		value: model.TelemetryState{
			DriveMotors: []model.DriveMotor{},
			ArmJoints:   []model.ArmJoint{},
			EventLog:    []model.LogEntry{},
			VerboseLog:  []model.LogEntry{},
			Environment: model.Environment{AirSensors: []int{}},
		},
	}
}

// Update replaces the sensor/motor portion of the state with a fresh reading
// from the rover. Logs are preserved because they accumulate here rather than
// being resent in full by the bridge on every packet.
func (s *State) Update(incoming model.TelemetryState) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.value.DriveMotors = incoming.DriveMotors
	s.value.ArmJoints = incoming.ArmJoints
	s.value.GPS = incoming.GPS
	s.value.IMU = incoming.IMU
	s.value.Environment = incoming.Environment
	s.value.Timestamp = incoming.Timestamp
	s.lastRecv = time.Now()

	for _, entry := range incoming.EventLog {
		s.appendEventLocked(entry)
	}
	for _, entry := range incoming.VerboseLog {
		s.appendVerboseLocked(entry)
	}
}

func (s *State) AppendEvent(entry model.LogEntry) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.appendEventLocked(entry)
	s.appendVerboseLocked(entry)
}

func (s *State) AppendVerbose(entry model.LogEntry) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.appendVerboseLocked(entry)
}

func (s *State) appendEventLocked(entry model.LogEntry) {
	s.value.EventLog = appendCapped(s.value.EventLog, entry, maxEventLog)
}

func (s *State) appendVerboseLocked(entry model.LogEntry) {
	s.value.VerboseLog = appendCapped(s.value.VerboseLog, entry, maxVerboseLog)
}

// copySlice returns a non-nil copy, so JSON encodes it as [] and never null.
func copySlice[T any](src []T) []T {
	out := make([]T, len(src))
	copy(out, src)
	return out
}

// appendCapped keeps the newest entries and drops the oldest once max is hit.
func appendCapped(log []model.LogEntry, entry model.LogEntry, max int) []model.LogEntry {
	log = append(log, entry)
	if len(log) > max {
		log = log[len(log)-max:]
	}
	return log
}

// Get returns a copy of the current state with the link freshness recomputed.
func (s *State) Get() model.TelemetryState {
	s.mu.RLock()
	defer s.mu.RUnlock()

	snapshot := s.value
	snapshot.RoverLinkUp = !s.lastRecv.IsZero() && time.Since(s.lastRecv) < linkTimeout

	// Slices share backing arrays with the stored state, so copy them to keep
	// a caller from observing a later mutation mid-encode. The copies are made
	// non-nil so an empty slice encodes as [] rather than null: the Data UI
	// types these as arrays and calls .map() on them directly.
	snapshot.DriveMotors = copySlice(s.value.DriveMotors)
	snapshot.ArmJoints = copySlice(s.value.ArmJoints)
	snapshot.EventLog = copySlice(s.value.EventLog)
	snapshot.VerboseLog = copySlice(s.value.VerboseLog)
	snapshot.Environment.AirSensors = copySlice(s.value.Environment.AirSensors)

	return snapshot
}
