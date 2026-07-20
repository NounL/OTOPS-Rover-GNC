// Telemetry WebSocket routes: the rover pushes data IN, the Data UI reads it OUT.
// This is the mirror image of server.go, which carries control commands the other way.
package websocket

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"aresgo/internal/model"
	"aresgo/internal/telemetry"

	"github.com/gorilla/websocket"
)

// How often each connected Data UI browser is sent a fresh snapshot.
// Telemetry is for human reading, so this is far slower than the 60Hz control loop.
const telemetryPushInterval = 200 * time.Millisecond

// HandleTelemetryIn accepts the Jetson bridge as a client and stores what it pushes.
func HandleTelemetryIn(state *telemetry.State) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Println("telemetry-in upgrade failed:", err)
			return
		}
		defer conn.Close()

		log.Println("telemetry-in: rover bridge connected")
		state.AppendEvent(model.LogEntry{
			Timestamp: time.Now().UnixMilli(),
			Level:     "info",
			Message:   "Rover telemetry bridge connected",
		})

		for {
			_, msg, err := conn.ReadMessage()
			if err != nil {
				log.Println("telemetry-in: rover bridge disconnected:", err)
				state.AppendEvent(model.LogEntry{
					Timestamp: time.Now().UnixMilli(),
					Level:     "warn",
					Message:   "Rover telemetry bridge disconnected",
				})
				return
			}

			var incoming model.TelemetryState
			if err := json.Unmarshal(msg, &incoming); err != nil {
				// A malformed packet is logged and skipped rather than dropping
				// the link, since one bad serial read should not blind the operator.
				state.AppendVerbose(model.LogEntry{
					Timestamp: time.Now().UnixMilli(),
					Level:     "error",
					Message:   "Discarded malformed telemetry packet: " + err.Error(),
				})
				continue
			}

			state.Update(incoming)
		}
	}
}

// HandleTelemetryOut pushes the current telemetry snapshot to a Data UI browser
// on a fixed interval for as long as the browser stays connected.
func HandleTelemetryOut(state *telemetry.State) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Println("telemetry-out upgrade failed:", err)
			return
		}
		defer conn.Close()

		log.Println("telemetry-out: Data UI connected")

		// Detect the browser closing the tab. Without a reader the write loop
		// below would not notice the socket is gone until its next failed write.
		closed := make(chan struct{})
		go func() {
			defer close(closed)
			for {
				if _, _, err := conn.ReadMessage(); err != nil {
					return
				}
			}
		}()

		ticker := time.NewTicker(telemetryPushInterval)
		defer ticker.Stop()

		for {
			select {
			case <-closed:
				log.Println("telemetry-out: Data UI disconnected")
				return
			case <-ticker.C:
				payload, err := json.Marshal(state.Get())
				if err != nil {
					log.Println("telemetry-out: encode failed:", err)
					continue
				}
				if err := conn.WriteMessage(websocket.TextMessage, payload); err != nil {
					log.Println("telemetry-out: write failed:", err)
					return
				}
			}
		}
	}
}
