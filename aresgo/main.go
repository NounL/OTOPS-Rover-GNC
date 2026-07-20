// Main package wires up the rover ground station server.
//
// Routes:
//
//	/ws            control commands  browser -> Go        (existing)
//	/telemetry-in  rover telemetry   Jetson  -> Go        (new)
//	/telemetry     rover telemetry   Go      -> Data UI   (new)
package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"time"

	"aresgo/internal/control"
	"aresgo/internal/mock"
	"aresgo/internal/telemetry"
	"aresgo/internal/websocket"
)

func main() {
	addr := flag.String("addr", ":8080", "HTTP listen address")
	useMock := flag.Bool("mock", false, "generate fake telemetry instead of waiting for the rover")
	printControl := flag.Bool("print-control", false, "print the live control state to the console")
	flag.Parse()

	controlState := control.NewState()
	telemetryState := telemetry.NewState()

	http.HandleFunc("/ws", websocket.Handle(controlState))
	http.HandleFunc("/telemetry-in", websocket.HandleTelemetryIn(telemetryState))
	http.HandleFunc("/telemetry", websocket.HandleTelemetryOut(telemetryState))

	if *useMock {
		log.Println("mock telemetry ENABLED - serving synthetic rover data")
		go mock.Run(telemetryState, 100*time.Millisecond)
	}

	// Opt-in because this prints ~60 lines a second and buries the connection logs.
	if *printControl {
		go func() {
			ticker := time.NewTicker(16 * time.Millisecond)
			defer ticker.Stop()

			for range ticker.C {
				current := controlState.Get()
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
	}

	log.Printf("ground station listening on %s", *addr)
	log.Printf("  control    ws://localhost%s/ws", *addr)
	log.Printf("  rover in   ws://localhost%s/telemetry-in", *addr)
	log.Printf("  data ui    ws://localhost%s/telemetry", *addr)

	if err := http.ListenAndServe(*addr, nil); err != nil {
		log.Fatalln("server error:", err)
	}
}
