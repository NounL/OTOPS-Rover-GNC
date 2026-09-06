export type Mode = "DRIVE" | "ARM";

export interface DriveStruct {
  linear_velocity: number;
  angular_velocity: number;
}

export interface ArmStruct {
  base: number;
  elbow: number;
  rotate: number;
  wrist: number;
  gripper: number;
}

export interface ControlState {
  mode: Mode;
  speed_scale: number;
  drive: DriveStruct;
  arm: ArmStruct;
  timestamp: number;
}
