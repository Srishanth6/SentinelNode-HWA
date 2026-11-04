// SentinelNode ESP32 firmware (prototype, not yet bench-tested)
// Sensors: INA219 (I2C 0x40) rail V/I, MLX90614 (I2C 0x5A) hot-spot temp,
// DS18B20 (1-Wire GPIO4) ambient, MPU6050 (I2C 0x68) vibration, ripple on ADC1 GPIO34.
// Libraries: Adafruit_INA219, Adafruit_MLX90614, OneWire, DallasTemperature, Adafruit_MPU6050, ArduinoJson
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Adafruit_MLX90614.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_MPU6050.h>
#include <ArduinoJson.h>

#define PIN_ONEWIRE 4
#define PIN_RIPPLE 34
#define PIN_LED 25
#define PIN_BUZZER 26
const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASS = "YOUR_PASS";
const char* SERVER = "http://192.168.1.10:8000/api/readings";
const char* NODE_ID = "node-01";

Adafruit_INA219 ina;
Adafruit_MLX90614 mlx;
OneWire ow(PIN_ONEWIRE);
DallasTemperature ds(&ow);
Adafruit_MPU6050 mpu;

// Threshold rules mirrored from sentinelnode/rules.py
const float TEMP_HOT_C = 85.0, DELTA_T_C = 30.0, VIB_RMS_G = 1.5, RIPPLE_MV = 250.0;

float rippleMv() {  // peak-to-peak over 200 samples of AC-coupled input
  int mn = 4095, mx = 0;
  for (int i = 0; i < 200; i++) { int v = analogRead(PIN_RIPPLE); mn = min(mn, v); mx = max(mx, v); delayMicroseconds(100); }
  return (mx - mn) * 3300.0 / 4095.0;
}

float vibrationRmsG() {
  double acc = 0; const int N = 100;
  for (int i = 0; i < N; i++) {
    sensors_event_t a, g, t; mpu.getEvent(&a, &g, &t);
    double m = sqrt(a.acceleration.x*a.acceleration.x + a.acceleration.y*a.acceleration.y + a.acceleration.z*a.acceleration.z) / 9.81 - 1.0;
    acc += m * m; delay(2);
  }
  return sqrt(acc / N);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT); pinMode(PIN_BUZZER, OUTPUT);
  Wire.begin(21, 22);
  ina.begin(); mlx.begin(); ds.begin(); mpu.begin();
  analogReadResolution(12);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

void loop() {
  float v = ina.getBusVoltage_V(), i = ina.getCurrent_mA();
  float hot = mlx.readObjectTempC();
  ds.requestTemperatures(); float amb = ds.getTempCByIndex(0);
  float vib = vibrationRmsG(), rip = rippleMv();
  bool alert = hot > TEMP_HOT_C || (hot - amb) > DELTA_T_C || vib > VIB_RMS_G || rip > RIPPLE_MV;
  digitalWrite(PIN_LED, alert); digitalWrite(PIN_BUZZER, alert);

  StaticJsonDocument<256> doc;
  doc["node_id"] = NODE_ID; doc["voltage_v"] = v; doc["current_ma"] = i;
  doc["temp_hot_c"] = hot; doc["temp_amb_c"] = amb; doc["vibration_g"] = vib; doc["ripple_mv"] = rip;
  String body; serializeJson(doc, body);
  Serial.println(body);
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http; http.begin(SERVER); http.addHeader("Content-Type", "application/json");
    http.POST(body); http.end();
  }
  delay(5000);
}
