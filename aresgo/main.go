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
	"net"
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

		jetsonAddr := "192.168.1.31:5999"
		conn1, err := net.Dial("udp", jetsonAddr)
		if err != nil {
			// Previously this error was discarded, and conn1 (nil on failure)
			// would then panic the whole process on the first conn1.Write call
			// below. Logging + bailing out here is both safer and gives us
			// visibility we didn't have before.
			log.Printf("udp-send: failed to dial %s: %v", jetsonAddr, err)
			return
		}
		defer conn1.Close()
		// LocalAddr() reveals which network interface the OS actually chose to
		// send from - if this isn't the Rocket Prism's address range, packets
		// are going out the wrong link (e.g. WiFi) and will never reach the Jetson.
		log.Printf("udp-send: sending drive commands to %s from local %s", jetsonAddr, conn1.LocalAddr())

		sentCount := 0
		errorCount := 0
		lastReport := time.Now()

		for range ticker.C {
			current := controlState.Get()

			if *printControl {
				data, err := json.Marshal(current)
				if err == nil {
					fmt.Println(string(data))
				}
			}

			payload, _ := json.Marshal(current)
			if _, werr := conn1.Write(payload); werr != nil {
				errorCount++
			} else {
				sentCount++
			}

			// Periodic summary instead of logging every ~16ms tick.
			if time.Since(lastReport) >= 5*time.Second {
				log.Printf("udp-send: %d packet(s) sent, %d write error(s) in the last ~5s (target %s, local %s)",
					sentCount, errorCount, jetsonAddr, conn1.LocalAddr())
				sentCount = 0
				errorCount = 0
				lastReport = time.Now()
			}
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
