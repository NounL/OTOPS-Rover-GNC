// Methods to initialize, update, and retrieve the control state of the rover
package control

import (
	"aresgo/internal/model"
	"sync"
)

// Defines an instance of the control state, which can be safely accessed and updated with a mutex
type State struct {
	mu    sync.RWMutex
	value model.ControlState
}

// Initializes a new State with default values
func NewState() *State {
	return &State{
		value: model.ControlState{
			Mode: "manual",
		},
	}
}

// Safely updates the control state with a new value, locking the mutex for writing
func (s *State) Update(newState model.ControlState) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.value = newState
}

// Safely retrieves the current control state, locking the mutex for reading
func (s *State) Get() model.ControlState {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.value
}
