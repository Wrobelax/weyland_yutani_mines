# Weyland-Yutani Mines

___

## **Project description**
This project consists of generating, analyzing, visualizing, and reporting synthetic mining-output data for an arbitrary number of mines.
The project consists of two main components:

Google Sheets Data Generator (Google Apps Script)
Generates realistic synthetic daily production data with multiple adjustable parameters.

Streamlit Dashboard (Python)
Loads data from the Google Sheet, performs statistical analysis, detects anomalies, visualizes trends, and exports detailed PDF reports.
___

## *Project Structure*
```
weyland_yutani_mines/
|
├── analysis/
|   ├── stats.py                 # Script used for analysis of statistics
|   └── init.py
├── charts/
|   ├── plotting.py              # Script used for creating charts on the tashboard
|   └── init.py
├── data/
|   ├── loader.py                # Script used for loading data from Google spreadsheet
|   └── init.py 
├── pdf/
|   ├── report.py                # Script used for generating PDF report
|   └── init.py 
├── requirements.txt
├── .gitignore                   # /secrets(API key for Google spreadsheet); pdf_reports(generated)
├── README.txt
└── app.py                       # Main file used for orchestration of the app.
```
___

## *Features*
1. Data Generator (Google Sheets + Apps Script)

* Unlimited number of mines (dynamic column detection)
* Per-mine baselines
* Two required distributions:
  * Normal
  * Uniform
* Automatic parameter label updates depending on distribution type (Normal Mean/SD vs. Uniform Min/Max)
* Correlation smoothing
* Day-of-week multipliers (e.g., Sunday −40%)
* Growth trend (% per day)
* Gaussian anomaly events:
  * date
  * duration
  * magnitude
  * probability
  * affected mines count
* Automatic creation of a chart in the “Generated Data” sheet


2. Streamlit Dashboard

* Loads and caches data from Google Sheets
* Supports dynamic mine names 
* Date range filtering
* Multiple anomaly detection methods:
  * IQR rule
  * Z-score
  * Moving average distance (percent)
  * Grubbs’ test
* For each mine + total:
  * mean
  * standard deviation
  * median
  * interquartile range
* Visualizations:
  * line charts
  * bar charts
  * stacked area charts
  * selectable polynomial trendlines (degree 1–4)
  * anomaly markers on the plot
* PDF Report:
  * statistics
  * anomaly list
  * complete plot
  * event descriptions
  * Gaussian curve explanation
___

## *Installation*

### 1.Clone the repository:
```bash
git clone https://github.com/Wrobelax/weyland_yutani_mines.git
cd weyland_yutani_mines
```

### 2.Install requirements:
```bash
pip install -r requirements.txt
```

### 3. Add Google API Credentials:
Place your service account key at:
```bash
secrets/service_account.json
```

### 4. Run the dashboard:
```bash
streamlit run dashboard.py

```
