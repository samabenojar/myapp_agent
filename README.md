
# 📁 README — Battery Telemetry Dataset Exploration & Build

## 📌 Purpose

This repository is a structured foundation for collecting, processing, and analyzing **battery telemetry and performance datasets**, with the goal of developing:

* reproducible ingestion pipelines
* standardized charge/discharge structures
* sag & recovery metrics
* health scoring models
* diagnostics pipelines
* visuals and dashboards

Datasets include time-series measurements of **voltage, current, temperature, and charge/discharge cycles** from lithium-ion battery testing sources.

---

## 📊 Recommended Public Datasets

These datasets provide realistic battery performance data you can use to experiment with telemetry ingestion, feature engineering, scoring, and analytics.

### 🔹 NASA Battery Aging Datasets

A set of discharge/charge/impedance tests on commercial 18650 cells under controlled conditions (voltage, current, temperature). Useful for modeling degradation over repeated cycles. ([NASA Open Data Portal][1])

📥 Example use cases:

* SOC/SoH prediction
* voltage vs time analysis
* cycle life modeling

**Link:** Search “NASA battery dataset” on Kaggle or NASA Open Data. ([Kaggle][2])

---

### 🔹 Lithium-Ion Battery Degradation (Kaggle)

Tabulated charge/discharge cycle data with averaged values like current, voltage, temperature, capacity, and state metrics. ([Kaggle][3])

📥 Example use cases:

* condition estimation per cycle
* feature extraction for degradation curves

**Link:** Kaggle dataset “Lithium-Ion Battery Degradation Dataset”.

---

### 🔹 CALCE Battery Data Repository

Experimental test data for lithium-ion batteries including full and partial cycle profiles. Useful for:

* SoC estimation
* RUL prediction
* reliability analysis ([calce.umd.edu][4])

**Link:** CALCE battery data (University of Maryland) portal.

---

### 🔹 Open Source Battery Data Lists

A community-curated list of open battery performance datasets, including multiple cycling tests. ([GitHub][5])

📥 Example use cases:

* benchmarking models
* comparing chemistries or protocols
* identifying new dataset sources

**Link:** Open Source Battery Data GitHub curate.

---

## 🧠 Key Concepts

Battery analysis typically involves the following core variables:

| Field         | Description                      |
| ------------- | -------------------------------- |
| `time`        | Timestamp of measurement         |
| `voltage`     | Terminal voltage of cell/battery |
| `current`     | Charge/discharge current         |
| `temperature` | Cell or ambient temp             |
| `soc`         | State of Charge                  |
| `soh`         | State of Health                  |
| `cycle`       | Charge/discharge cycle index     |

These allow modeling:

* sag events
* recovery curves
* internal resistance proxies
* state indicators

Understanding SoH (State of Health) — a metric of battery condition relative to ideal — is central. It’s defined as a percentage (100% = new, lower = degraded). ([Wikipedia][6])

---

## 🛠 Repository Structure

```
battery-telemetry-datasets/
├── data/                        # downloaded datasets (raw)
├── canonical/                  # cleaned canonical tables
│   ├── runs.csv
│   ├── samples.csv
│   └── metadata.csv
├── src/
│   ├── ingest/                 # ingestion scripts
│   ├── transform/              # normalization & feature extraction
│   ├── derive/                 # sag/recovery metrics
│   ├── visualization/          # plotting dashboards
│   └── db/                     # schema + load scripts
├── notebooks/                  # exploratory analysis
├── README.md
└── requirements.txt
```

---

## 🚀 Workflow Overview

### 📥 1. Ingestion

* Download and store raw dataset files locally (CSV/JSON/MAT)
* Validate against contracts (schema + type checks)

### 🔄 2. Normalization

* Convert to canonical schema: time, voltage, current, temp, run_id etc.
* Use Pydantic (Python) for executable contracts

### 🧮 3. Feature Engineering

Compute derived metrics such as:

* sag = voltage drop under load
* recovery curves
* T50/T90 recovery times
* internal resistance proxy
* SoC estimates

---

## 📊 Example Derived Metrics

| Metric         | Meaning                                   |
| -------------- | ----------------------------------------- |
| `vbat_sag`     | Drop in voltage under load                |
| `t50_recovery` | Time for voltage to recover 50% post-load |
| `t90_recovery` | Time to reach 90% of baseline             |
| `soh_est`      | Estimated health metric                   |

Use these to compare:

* new vs aged cells
* different protocols
* performance under varied conditions

---

## 📈 Visualization Examples

Provide plots like:

* Voltage vs time with load events highlighted
* Sag & recovery curves overlayed
* SoH vs cycle number
* Histogram of internal resistance proxies

---

## 📦 Getting Started

1. **Install dependencies**

```sh
pip install -r requirements.txt
```

2. **Download datasets**

Place them under `data/` and record source metadata.

3. **Run ingestion**

```sh
python src/ingest/load_nasa.py
```

4. **Build canonical tables**

```sh
python src/transform/normalize.py
```

5. **Compute derived metrics**

```sh
python src/derive/battery_metrics.py
```

6. **Visualize results**

```sh
python src/visualization/plot_sag_vs_time.py
```

---

## 🧪 How to Use This for Incubator

This dataset foundation will allow you to:

* test ingestion contracts
* validate normalization logic
* generate derived health metrics
* create dashboards or API endpoints
* calibrate scoring systems

It aligns with the telemetry platform you intend to build.

---

## 📚 Related Resources

* NASA Prognostics Center battery repository (builds discharge/charge data) ([NASA Open Data Portal][1])
* Kaggle lithium-ion battery degradation dataset with cycle data ([Kaggle][3])
* CALCE battery experimental test data (raw/partial cycling) ([calce.umd.edu][4])
* Open Source Battery Data curated list ([GitHub][5])

---

## 🧩 License

Datasets have their own licenses — ensure you check terms before reuse.

---

## 📫 Contribution

If you find new relevant datasets, add them under `data-sources.md` with:

* source name
* variables
* sampling rate
* license
* intended use case


[1]: https://data.nasa.gov/dataset/li-ion-battery-aging-datasets?utm_source=chatgpt.com "Li-ion Battery Aging Datasets"
[2]: https://www.kaggle.com/datasets/patrickfleith/nasa-battery-dataset?utm_source=chatgpt.com "NASA Battery Dataset"
[3]: https://www.kaggle.com/datasets/programmer3/lithium-ion-battery-degradation-dataset?utm_source=chatgpt.com "Lithium-Ion Battery Degradation Dataset"
[4]: https://calce.umd.edu/battery-data?utm_source=chatgpt.com "Battery Data | Center for Advanced Life Cycle Engineering"
[5]: https://github.com/lappemic/open-source-battery-data?utm_source=chatgpt.com "An awesome list about all available open source battery data."
[6]: https://en.wikipedia.org/wiki/State_of_health?utm_source=chatgpt.com "State of health"
