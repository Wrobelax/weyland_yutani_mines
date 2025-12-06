"""
Script used for calculating stats and detecting anomalies from data.
"""

import pandas as pd
import numpy as np
from scipy import stats as sp_stats

#---------------------
# Calculate statistics
#---------------------
def calculate_stats(df):
    """
    Calculating statistics used on dashboard. Total counted separately
    """
    mine_cols = [
        col for col in df.columns
        if col not in ["Date"] and pd.api.types.is_numeric_dtype(df[col])
    ]

    stats = pd.DataFrame(index=mine_cols)
    stats["mean"] = df[mine_cols].mean()
    stats["std"] = df[mine_cols].std()
    stats["median"] = df[mine_cols].median()
    stats["IQR"] = df[mine_cols].quantile(0.75) - df[mine_cols].quantile(0.25)

    return stats


#-----------------
# Detect Anomalies
#-----------------
def detect_anomalies(df,
                     methods=["IQR", "z-score", "moving_avg", "grubbs"],
                     z_thresh=2.0,
                     ma_window=7,
                     iqr_factor=1.5,
                     ma_pct=0.2
                     ):
    """
    Function for detecting anomalies in dataframe.
    - methods: list od methods for detection
    - z_thresh: threshold for z-score
    - ma_window: window size for moving average
    - iqr_factor: factor for iqr
    """
    mine_cols = [
        col for col in df.columns
        if col not in ["Date"]
        and pd.api.types.is_numeric_dtype(df[col])
    ]

    anomalies = pd.DataFrame(False, index=df.index, columns=mine_cols)

    # --- IQR ---
    if "IQR" in methods:
        Q1 = df[mine_cols].quantile(0.25)
        Q3 = df[mine_cols].quantile(0.75)
        IQR = Q3 - Q1
        anomalies |= (df[mine_cols] < (Q1 - iqr_factor * IQR)) | (df[mine_cols] > (Q3 + iqr_factor * IQR))

    # --- Z-score ---
    if "z-score" in methods:
        zscores = (df[mine_cols] - df[mine_cols].mean()) / df[mine_cols].std(ddof=0)
        anomalies |= zscores.abs() > z_thresh

    # --- Moving average ---
    if "moving_avg" in methods:
        for col in mine_cols:
            ma = df[col].rolling(window=ma_window, center=True).mean()
            diff = (df[col] - ma).abs()

            distance = pd.Series(0.0, index=df.index)
            nonzero = ma.abs() > 1e-12
            distance[nonzero] = diff[nonzero] / ma[nonzero]
            anomalies[col] |= distance > ma_pct

    # --- Grubbs ---
    if "grubbs" in methods:
        for col in mine_cols:
            series = df[col].dropna().values
            N = len(series)
            if N < 3:
                continue

            mean_val = np.mean(series)
            std_val = np.std(series, ddof=1)
            if std_val == 0:
                continue

            t = sp_stats.t.ppf(1 - 0.05 / (2 * N), N - 2)
            Gcrit = ((N - 1) / np.sqrt(N)) * np.sqrt(t ** 2 / (N - 2 + t ** 2))

            for i in range(len(df)):
                val = df.at[i, col]
                if pd.isna(val):
                    continue
                G = abs(val - mean_val) / std_val
                if G > Gcrit:
                    anomalies.at[i, col] = True

    return anomalies