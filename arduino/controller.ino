// Mega_Rover_Controller.ino
// Mega 5-stepper + 5-encoder (4 ext interrupts + 1 polled) + BMP280 + MPU6050 + GPS
// Libraries required: Adafruit_BMP280, Adafruit_Sensor

/*
Note from Nouwen Laroche:
consider making all the serial communication use JSON.
Will be more consisent and universal for further development.

#####################################################################
TODO:

- poll the multiple gas sensors. currently only accounts for one
- format serial communication to JSON
- test GPS serial read format -- will use TinyGPSPlus.h Jul 07 2026 ,Nouwen
- test BMP sensor
- add MPU?

*/

#include <Wire.h>
#include <SoftwareSerial.h>
#include <Adafruit_BMP280.h>
#include <ArduinoJson.h>

// CONFIG MOTORS
const int NUM_MOTORS = 5;
const uint32_t DEFAULT_STEP_INTERVAL_US = 1000;
const uint16_t STEP_PULSE_US = 10;

// MOTORS PINOUT (Mega mapping, conflict-free with I2C SDA=D20 SCL=D21)
// Step / Dir / Enable
const int STEP_PINS[NUM_MOTORS]   = {22, 23, 24, 25, 26}; 
const int DIR_PINS[NUM_MOTORS]    = {27, 28, 29, 30, 31};
const int ENABLE_PINS[NUM_MOTORS] = {32, 33, 34, 35, 36};

// Encoder pins
// ENC_A 0..3 use external interrupts on Mega pins 2,3,18,19
// ENC_A4 uses D50 and is polled to avoid I2C conflict (20 & 21 are used for I2C)
const int ENC_A_PINS[NUM_MOTORS] = {2, 3, 18, 19, 50}
const int ENC_B_PINS[NUM_MOTORS] = {40, 41, 42, 43, 44};

// Sensors / GPS pins
const int GPS_PPS = 49;
const int GPS_RX  = 10;
const int GPS_TX  = 11;
const int SOIL_PIN = A0;
const int AIR_PIN  = A3; // add more as required

// GLOBALS
//Motor Variables
volatile long encoderCount[NUM_MOTORS] = {0};
volatile long remainingSteps[NUM_MOTORS] = {0};
long currentPos[NUM_MOTORS] = {0};
int dirState[NUM_MOTORS] = {1,1,1,1,1};
bool motorActive[NUM_MOTORS] = {false};

unsigned long nextStepTimeUs[NUM_MOTORS] = {0};
uint32_t stepIntervalUs[NUM_MOTORS] = {DEFAULT_STEP_INTERVAL_US, DEFAULT_STEP_INTERVAL_US, DEFAULT_STEP_INTERVAL_US, DEFAULT_STEP_INTERVAL_US, DEFAULT_STEP_INTERVAL_US};

// Sensor Init
SoftwareSerial gpsSerial(GPS_RX, GPS_TX);
Adafruit_BMP280 bmp;

unsigned long lastSensorMillis = 0;
const unsigned long SENSOR_INTERVAL = 1000;

// FORWARD DECLARATIONS (ISRs) "Interrupt Service Routines"
void encoderISR0();
void encoderISR1();
void encoderISR2();
void encoderISR3();

// HELPER: quadrature handling (Resolves encoder count addition or subtraction)
inline void handleEncoderChange(int idx) {
  bool a = digitalRead(ENC_A_PINS[idx]);
  bool b = digitalRead(ENC_B_PINS[idx]);
  if (a == b) encoderCount[idx]++; else encoderCount[idx]--;
}

// ISR implementations for A pins 0..3
void encoderISR0() { handleEncoderChange(0); }
void encoderISR1() { handleEncoderChange(1); }
void encoderISR2() { handleEncoderChange(2); }
void encoderISR3() { handleEncoderChange(3); }

// Polling state for encoder 4
bool lastEnc4A = HIGH;

void attachEncoderISRs() {
  for (int i = 0; i < NUM_MOTORS; ++i) { // setup pins for reading
    pinMode(ENC_A_PINS[i], INPUT_PULLUP);
    pinMode(ENC_B_PINS[i], INPUT_PULLUP);
  }
  attachInterrupt(digitalPinToInterrupt(ENC_A_PINS[0]), encoderISR0, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_A_PINS[1]), encoderISR1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_A_PINS[2]), encoderISR2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_A_PINS[3]), encoderISR3, CHANGE);
  // ENC_A_PINS[4] will be polled in loop to avoid I2C pin conflicts // surely this can be resolved?
  Serial.println("ENC: attached 4 external-interrupt ISRs; encoder 4 will be polled.");
}

void setup() {
  Serial.begin(115200);
  Wire.begin(); // Mega: SDA=D20, SCL=D21

  Serial.println("Mega Combined Controller starting...");

  for (int i = 0; i < NUM_MOTORS; ++i) {
    pinMode(STEP_PINS[i], OUTPUT);
    pinMode(DIR_PINS[i], OUTPUT);
    pinMode(ENABLE_PINS[i], OUTPUT);
    digitalWrite(STEP_PINS[i], LOW);
    digitalWrite(ENABLE_PINS[i], LOW);
    motorActive[i] = false;
    remainingSteps[i] = 0;
    nextStepTimeUs[i] = micros();
  }

  gpsSerial.begin(9600);
  pinMode(GPS_PPS, INPUT);

  if (bmp.begin(0x76)) {
    Serial.println("BMP280 found at 0x76");
  } else if (bmp.begin(0x77)) {
    Serial.println("BMP280 found at 0x77");
  } else {
    Serial.println("BMP280 not found at 0x76 or 0x77");
  }

  if (initMPU6050()) {
    Serial.println("MPU6050 OK");
  } else {
    Serial.println("MPU6050 not responding");
  }

  attachEncoderISRs();
  lastEnc4A = digitalRead(ENC_A_PINS[4]);

  Serial.println("Ready. Commands: M,id,dir,steps  S  R  ENC  !");
}

// COMMAND PARSER
// takes the received serial command, decodes, and executes
void parseCommand(const String &cmd) {
  String s = cmd;
  s.trim();
  if (s.length() == 0) return; // No command

  if (s.charAt(0) == 'M') { // Start at "M" motor command
    int firstCommaIndex = s.indexOf(',');
    int secondCommaIndex = s.indexOf(',', firstCommaIndex + 1);
    int thirdCommaIndex = s.indexOf(',', secondCommaIndex + 1);
	
    if (firstCommaIndex > 0 && secondCommaIndex > firstCommaIndex && c > b) { // Check id there is a value for a,b,c then add to id, dir, steps
      int id = s.substring(firstCommaIndex + 1, b).toInt();
      int dir = s.substring(secondCommaIndex + 1, c).toInt();
      long steps = s.substring(thirdCommaIndex + 1).toInt();
	  
      if (id >= 0 && id < NUM_MOTORS && steps > 0) { // check for a valid id and steps
        remainingSteps[id] = steps;
        dirState[id] = (dir == 0 ? -1 : 1);
        motorActive[id] = true;
        nextStepTimeUs[id] = micros();
        Serial.print("ACK:M,");
        Serial.print(id);
        Serial.print(",DIR:");
        Serial.print(dirState[id]);
        Serial.print(",STEPS:");
        Serial.println(steps);
		
      } else {
        Serial.println("ERR: invalid motor command");
      }
    } else {
      Serial.println("ERR: bad M command format");
    }
  } else if (s.startsWith("ENC")) { // Request Encoder Data
    String token = "";
    int comma = s.indexOf(',');
    if (comma > 0) token = s.substring(comma + 1);
    else {
      int sp = s.indexOf(' ');
      if (sp > 0) token = s.substring(sp + 1);
    }
    token.trim();
    if (token.length() == 0 || token.equalsIgnoreCase("ALL")) { // Return all encoder data
      for (int j = 0; j < NUM_MOTORS; ++j) {
        Serial.print("ENC:");
        Serial.print(encoderCount[j]);
        Serial.print(",");
      }
	  Serial.println();
    } else {
      int id = token.toInt(); // Return Specific Encoder
      if (id >= 0 && id < NUM_MOTORS) {
        Serial.print("ENC:");
        Serial.print(",");
        Serial.println(encoderCount[id]);
      } else {
        Serial.println("ERR: bad ENC id");
      }
    }
  } else if (s == "S") { // Request Sensor Data
    printSensorData();
  } else if (s == "R") { // Request Motor Status
    printMotorStatus();
  } else if (s == "!") { // Emergency Stop Signal
    for (int i = 0; i < NUM_MOTORS; ++i) {
      remainingSteps[i] = 0;
      motorActive[i] = false;
    }
    Serial.println("ACK:EMERGENCY_STOP");
  } else {
    Serial.println("ERR: unknown command");
  }
}

// SENSORS
bool initMPU6050() { //note: need to redefine the return
  const int MPU_ADDR = 0x68;
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  byte err = Wire.endTransmission();
  
  // Set accelerometer range to ±2g (most stable) from https://controllerstech.com/mpu6050-arduino-tutorial/
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C);           // ACCEL_CONFIG register
  Wire.write(0x00);           // ±2g range
  Wire.endTransmission(true);
  return (err == 0);
}

void readGyroscope(int16_t &ax, int16_t &ay, int16_t &az,
                   int16_t &gx, int16_t &gy, int16_t &gz) {
  const int MPU_ADDR = 0x68;
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true); // note check MPU address values
  ax = (Wire.read() << 8) | Wire.read();
  ay = (Wire.read() << 8) | Wire.read();
  az = (Wire.read() << 8) | Wire.read();
  Wire.read(); Wire.read();
  gx = (Wire.read() << 8) | Wire.read();
  gy = (Wire.read() << 8) | Wire.read();
  gz = (Wire.read() << 8) | Wire.read();
}

int readSoilMoisturePercent() {
  int raw = analogRead(SOIL_PIN);
  int percent = map(raw, 1023, 0, 0, 100);
  return constrain(percent, 0, 100);
}

int readAirRaw() {
  return analogRead(AIR_PIN);
}

void readGPS() {
  while (gpsSerial.available()) {
    char c = gpsSerial.read();
    Serial.write(c);
  }
}

void printSensorData() {
  int soil = readSoilMoisturePercent();
  int air = readAirRaw();
  float pressure = NAN;
  float tempC = NAN;
  tempC = bmp.readTemperature();
  pressure = bmp.readPressure();
  int16_t ax, ay, az, gx, gy, gz;
  readGyroscope(ax, ay, az, gx, gy, gz);

  Serial.print("Time(s):"); Serial.println(millis() / 1000);
  Serial.print("Soil%:"); Serial.println(soil);
  Serial.print("AirRaw:"); Serial.println(air);
  if (pressure > 0) {
    Serial.print("BMP_Pa:"); Serial.println(pressure);
    Serial.print("BMP_C:"); Serial.println(tempC);
  } else {
    Serial.println("BMP: not present or read failed");
  }
  Serial.print("MPU Accel X,Y,Z:"); Serial.print(ax); Serial.print(","); Serial.print(ay); Serial.print(","); Serial.println(az);
  Serial.print("MPU Gyro  X,Y,Z:"); Serial.print(gx); Serial.print(","); Serial.print(gy); Serial.print(","); Serial.println(gz);
  Serial.print("GPS_PPS:"); Serial.println(digitalRead(GPS_PPS) ? "HIGH" : "LOW");
}

void printMotorStatus() {
  for (int i = 0; i < NUM_MOTORS; ++i) {
    Serial.print("M"); Serial.print(i);
    Serial.print(":POS="); Serial.print(currentPos[i]);
    Serial.print(",REM="); Serial.print(remainingSteps[i]);
    Serial.print(",DIR="); Serial.print(dirState[i] > 0 ? "F" : "R");
    Serial.print(",ACT="); Serial.println(motorActive[i] ? "1" : "0");
  }
}

// MAIN LOOP
void loop() {

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) parseCommand(line);
  }

  readGPS();

  // Poll encoder 4 (polled A pin) NOTE: this must be able to be added to interrupt as well
  bool curA4 = digitalRead(ENC_A_PINS[4]);
  if (curA4 != lastEnc4A) {
    bool b = digitalRead(ENC_B_PINS[4]);
    if (curA4 == b) encoderCount[4]++; else encoderCount[4]--;
    lastEnc4A = curA4;
  }

  uint32_t nowUs = micros();
  for (int i = 0; i < NUM_MOTORS; ++i) {
    if (motorActive[i] && remainingSteps[i] > 0) {
      if ((long)(nowUs - nextStepTimeUs[i]) >= 0) {
        digitalWrite(DIR_PINS[i], dirState[i] > 0 ? HIGH : LOW);
        digitalWrite(STEP_PINS[i], HIGH);
        delayMicroseconds(STEP_PULSE_US);
        digitalWrite(STEP_PINS[i], LOW);

        remainingSteps[i]--;
        currentPos[i] += (dirState[i] > 0 ? 1 : -1);

        nextStepTimeUs[i] = nowUs + stepIntervalUs[i];

        if (remainingSteps[i] == 0) {
          motorActive[i] = false;
          long enc = encoderCount[i];
          Serial.print("DONE:");
          Serial.print(i);
          Serial.print(",POS:");
          Serial.print(currentPos[i]);
          Serial.print(",ENC:");
          Serial.println(enc);
        }
      }
    }
  }

  if (millis() - lastSensorMillis >= SENSOR_INTERVAL) {
    lastSensorMillis = millis();
    // printSensorData(); // uncomment to broadcast periodically
  }
}
