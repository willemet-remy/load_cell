#include <Arduino.h>
#include <HX711.h>
#include <ArduinoJson.h>

// Pins for the 4 load cells (Data, Clock)
const int DT_PINS[4]  = {16, 18, 22, 32};
const int SCK_PINS[4] = {17, 19, 23, 33};

HX711 scales[4];

// Current calibration factors and offsets (can be updated via serial)
float calibration_factors[4] = {1.0, 1.0, 1.0, 1.0};
long offsets[4] = {0, 0, 0, 0};

unsigned long lastTime = 0;
const unsigned long timerDelay = 1000; // 1Hz data streaming

void initScales() {
  for (int i = 0; i < 4; i++) {
    scales[i].begin(DT_PINS[i], SCK_PINS[i]);
    scales[i].set_scale(calibration_factors[i]);
    scales[i].set_offset(offsets[i]);
  }
}

// Tare a specific scale and send response
void tareScale(int scaleIdx) {
  scales[scaleIdx].tare();
  offsets[scaleIdx] = scales[scaleIdx].get_offset();
  
  JsonDocument resp;
  resp["status"] = "TARED";
  resp["scale"] = scaleIdx;
  resp["offset"] = offsets[scaleIdx];
  serializeJson(resp, Serial);
  Serial.println();
}

// Calibrate a specific scale using a known weight and send response
void calibrateScale(int scaleIdx, float known_weight) {
  if (known_weight > 0) {
    // get_value(10) gets average of 10 raw readings minus the offset
    long raw_val = scales[scaleIdx].get_value(10); 
    calibration_factors[scaleIdx] = (float)raw_val / known_weight;
    scales[scaleIdx].set_scale(calibration_factors[scaleIdx]);
    
    JsonDocument resp;
    resp["status"] = "CALIBRATED";
    resp["scale"] = scaleIdx;
    resp["factor"] = calibration_factors[scaleIdx];
    serializeJson(resp, Serial);
    Serial.println();
  }
}

// Force a calibration factor and offset from PC config
void setCalibration(int scaleIdx, float factor, long offset) {
  calibration_factors[scaleIdx] = factor;
  offsets[scaleIdx] = offset;
  scales[scaleIdx].set_scale(factor);
  scales[scaleIdx].set_offset(offset);
  
  JsonDocument resp;
  resp["status"] = "CALIBRATION_SET";
  resp["scale"] = scaleIdx;
  serializeJson(resp, Serial);
  Serial.println();
}

void processSerialCommand() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() == 0) return;

    // Incoming JSON command format:
    // {"cmd": "TARE", "scale": 0}
    // {"cmd": "CALIBRATE", "scale": 0, "weight": 500.0}
    // {"cmd": "SET_CALIBRATION", "scale": 0, "factor": 250.5, "offset": 8345}
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, cmd);
    
    if (error) {
      Serial.println("{\"error\": \"Invalid JSON command\"}");
      return;
    }

    String action = doc["cmd"].as<String>();
    int scaleIdx = doc["scale"].as<int>();

    if (scaleIdx >= 0 && scaleIdx < 4) {
      if (action == "TARE") {
        tareScale(scaleIdx);
      } 
      else if (action == "CALIBRATE") {
        calibrateScale(scaleIdx, doc["weight"].as<float>());
      }
      else if (action == "SET_CALIBRATION") {
        setCalibration(scaleIdx, doc["factor"].as<float>(), doc["offset"].as<long>());
      }
    }
  }
}

void sendData() {
  JsonDocument doc;
  doc["type"] = "DATA";
  doc["timestamp"] = millis();
  
  JsonArray rawArr = doc["raw"].to<JsonArray>();
  JsonArray weightArr = doc["weight"].to<JsonArray>();

  for (int i = 0; i < 4; i++) {
    if (scales[i].is_ready()) {
      long raw = scales[i].read(); // absolute raw reading
      float weight = scales[i].get_units(1); // 1 sample with applied scale/offset
      rawArr.add(raw);
      weightArr.add(weight);
    } else {
      rawArr.add(0);
      weightArr.add(0.0);
    }
  }

  serializeJson(doc, Serial);
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  initScales();
}

void loop() {
  processSerialCommand();

  unsigned long currentMillis = millis();
  if (currentMillis - lastTime >= timerDelay) {
    sendData();
    lastTime = currentMillis;
  }
}