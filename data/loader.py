"""
Script used for loading data and events from Google sheet.
"""

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

#-----------------------------
# Load data from Google Sheets
#-----------------------------
@st.cache_data
def load_data(sheet_name="Generated Data", json_key="secrets/service_account.json"):
    """
    Function used to load data from Google sheet.
    """
    # Google Sheets API scope
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    # Authenticate
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_key, scope)
    client = gspread.authorize(credentials)

    # Opening sheet and converting to DF
    sheet = client.open("Weyland-Yutani Data Generator").worksheet(sheet_name)
    data = pd.DataFrame(sheet.get_all_records())

    # Ensuring date column is datetime
    data["Date"] = pd.to_datetime(data["Date"])

    return data

# Loading data
data = load_data()
st.subheader("Preview of Generated Data")
st.dataframe(data.head())


#------------
# Load events
#------------
def load_events(json_key="secrets/service_account.json"):
    """
    Load events from Google spreadsheet. Used to generate data into PDF.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_key, scope)
    client = gspread.authorize(credentials)

    sheet = client.open("Weyland-Yutani Data Generator").sheet1

    # Read rows B10:E
    raw = sheet.get("B10:E50")

    events = []
    for row in raw:
        if not any(row):
            continue

        day, duration, factor, prob = row

        # convert types
        try:
            event_date = pd.to_datetime(day).normalize()
        except:
            continue

        events.append({
            "date": event_date,
            "duration": int(duration),
            "factor": float(factor),
            "prob": float(prob)
        })

    return events
