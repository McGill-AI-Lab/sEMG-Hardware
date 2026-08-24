# open-semg-16: Open-Source 16-Channel High Accuracy EMG

<p align="center">
  <img src="https://github.com/user-attachments/assets/6cdbc603-053d-4552-9c33-e2e7e87b085e" width="75%">
</p>

Recent advances in **surface electromyography (sEMG) decoding**, such as **[Meta’s EMG2Pose](https://arxiv.org/abs/2412.02725)**, **[EMG2QWERTY datasets](https://arxiv.org/abs/2410.20081)**, and their associated pretrained models, have demonstrated high-accuracy hand-pose and typing reconstruction. However, these breakthroughs rely on **Meta’s proprietary acquisition hardware (sEMG-RD)**, limiting reproducibility and broader utility for independent research and open development. This repo aims to make the hardware, data, model pipeline **transparent, modifiable, and benchmarkable**.

open-sEMG-16 will be a 16-channel, high-fidelity, wrist-wearable sEMG platform built from commercially available components, with design files + firmware to enable **end-to-end reproducibility**.


<p align="center">
  <img src="https://github.com/user-attachments/assets/de04b735-f96d-437d-bec9-f8423d788860" width="85%">
</p>

---

High-level modules (see top-level folders):

- `Hardware/` — **open-sEMG-16** hardware stack (schematics/PCB, electrode layout, enclosure notes, firmware hooks, bring-up docs).
- (*future*)_`acquisition/` — acquisition + preprocessing utilities (streaming, windowing, filtering, normalization, dataset I/O, evaluation harness).
- (*future*)`data/` — dataset organization, conversion scripts, and format docs (raw → aligned → windowed → model-ready).
- (*future*)`hand-joint-labeling/` — tooling for pose labeling / alignment (e.g., joint definitions, coordinate frames, annotation utilities).
- `Weareable sEMG Report.pdf` — a PDF report summarizing the design and development of the wearable sEMG platform, including a review of hardware design choices, justification of our component choices, and introduction to the data collection pipeline. 
- `Documents`/ — remaining design docs, physiology summaries, meeting notes, and other internal documentation.
> **Status:** still in active development; APIs and folder contents may shift. We aim to keep experiments **config-driven** and results **reproducible** as the codebase stabilizes.

---
Prototype picture is shown below, the final device will be a wireless wearable.
<img width="2160" height="2880" alt="karen-semg" src="https://github.com/user-attachments/assets/314c58b5-e3a1-42e9-87e9-9a9da2935625" />

Signal Visualization for 5-seconds closed 5-seconds open hand test. You can see the signals (voltages picked up from each channel) moving up and down accordingly:
<img width="1332" height="615" alt="WhatsApp Image 2026-08-24 at 21 48 25" src="https://github.com/user-attachments/assets/4d7f43fd-ffba-456b-90ef-e3a101d88d70" />


## Contributors

* Emir
* Karen 
* Oscar
* Jazia
* Clarissa
* Emiliano



---

## References

* **emg2pose: A Large and Diverse Benchmark for Surface Electromyographic Hand Pose Estimation** (2024)
  [https://arxiv.org/abs/2412.02725](https://arxiv.org/abs/2412.02725)

* **emg2qwerty: A Large Dataset with Baselines for Touch Typing using Surface Electromyography** (2024)
  [https://arxiv.org/abs/2410.20081](https://arxiv.org/abs/2410.20081)

* **A generic non-invasive neuromotor interface for human-computer interaction** (Nature, 2025)
  [https://www.nature.com/articles/s41586-025-09255-w](https://www.nature.com/articles/s41586-025-09255-w)

* **Meta blog: Advancing Neuromotor Interfaces by Open Sourcing sEMG Datasets** (2024)
  [https://ai.meta.com/blog/open-sourcing-surface-electromyography-datasets-neurips-2024/](https://ai.meta.com/blog/open-sourcing-surface-electromyography-datasets-neurips-2024/)


will include list of components and their associated datasheets
