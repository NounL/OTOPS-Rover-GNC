// src/hooks/useGamepadreplacement.ts
// Logitech F310 (XInput mode) control scheme:
//   A            toggle DRIVE / ARM mode
//   Left stick   DRIVE: Y = linear velocity (X ignored)
//                ARM:   Y controls the joint currently assigned to it
//   Right stick  DRIVE: X = angular velocity (Y ignored)
//                ARM:   Y controls the joint currently assigned to it
//   X            cycle the joint assigned to the left stick
//   B            cycle the joint assigned to the right stick
//   RB / LB      increment / decrement the global speed scale
import { useState, useEffect } from "react";
import { type ControlState, type ArmStruct, type Mode } from "../types/control";

const ARM_JOINTS: (keyof ArmStruct)[] = ["base", "shoulder", "elbow", "wrist", "gripper"];

const SPEED_SCALE_MIN = 0.1;
const SPEED_SCALE_MAX = 1.0;
const SPEED_SCALE_STEP = 0.1;
const SPEED_SCALE_DEFAULT = 0.5;

const ZERO_ARM: ArmStruct = { base: 0, shoulder: 0, elbow: 0, wrist: 0, gripper: 0 };

export function useGamepad() {
    const [controlState, setControlState] = useState<ControlState | null>(null);

    useEffect(() => {
        let animationFrameId: number;

        let mode: Mode = "DRIVE";
        let speedScale = SPEED_SCALE_DEFAULT;
        let leftJoint = 0;   // index into ARM_JOINTS, starts on Base
        let rightJoint = 1;  // index into ARM_JOINTS, starts on Shoulder

        // Previous button states, needed so mode/joint/speed changes fire once
        // per press instead of every frame the button is held.
        let prevModeButton = false;
        let prevLeftCycleButton = false;
        let prevRightCycleButton = false;
        let prevSpeedUpButton = false;
        let prevSpeedDownButton = false;

        const pollGamepadLoop = () => {
            const gamepads = navigator.getGamepads();
            const gamepad = gamepads[0];

            if (gamepad) {
                const leftStickY = gamepad.axes[1] || 0;
                const rightStickX = gamepad.axes[2] || 0;
                const rightStickY = gamepad.axes[3] || 0;

                const buttonA = gamepad.buttons[0]?.pressed || false;
                const buttonB = gamepad.buttons[1]?.pressed || false;
                const buttonX = gamepad.buttons[2]?.pressed || false;
                const bumperLeft = gamepad.buttons[4]?.pressed || false;
                const bumperRight = gamepad.buttons[5]?.pressed || false;

                if (buttonA && !prevModeButton) {
                    mode = mode === "DRIVE" ? "ARM" : "DRIVE";
                }
                prevModeButton = buttonA;

                if (buttonX && !prevLeftCycleButton) {
                    leftJoint = (leftJoint + 1) % ARM_JOINTS.length;
                }
                prevLeftCycleButton = buttonX;

                if (buttonB && !prevRightCycleButton) {
                    rightJoint = (rightJoint + 1) % ARM_JOINTS.length;
                }
                prevRightCycleButton = buttonB;

                if (bumperRight && !prevSpeedUpButton) {
                    speedScale = Math.min(SPEED_SCALE_MAX, speedScale + SPEED_SCALE_STEP);
                }
                prevSpeedUpButton = bumperRight;

                if (bumperLeft && !prevSpeedDownButton) {
                    speedScale = Math.max(SPEED_SCALE_MIN, speedScale - SPEED_SCALE_STEP);
                }
                prevSpeedDownButton = bumperLeft;

                const arm: ArmStruct = { ...ZERO_ARM };
                arm[ARM_JOINTS[leftJoint]] = -leftStickY;
                arm[ARM_JOINTS[rightJoint]] = -rightStickY;

                setControlState({
                    mode,
                    speed_scale: Number(speedScale.toFixed(2)),
                    drive: mode === "DRIVE"
                        ? { linear_velocity: -leftStickY, angular_velocity: rightStickX }
                        : { linear_velocity: 0, angular_velocity: 0 },
                    arm: mode === "ARM" ? arm : { ...ZERO_ARM },
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
