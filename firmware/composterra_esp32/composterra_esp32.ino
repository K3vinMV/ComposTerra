
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "secrets.h"

const int ID_LOTE = 8;         
const int PIN_DS18B20 = 4;
const int PIN_HUMEDAD = 34;    
const int PIN_PH = 33;

OneWire oneWire(PIN_DS18B20);
DallasTemperature ds(&oneWire);
WiFiClientSecure red;
PubSubClient mqtt(red);

void setup() {
  Serial.begin(115200);
  ds.begin();

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi OK");

  red.setCACert(AWS_ROOT_CA);
  red.setCertificate(DEVICE_CERT);
  red.setPrivateKey(DEVICE_KEY);
  mqtt.setServer(IOT_ENDPOINT, 8883);
}

void loop() {
  if (!mqtt.connected()) {
    Serial.print("Conectando a AWS... ");
    if (mqtt.connect(IOT_CLIENT_ID)) Serial.println("OK");
    else { Serial.printf("falló (%d)\n", mqtt.state()); delay(5000); return; }
  }
  mqtt.loop();

  ds.requestTemperatures();
  float temp = ds.getTempCByIndex(0);

  // Capacitivo: ~2600 mV seco, ~1200 mV en agua
  float hum = constrain(map(analogReadMilliVolts(PIN_HUMEDAD), 2600, 1200, 0, 100), 0, 100);

  // PH-4502C con divisor 2/3: ~1670 mV en el pin = pH 7
  float volts = analogReadMilliVolts(PIN_PH) / 1000.0 * 1.5;
  float ph = constrain(7 + (2.5 - volts) * 3.5, 0, 14);

  char msg[128];
  snprintf(msg, sizeof(msg),
           "{\"id_lote\":%d,\"temperatura\":%.2f,\"humedad\":%.2f,\"ph\":%.2f}",
           ID_LOTE, temp, hum, ph);
  char topico[40];
  snprintf(topico, sizeof(topico), "composterra/sensores/%d", ID_LOTE);
  mqtt.publish(topico, msg);
  Serial.println(msg);

  delay(10000);
}
