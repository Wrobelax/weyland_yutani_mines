"""
Script used for loading data and events from Google sheet.
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

#-----------------------------
# Load data from Google Sheets
#-----------------------------
def _normalize_sa_info(sa_info_raw):
    """
    Accept either:
      - a dict-like object already (preferred), or
      - a JSON string (common when users paste JSON into TOML),
    and return a dict suitable for from_service_account_info.
    Also fixes escaped newlines in private_key.
    """
    if sa_info_raw is None:
        raise KeyError("No service account info provided (st.secrets['gcp_service_account'] missing).")

    # If user provided a mapping already (Streamlit TOML nested table -> dict), use it
    if isinstance(sa_info_raw, dict):
        sa_info = dict(sa_info_raw)  # shallow copy
    elif isinstance(sa_info_raw, str):
        # try to parse JSON string
        try:
            sa_info = json.loads(sa_info_raw)
        except Exception as e:
            raise ValueError("Service account value in st.secrets is a string but not valid JSON: " + str(e))
    else:
        # attempt to coerce (rare)
        raise TypeError("Unsupported type for gcp_service_account in st.secrets: {}".format(type(sa_info_raw)))

    # Fix common problem: private_key stored with literal '\n' sequences
    if "private_key" in sa_info and isinstance(sa_info["private_key"], str):
        pk = sa_info["private_key"]
        if "\\n" in pk:
            sa_info["private_key"] = pk.replace("\\n", "\n")
    return sa_info
def get_gspread_client():
    """
    Builds a gspread client using Streamlit secrets.
    """
    try:
        sa_raw = st.secrets["gcp_service_account"]
    except Exception:
        st.error(
            "Missing Streamlit secret `gcp_service_account`. "
            "Add your service account JSON under that key (see README)."
        )
        st.stop()

    try:
        sa_info = _normalize_sa_info(sa_raw)
    except Exception as e:
        st.error(f"Failed to parse gcp_service_account secret: {e}")
        st.stop()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    try:
        credentials = Credentials.from_service_account_info(sa_info, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(
            "Failed to create Google credentials from service account info. "
            "Common issues:\n"
            " - private_key contains literal '\\\\n' instead of real newlines (this loader attempts to fix that),\n"
            " - secret JSON structure is invalid, or\n"
            " - missing required fields (client_email, private_key, etc.).\n\n"
            f"Underlying error: {e}"
        )
        st.stop()


@st.cache_data
def load_data(sheet_name="Generated Data", json_key="secrets/service_account.json"):
    """
    Function used to load data from Google sheet.
    """
    client = get_gspread_client()
    try:
        sheet = client.open("Weyland-Yutani Data Generator").worksheet(sheet_name)
    except Exception as e:
        st.error(f"Failed to open spreadsheet or worksheet '{sheet_name}': {e}")
        st.stop()

    df = pd.DataFrame(sheet.get_all_records())
    df["Date"] = pd.to_datetime(df.get("Date"), errors="coerce")
    return df


#------------
# Load events
#------------
def load_events(json_key="secrets/service_account.json"):
    """
    Load events from Google spreadsheet. Used to generate data into PDF.
    """
    client = get_gspread_client()
    try:
        sheet = client.open("Weyland-Yutani Data Generator").sheet1
    except Exception as e:
        st.error(f"Failed to open spreadsheet (sheet1): {e}")
        st.stop()

    raw = sheet.get("B10:E50")
    events = []
    for row in raw:
        if not any(row):
            continue
        try:
            day, duration, factor, prob = row
        except ValueError:
            # skip malformed row
            continue
        try:
            event_date = pd.to_datetime(day).normalize()
        except Exception:
            continue
        try:
            events.append(
                {
                    "date": event_date,
                    "duration": int(duration),
                    "factor": float(factor),
                    "prob": float(prob),
                }
            )
        except Exception:
            # skip rows with wrong types
            continue

    return events
