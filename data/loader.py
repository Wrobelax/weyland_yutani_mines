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
def get_gspread_client():
    """
    Builds a gspread client using Streamlit secrets.
    """
    try:
        sa_info = st.secrets["gcp_service_account"]
    except KeyError:
        st.error("Missing [gcp_service_account] section in Streamlit secrets.")
        st.stop()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(sa_info, scopes=scopes)
    client = gspread.authorize(credentials)
    return client


@st.cache_data
def load_data(sheet_name="Generated Data", json_key="secrets/service_account.json"):
    """
    Function used to load data from Google sheet.
    """
    client = get_gspread_client()
    sheet = client.open("Weyland-Yutani Data Generator").worksheet(sheet_name)

    df = pd.DataFrame(sheet.get_all_records())
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    return df


#------------
# Load events
#------------
def load_events(json_key="secrets/service_account.json"):
    """
    Load events from Google spreadsheet. Used to generate data into PDF.
    """
    client = get_gspread_client()
    sheet = client.open("Weyland-Yutani Data Generator").sheet1

    # Read rows B10:E (date, duration, factor, probability)
    raw = sheet.get("B10:E50")

    events = []
    for row in raw:
        if not any(row):
            continue

        try:
            day, duration, factor, prob = row
        except ValueError:
            continue

        try:
            event_date = pd.to_datetime(day).normalize()
        except Exception:
            continue

        events.append(
            {
                "date": event_date,
                "duration": int(duration),
                "factor": float(factor),
                "prob": float(prob),
            }
        )

    return events
