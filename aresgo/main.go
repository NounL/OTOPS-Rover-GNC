// Main package handles the creation of the control state, sets up the WebSocket server
// and periodically prints the current state to the console.
package main

import (
	"aresgo/internal/control"
	"aresgo/internal/websocket"
	"fmt"
	"net/http"
	"time"
)

func main() {

	// Create a new control state
	state := control.NewState()

	// Websocket url is /ws, handles incoming connections using the websocket.Handle function
	http.HandleFunc("/ws", websocket.Handle(state))

	go func() {
		// This goroutine will print the current state to the console every 16 milliseconds (approximately 60 times per second)
		ticker := time.NewTicker(16 * time.Millisecond)

		for range ticker.C {
			current := state.Get()

			fmt.Printf(
				"DRIVE v=%.2f turn=%.2f | ARM s=%.2f e=%.2f g=%.2f | mode=%s\n",
				current.Drive.Velocity,
				current.Drive.Turn,
				current.Arm.Shoulder,
				current.Arm.Elbow,
				current.Arm.Gripper,
				current.Mode,
			)
		}

	}()
	// Start the HTTP server on port 8080
	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		fmt.Println("Server error:", err)
	}
}
