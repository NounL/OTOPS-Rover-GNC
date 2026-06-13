export interface Drive {
  velocity: number;
  turn: number;
}

export interface Arm {
  shoulder: number;
  elbow: number;
  gripper: number;
}

export interface ControlState {
  drive: Drive;
  arm: Arm;
  mode: string;
  estop: boolean;
  timestamp: number;
}