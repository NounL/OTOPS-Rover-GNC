// src/hooks/useGamepad.ts
// NOTE: POLLING LOOP USES REQUESTANIMATIONFRAME TO DETERMINE WHEN CONTROLSTATE
// GETS UPDATED. THIS IS DEPENDENT ON YOUR LAPTOPS REFRESH RATE. IF YOU ENCOUNTER
// ISSUES WITH RESPONSIVNESS, LOWER THE INTERVAL IN APP.TSX 
import { useState, useEffect } from "react";
import { type ControlState } from "../types/control";

export function useGamepad() {
    //Holds the current state of the keyboard input, updates on every animation frame
    const [controlState, setControlState] = useState<ControlState | null>(null);

    // this useEffect function runs once on call
    useEffect(() => {
        let animationFrameId: number;

        // dictionary to track which keyboard keys are currently pressed
        const keysPressed: Record<string, boolean> = {};

        //Set up dictionary with event listeners to track key presses and releases 
        const handleKeyDown = (e: KeyboardEvent) => {
            keysPressed[e.key.toLowerCase()] = true;
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            keysPressed[e.key.toLowerCase()] = false;
        };

        // Listen for key events at the window level to capture all input regardless of focus
        window.addEventListener("keydown", handleKeyDown);
        window.addEventListener("keyup", handleKeyUp);

        // Continuous frame execution clock loop
        const pollKeyboardLoop = () => {
            // WASD for Mobile Base Drive Control
            let velocity = 0;
            let turn = 0;
            if (keysPressed["w"]) velocity = 1.0;  // Forward
            if (keysPressed["s"]) velocity = -1.0; // Backward
            if (keysPressed["a"]) turn = -1.0;     // Turn Left
            if (keysPressed["d"]) turn = 1.0;      // Turn Right

            // Arrow Keys for Robotic Arm Movement
            let shoulder = 0;
            let elbow = 0;
            if (keysPressed["arrowup"]) shoulder = 1.0;
            if (keysPressed["arrowdown"]) shoulder = -1.0;
            if (keysPressed["arrowleft"]) elbow = -1.0;
            if (keysPressed["arrowright"]) elbow = 1.0;

            // Operational Action Mapping keys
            const buttonA = keysPressed["z"] || false; // Open Gripper
            const buttonB = keysPressed["x"] || false; // Close Gripper
            const buttonX = keysPressed["m"] || false; // Manual Mode Toggle
            const buttonY = keysPressed["space"] || keysPressed[" "] || false; // Spacebar for Emergency E-STOP

            // Set control state 
            setControlState({
                drive: {
                    velocity: velocity,
                    turn: turn,
                },
                arm: {
                    shoulder: shoulder,
                    elbow: elbow,
                    gripper: buttonA ? 1 : buttonB ? -1 : 0,
                },
                mode: buttonX ? "manual" : "idle",
                estop: buttonY,
                timestamp: Date.now(),
            });
            
            // for debugging in browser console
            console.log("Keyboard Control State Updated: ", {
                drive: { velocity, turn },
                arm: { shoulder, elbow, gripper: buttonA ? "OPEN" : buttonB ? "CLOSE" : "NEUTRAL" },
                mode: buttonX ? "MANUAL" : "IDLE",
                estop: buttonY,
            });

            animationFrameId = requestAnimationFrame(pollKeyboardLoop);
        };

        // Kickstart the execution cycle
        animationFrameId = requestAnimationFrame(pollKeyboardLoop);

        // Finisher
        return () => {
            cancelAnimationFrame(animationFrameId);
            window.removeEventListener("keydown", handleKeyDown);
            window.removeEventListener("keyup", handleKeyUp);
        };
    }, []);
    
    return controlState;
}