# V1.4 DevKit USB power, GPIO and Wi-Fi evidence

28 October 2026. Independent document review; no schematic edits, hardware measurements or wearable release. Read the original F01–F21 review §§4.3–4.5/7.4–7.5 and V1.3 `power_architecture.md`, `diagnostics/power_architecture/esp-usb-evidence.md` and `diagnostics/power_simplification/esp.md` before evaluating this change. The V1.4 USB-only instruction supersedes V1.3's battery-only source contract; it does not retroactively validate USB wearability.

## Actual assembly boundary

The current V1.4 cached symbol and the native [initial-netlist.xml](initial-netlist.xml) identify U3 as `ESP32-S3-DevKitC`, footprint `PCM_Espressif:ESP32-S3-DevKitC`, with no board revision or module suffix. U3.1/.2 are the two 3V3 headers; U3.21 is the 5V header; U3.22/.23/.24/.44 are ground. This is a whole development-board symbol, so the carrier does not depict its regulator, USB diodes, bridge or LEDs. Final native-netlist verification must establish the implemented carrier rail membership.

The [official DevKitC-1 v1.1 schematic, sheet 2](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf) specifies **SGM2212-3.3XKC3G/TR** as onboard U2, with a CP2102N bridge and LEDs. This supports that exact reference assembly, not every compatible board or clone. The [official guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html#power-supply-options) supports USB power and makes USB, 5V-header and 3V3-header supply methods mutually exclusive. For V1.4 use one USB source, leave the carrier 5V header unpowered, and do not inject an external carrier 3V3 source.

## F13/F16/F17: power budget and its limits

The [WROOM-1/-1U v1.8 datasheet, Tables 6-2/6-4](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) specifies 3.0–3.6 V and a source capable of at least 0.5 A. Characterized 3.3 V, 25°C Wi-Fi TX peaks are 355 mA (1 Mbps/20.5 dBm), 297 mA (54 Mbps/18 dBm) and 285–286 mA for the listed 802.11n modes; RX is 95–97 mA. These conditions do not bound every application, memory variant, temperature or complete DevKit load. Do not add mutually exclusive TX/RX modes together.

[ADS1298 Rev. K, electrical characteristics p.16](https://www.ti.com/lit/ds/symlink/ads1298.pdf) gives typical HR analog current 2.75 mA at 3 V and typical digital current 0.5 mA at DVDD=3 V, with RLD/WCT/PACE off: approximately **6.5 mA for two devices** under those conditions. This is a screening estimate, not a guaranteed 3.3 V/2 kSPS upper bound. Use a **20 mA pair allowance** provisionally, including clock/interface/auxiliary uncertainty, and replace it with measurements.

The [CP2102N datasheet Table 3.2](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf) gives typical 9.5 mA at 115200 baud and 13.7 mA at 3 Mbaud, plus USB pull-up current. Its supply routing must follow the actual board. Disable RGB during acquisition. A provisional **25 mA additional board allowance** is a design assumption, not a measured maximum.

| Screen | Arithmetic | Meaning |
|---|---:|---|
| Characterized high TX plus allowances | 355 + 20 + 25 = **400 mA** | Plausible operating screen; not a worst-case guarantee |
| Module source-capability allocation plus allowances | 500 + 20 + 25 = **545 mA** | A 500 mA USB budget cannot preserve this entire allocation |
| Illustrative onboard LDO loss at 400 mA | (5 − 3.3) × 0.4 = **0.68 W** | Conservative full-load-through-LDO screen before USB-diode drop |

The [SGM2212 Rev. A.2 datasheet](https://www.sg-micro.com/rect/assets/54089b71-cc25-4f36-af2e-34b07f00a108/SGM2212.pdf) rates the regulator at 800 mA; that rating does not guarantee an 800 mA DevKit output. Its reference SOT-223 thermal resistance is 117°C/W: the 0.68 W screen corresponds to approximately 80°C rise on that fixture. Actual copper, enclosure, ambient, RF duty and which loads bypass the LDO determine the real temperature. Recommended effective output capacitance is 1–10 µF; the carrier bank adds to the DevKit's existing capacitance, so the delivered parallel network exceeds that recommendation by nominal arithmetic. This requires startup/stability/transient qualification; no oscillation has been demonstrated. Check fitted regulator identity before relying on these specifications.

[USB-IF peripheral-power policy](https://compliance.usb.org/index.asp?Format=Standard&UpdateFile=Policies) limits a USB 2.0 peripheral on a standard USB 2.0 downstream port to 500 mA; attaching it to USB 3 does not itself grant 900 mA. A connector alone does not establish authorization, pre-configuration/suspend compliance or available current. The bridge/native-USB descriptors and host policy have not been checked. A known 5 V USB source with at least **1 A available** gives supply margin for bench tests, but cannot remove the onboard LDO thermal limit or establish host-port compliance. Use one source/cable, then measure USB input current, 5V/LDO input, 3V3 at U3 and both ADCs, boot/hot-plug and sustained Wi-Fi TX temperature. F16 remains conditional; removing carrier regulators addresses the former competing-source mechanism of F17 only when the one-source contract is enforced.

## F09: direct-interface GPIO choices

The [ESP32-S3 SoC v2.2 datasheet, Tables 2-1/2-2 and §§2.3.1/2.3.4](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) documents low-output power-up glitches on GPIO6–14. GPIO21 and GPIO39–42 are absent from its glitch table; GPIO39–42 are JTAG pads and input-enabled at reset. Thus the following remap removes the documented startup contention path, conditional on GPIO ownership:

| Signal | MCU GPIO | U3 terminal |
|---|---:|---:|
| CS_ADC1, 10 kΩ to 3V3 | 21 | 27 |
| CS_ADC2, 10 kΩ to 3V3 | 39 | 36 |
| Shared SPI_MISO | 40 | 37 |
| DRDY_ADC1 | 41 | 38 |
| DRDY_ADC2 | 42 | 39 |

The [WROOM datasheet §4.4/Table 4-5](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) requires a defined GPIO3 strap. A 10 kΩ pull-up is suitable: default eFuses select USB JTAG regardless of GPIO3, and strap-select mode selects USB when GPIO3 is HIGH. An eFuse configuration forcing pad JTAG overrides that strap. Read the installed eFuses and reserve pad JTAG; do not assume the resistor overrides every configuration or burn eFuses as a routine fix.

Keep RESET GPIO6 and PWDN GPIO7 pulled LOW; START GPIO8, MOSI GPIO11 and SCLK GPIO12 pulled LOW. Their documented LOW glitches reinforce those defaults. Firmware must set output latches before enabling outputs, retain exclusive CS, explicitly mux GPIO40–42 as input-only with pulls disabled, and reset/reconfigure both ADCs on every firmware entry and recovery. CPU-only restart can retain GPIO/peripheral state; a pull resistor does not override an actively driven pin. This is a minimum controlled-firmware interface, not hardware protection against arbitrary firmware faults. Validate cold start, reset button, flashing, watchdog, software restart and brownout using dummy inputs.

## F18: 2 kSPS traffic and scheduling

Each ADS1298 output frame is 24 status bits plus 8 × 24 channel bits = 27 bytes. A synchronized 16-channel sample pair is therefore **54 bytes**. At 2 kSPS, acquisition produces **108,000 bytes/s = 864 kbit/s** including both status words; channel samples alone are 96,000 bytes/s. These calculations preserve the original review §7.5. At 4 MHz, two full frames need 108 µs of shift time within each 500 µs sample period, before CS hold times, update keepout and scheduling. Use a measured SPI/interrupt budget; nominal average bit rate is not a sufficient clock choice.

Example packetization calculation, not implemented firmware: 20 sample pairs per packet gives 1080 data bytes every 10 ms; adding a proposed 16-byte sequence/timestamp/header makes 1096 application bytes and **100 packets/s**. With ordinary 20-byte IPv4 plus 8-byte UDP headers this is 112,400 bytes/s, approximately **0.899 Mbit/s**, before link-layer headers, acknowledgments, retries or security. Check the actual network MTU. A 100 ms network interruption requires at least 10.8 kB of frame storage before queue/metadata overhead; no finite buffer guarantees survival of arbitrary disconnects.

[Espressif's ESP32-S3 Wi-Fi performance guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/wifi-driver/wifi-performance-and-power-save.html#esp32-s3-wi-fi-throughput) reports favorable lab iperf results around 20 Mbit/s TCP TX and 30 Mbit/s UDP TX, with higher shield-box results. This supports **2 kSPS as a reasonable engineering target**, not guaranteed end-to-end performance. Actual AP, interference, antenna placement, CPU/heap configuration, retransmissions and application processing control sustained service. Acquire into a bounded ring buffer independently of network sends; timestamp and sequence frames, count overrun/drop events, and test simultaneous acquisition plus streaming. TCP backpressure can stall transmission; UDP requires loss detection. Bench acceptance needs both DRDY alignment and a long continuous receiver-side sequence audit, including network interruption/reconnect.

USB power/ground remains electrically connected to the electrode circuitry. These checks do not establish normal/single-fault wearer safety, F07/F08 resolution, analog noise performance, or readiness for human-worn tests.
