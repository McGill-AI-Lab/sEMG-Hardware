/*
 * =============================================================================
 *  aggressors.cpp  —  WiFi and CPU-load "noise sources" for Experiment F
 * =============================================================================
 *
 *  LIBRARIES AND CONCEPTS USED
 *  ---------------------------
 *  - WiFi.h (Arduino-ESP32): the global "WiFi" object controls the radio.
 *      WiFi.mode(WIFI_OFF / WIFI_STA / WIFI_AP)   choose radio role or turn it off
 *      WiFi.softAP(ssid, password)                start an access point
 *      WiFi.scanNetworks(async, hidden, passive, ms_per_channel)
 *                                                 scan all channels; "passive=false"
 *                                                 means ACTIVE scanning, which transmits
 *      WiFi.scanDelete()                          free the scan result memory
 *
 *  - FreeRTOS tasks. The ESP32-S3 has two CPU cores (core 0 and core 1) and
 *    runs a small operating system called FreeRTOS. A "task" is like a
 *    separate little program with its own loop, scheduled by FreeRTOS.
 *    Arduino's setup()/loop() run in a task on core 1. We create our
 *    aggressor tasks on core 0 so they do not steal time from the ADS1298
 *    capture loop on core 1 (we want to test electrical coupling, not
 *    starve the capture of CPU).
 *
 *      xTaskCreatePinnedToCore(function, name, stackBytes, arg, priority,
 *                              &handle, core)
 *      vTaskDelete(NULL)   a task deletes itself when its function finishes
 *
 *    Priority 0 is the same as FreeRTOS's "idle" task. FreeRTOS shares the
 *    core between equal-priority tasks (time slicing), so the idle task still
 *    runs now and then and the "task watchdog" (which reboots the chip if
 *    the idle task never runs) stays happy, while our task still uses almost
 *    all the remaining CPU time.
 *
 *  STOPPING A TASK SAFELY
 *  ----------------------
 *  We never kill a task from outside while it is in the middle of a WiFi
 *  call. Instead we clear a "keep running" flag, the task notices it at the
 *  end of its current iteration, sets its "alive" flag to false and deletes
 *  itself. The caller waits (with a time limit) for "alive" to go false.
 * =============================================================================
 */
#include "aggressors.h"                      // our declarations
#include <WiFi.h>                            // Arduino-ESP32 WiFi API

static volatile bool s_loadRun   = false;    // true while the CPU-load task should keep going
static volatile bool s_loadAlive = false;    // true while the CPU-load task exists
static volatile bool s_scanRun   = false;    // true while the WiFi-scan task should keep going
static volatile bool s_scanAlive = false;    // true while the WiFi-scan task exists
static const char   *s_wifiName  = "OFF";    // current WiFi mode, as text
static const char   *s_loadName  = "IDLE";   // current CPU-load mode, as text

/*
 * -----------------------------------------------------------------------------
 *  loadTask()  —  burn CPU time on core 0 until told to stop
 * -----------------------------------------------------------------------------
 *  "void *" is a generic pointer argument FreeRTOS passes to every task; we
 *  do not need it. The "volatile float acc" stops the compiler from
 *  optimising the pointless math away.
 * -----------------------------------------------------------------------------
 */
static void loadTask(void *) {
  volatile float acc = 1.0f;                 // dummy accumulator the compiler must really compute
  while (s_loadRun) {                        // keep working until aggressorSetLoad("IDLE") clears the flag
    for (int i = 0; i < 1000; i++) {         // a short burst of floating-point work ...
      acc = acc * 1.0000001f + 0.5f;         // ... that never ends up anywhere useful
    }
  }
  s_loadAlive = false;                       // tell the caller we are finished
  vTaskDelete(NULL);                         // delete this task (NULL = "myself")
}

/*
 * -----------------------------------------------------------------------------
 *  scanTask()  —  run active WiFi scans back to back until told to stop
 * -----------------------------------------------------------------------------
 *  Each blocking scan visits all channels for 120 ms each (~1.5 s total)
 *  and transmits probe requests on each, so the radio is busy nearly all the
 *  time. scanDelete() frees the result list between scans.
 * -----------------------------------------------------------------------------
 */
static void scanTask(void *) {
  while (s_scanRun) {                                   // until told to stop ...
    WiFi.scanNetworks(false, true, false, 120);         // blocking, include hidden, ACTIVE (transmitting), 120 ms/channel
    WiFi.scanDelete();                                  // free memory used by the results
  }
  s_scanAlive = false;                                  // signal that the task is done
  vTaskDelete(NULL);                                    // delete this task
}

/*
 * -----------------------------------------------------------------------------
 *  waitWhileTrue()  —  wait until a flag goes false, at most timeoutMs
 * -----------------------------------------------------------------------------
 */
static void waitWhileTrue(volatile bool &flag, uint32_t timeoutMs) {
  uint32_t t0 = millis();                               // remember when we started waiting
  while (flag && (millis() - t0) < timeoutMs) {         // still set and not yet timed out ...
    delay(10);                                          // ... sleep 10 ms and look again
  }
}

/*
 * -----------------------------------------------------------------------------
 *  stopScanTask()  —  stop the WiFi-scan task if it is running
 * -----------------------------------------------------------------------------
 */
static void stopScanTask() {
  if (!s_scanAlive) {                                   // nothing to stop
    return;                                             // leave immediately
  }
  s_scanRun = false;                                    // ask the task to finish after the current scan
  waitWhileTrue(s_scanAlive, 5000);                     // a scan can take ~1.5 s; wait up to 5 s
}

/*
 * -----------------------------------------------------------------------------
 *  aggressorSetWifi()  —  switch the radio to OFF, AP or SCAN
 * -----------------------------------------------------------------------------
 *  strcmp(a, b) compares two C strings and returns 0 when they are equal.
 * -----------------------------------------------------------------------------
 */
void aggressorSetWifi(const char *mode) {
  stopScanTask();                                       // always stop scanning before changing the radio mode

  if (strcmp(mode, "AP") == 0) {                        // access-point mode requested
    WiFi.mode(WIFI_AP);                                 // radio becomes an access point
    WiFi.softAP("clamshell-noise-test", "clamshell123");  // start beaconing (password must be >= 8 characters)
    s_wifiName = "AP";                                  // remember the mode
  } else if (strcmp(mode, "SCAN") == 0) {               // continuous transmit requested
    WiFi.softAPdisconnect(true);                        // stop any access point that may be running
    WiFi.mode(WIFI_STA);                                // "station" mode is needed for scanning
    WiFi.disconnect();                                  // make sure we are not trying to join a network
    s_scanRun = true;                                   // the task should keep scanning
    s_scanAlive = true;                                 // mark it alive before it starts
    xTaskCreatePinnedToCore(scanTask, "wifiScan", 4096, nullptr, 1, nullptr, 0);  // 4 KB stack, priority 1, core 0
    s_wifiName = "SCAN";                                // remember the mode
  } else {                                              // "OFF" (or anything unknown)
    WiFi.softAPdisconnect(true);                        // stop the access point if there is one
    WiFi.mode(WIFI_OFF);                                // switch the radio off completely
    s_wifiName = "OFF";                                 // remember the mode
  }
}

/*
 * -----------------------------------------------------------------------------
 *  aggressorSetLoad()  —  start or stop the CPU-load task
 * -----------------------------------------------------------------------------
 */
void aggressorSetLoad(const char *mode) {
  if (strcmp(mode, "BUSY") == 0) {                      // busy CPU requested
    if (!s_loadAlive) {                                 // only start one task
      s_loadRun = true;                                 // the task should keep running
      s_loadAlive = true;                               // mark it alive before it starts
      xTaskCreatePinnedToCore(loadTask, "cpuLoad", 2048, nullptr, 0, nullptr, 0);  // 2 KB stack, priority 0, core 0
    }
    s_loadName = "BUSY";                                // remember the mode
  } else {                                              // "IDLE" (or anything unknown)
    s_loadRun = false;                                  // ask the task to stop
    waitWhileTrue(s_loadAlive, 1000);                   // it stops within microseconds; 1 s is plenty
    s_loadName = "IDLE";                                // remember the mode
  }
}

/*
 * -----------------------------------------------------------------------------
 *  aggressorWifiName() / aggressorLoadName()  —  report current modes
 * -----------------------------------------------------------------------------
 */
const char *aggressorWifiName() { return s_wifiName; }   // e.g. "SCAN"
const char *aggressorLoadName() { return s_loadName; }   // e.g. "BUSY"
