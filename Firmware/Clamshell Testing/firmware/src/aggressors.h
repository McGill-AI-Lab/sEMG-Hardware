/*
 * =============================================================================
 *  aggressors.h  —  deliberately noisy ESP32 activity for Experiment F
 * =============================================================================
 *
 *  An "aggressor" is any activity that might couple electrical noise into
 *  the ADS1298: the WiFi radio transmitting, the CPU running flat out, etc.
 *  Experiment F (clamshell_validation.md, section 7) switches these on one at
 *  a time and checks whether the noise floor changes.
 *
 *  The PC turns them on and off with the text commands
 *      WIFI OFF | WIFI AP | WIFI SCAN        and        LOAD IDLE | LOAD BUSY
 *
 *  WIFI AP    : the ESP32 becomes a WiFi access point. It then transmits a
 *               short "beacon" packet about 10 times per second (every
 *               102.4 ms). That is the "idle connected" radio condition.
 *  WIFI SCAN  : the ESP32 scans for networks again and again. Active scanning
 *               transmits "probe request" packets on every WiFi channel, so
 *               the radio transmits almost continuously. That is the
 *               "continuous TX" condition, and it needs no router.
 *  LOAD BUSY  : a background task keeps CPU core 0 at ~100 % doing math.
 * =============================================================================
 */
#pragma once                                 // include this header only once per build

#include <Arduino.h>                         // basic Arduino types and functions

void aggressorSetWifi(const char *mode);     // mode = "OFF", "AP" or "SCAN"; unknown text -> treated as OFF
void aggressorSetLoad(const char *mode);     // mode = "IDLE" or "BUSY"
const char *aggressorWifiName();             // the current WiFi mode as text (for replies to the PC)
const char *aggressorLoadName();             // the current CPU-load mode as text
