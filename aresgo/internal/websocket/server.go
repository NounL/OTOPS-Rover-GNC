// Handles Websocket connections by upgrading incoming HTTP requests
package websocket

import (
	"aresgo/internal/control"
	"aresgo/internal/model"
	"encoding/json"
	"net/http"

	"github.com/gorilla/websocket"
)

// Upgrader object initialized so that all origins are accepted
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

// Handle returns an HTTP handler function that upgrades incoming HTTP requests to WebSocket connections.
func Handle(state *control.State) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn, _ := upgrader.Upgrade(w, r, nil)

		for {
			_, msg, err := conn.ReadMessage()
			if err != nil {
				return
			}

			var cmd model.ControlState

			stt := json.Unmarshal(msg, &cmd)
			if stt == nil {
				state.Update(cmd)
			}

		}
	}
}
