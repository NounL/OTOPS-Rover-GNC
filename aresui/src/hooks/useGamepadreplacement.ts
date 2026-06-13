// imports

import { useState, useEffect } from "react";
import { type ControlState } from "../types/control";


// Hook to manage gamepad input and control state
export function useGamepad() {
    const [controlState, setControlState] = useState<ControlState | null>(null);

    useEffect(() => {
        let animationFrameId: number;

        const pollGamepadLoop = () => {
            const gamepads = navigator.getGamepads();
            const mainGamepad = gamepads[0]; // Assuming the first gamepad is the one we want to use

            if (mainGamepad) {

                const leftStickX = mainGamepad.axes[0] || 0; // Left stick horizontal
                const leftStickY = mainGamepad.axes[1] || 0; // Left stick vertical
                const rightStickX = mainGamepad.axes[2] || 0; // Right stick horizontal
                const rightStickY = mainGamepad.axes[3] || 0; // Right stick vertical
                const buttonA = mainGamepad.buttons[0]?.pressed || false; // A button
                const buttonB = mainGamepad.buttons[1]?.pressed || false; // B button
                const buttonX = mainGamepad.buttons[2]?.pressed || false; // X button
                const buttonY = mainGamepad.buttons[3]?.pressed || false; // Y button
        
                setControlState({ 
                    drive: {
                        velocity: -leftStickY, // Invert Y axis for typical forward/backward control
                        turn: leftStickX, // Use horizontal axis for turning
                    },
                    arm: {
                        shoulder: rightStickY, // Use right stick vertical for shoulder control
                        elbow: rightStickX, // Use right stick horizontal for elbow contro
                        gripper: buttonA ? 1 : buttonB ? -1 : 0, // A to open, B to close, otherwise neutral
                    },
                    mode: buttonX ? "manual" : "idle", 
                    estop: buttonY, // Y button for emergency stop
                    timestamp: Date.now(),
                });
            }
            animationFrameId = requestAnimationFrame(pollGamepadLoop);
        };

        animationFrameId = requestAnimationFrame(pollGamepadLoop);

        return () => {
            cancelAnimationFrame(animationFrameId);
        };
    }, []);
    return controlState;
}