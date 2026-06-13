// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from "react";
import { type ControlState } from "../types/control";

export function useWebSocket(url: string) {
    const [isConnected, setIsConnected] = useState<boolean>(false);
    
    // useRef acts like a persistent pointer in memory. 
    // It keeps our WebSocket connection alive across screen refreshes without losing the socket pointer.
    const socketRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<number | null>(null);

    useEffect(() => {
        // 1. Establish connection to your Go telemetry backend
        const connect = () => {
            console.log(`Connecting to Rover Go Server at: ${url}...`);
            const ws = new WebSocket(url);
            socketRef.current = ws;

            ws.onopen = () => {
                console.log("🟢 WebSocket Network Connection Established!");
                setIsConnected(true);
            };

            ws.onclose = () => {
                console.log("🔴 WebSocket Disconnected.");
                setIsConnected(false);
                
                // 2. Auto Reconnect Engine: If the Go server drops, check back every 3 seconds
                console.log("Attempting automatic reconnection in 3 seconds...");
                reconnectTimeoutRef.current = window.setTimeout(() => {
                    connect();
                }, 3000);
            };

            ws.onerror = (error) => {
                console.error("WebSocket Pipeline Error: ", error);
                ws.close(); // Force clean drop to trigger the onclose reconnect loop
            };
        };

        connect();

        // 3. Cleanup phase: Kill active sockets and timeouts if the component unmounts
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (socketRef.current) {
                // Remove the onclose listener first so it doesn't try to reconnect while shutting down
                socketRef.current.onclose = null; 
                socketRef.current.close();
            }
        };
    }, [url]); // Re-run setup if the backend URL changes

    // 4. Send JSON Commands back across the wire to Go
    const sendControlMessage = (state: ControlState | null) => {
        if (!state) return;

        // Ensure the network pipe is fully open before blasting bits
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            // Equivalent to json.Marshal() in Go. Converts your structural JS object into a plain string packet.
            const packet = JSON.stringify(state);
            socketRef.current.send(packet);
        }
    };

    // Return status variables and the send function tool out to the rest of the app
    return { isConnected, sendControlMessage };
}