// Main package wires up the rover ground station server.
//
// Routes:
//
//	/ws            control commands  browser -> Go        (existing)
//	/telemetry-in  rover telemetry   Jetson  -> Go        (new)
//	/telemetry     rover telemetry   Go      -> Data UI   (new)
package main

import (
	"encoding/json"
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

	// This loop always runs, because it is where control state gets forwarded
	// on to the rover. Only the console print is opt-in, since it emits ~60
	// lines a second and buries the connection logs.
	go func() {
		ticker := time.NewTicker(16 * time.Millisecond)
		defer ticker.Stop()

		//conn1, _ := net.Dial("udp", "192.168.1.20:5999")
		//defer conn1.Close()

		for range ticker.C {
			current := controlState.Get()

			if *printControl {
				data, err := json.Marshal(current)
				if err == nil {
					fmt.Println(string(data))
				}
			}

			/*
				payload, _ := json.Marshal(current)
				conn1.Write(payload)
			*/
		}
	}()

	log.Printf("ground station listening on %s", *addr)
	log.Printf("  control    ws://localhost%s/ws", *addr)
	log.Printf("  rover in   ws://localhost%s/telemetry-in", *addr)
	log.Printf("  data ui    ws://localhost%s/telemetry", *addr)

	if err := http.ListenAndServe(*addr, nil); err != nil {
		log.Fatalln("server error:", err)
	}
}
