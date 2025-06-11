# AutoSense — Smart Asset Monitoring & Maintenance

AutoSense is an integrated platform designed for real-time monitoring and predictive maintenance of physical assets using IoT sensors, data analytics, and visualization tools. The system aims to increase operational efficiency, reduce downtime, and enable data-driven decision-making for asset management.

## Features

- **IoT Sensor Integration:** Collects real-time data from various sensors attached to assets (see `Real Sensors.txt`).
- **Data Visualization:** Interactive dashboards and charts for monitoring asset health, trends, and anomalies. Custom React components are available in [`Custom Components/`](Custom%20Components/).
- **Predictive Maintenance:** Uses machine learning models (see `FYP ML Training and Pipeline Code/`) to predict failures and recommend maintenance actions.
- **Threshold Alerts:** Configurable thresholds (see `Thresholds.txt`) trigger alerts for abnormal readings.
- **Asset Tracking:** Map-based visualization for asset locations and status.
- **Simulator:** Simulates sensor data for testing and development (see `Simulator/`).

## Project Structure

- [`Custom Components/`](Custom%20Components/): React components for data visualization (e.g., `Barchart.js`, `Doughnut Chart.js`, `ColorfulMarkersMap.js`).
- [`Dataset/`](Dataset/): Datasets used for analytics and model training.
- [`FYP ML Training and Pipeline Code/`](FYP%20ML%20Training%20and%20Pipeline%20Code/): Machine learning scripts and pipelines.
- [`IoT/`](IoT/): IoT integration scripts and sensor data handlers.
- [`Models and scripts/`](Models%20and%20scripts/): Additional models and utility scripts.
- [`Simulator/`](Simulator/): Tools for simulating sensor data.
- [`Salesforce/`](Salesforce/): Salesforce integration for asset management.
- [`Graphics/`](Graphics/) & [`Icons/`](Icons/): Visual assets for the UI.
- `Real Sensors.txt`, `Thresholds.txt`, `Tyres.txt`: Configuration and reference files.

## Getting Started

1. **Clone the repository:**
   ```sh
   git clone https://github.com/HuzaifaNaseer02/AutoSense---Smart-Asset-Monitoring-Maintenance.git
   ```
