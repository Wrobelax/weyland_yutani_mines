"""
Script used for loading data and events from Google sheet.
"""

import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from collections.abc import Mapping

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
        raise KeyError("gcp_service_account secret is missing.")

    # --- CASE 1: Streamlit AttrDict or any mapping → treat as dict ---
    if isinstance(sa_info_raw, Mapping):
        sa_info = dict(sa_info_raw)   # convert to plain dict

    # --- CASE 2: JSON string containing service account JSON ---
    elif isinstance(sa_info_raw, str):
        try:
            sa_info = json.loads(sa_info_raw)
        except Exception as e:
            raise ValueError(f"Service account string is not valid JSON: {e}")

    else:
        raise TypeError(
            f"Unsupported type for gcp_service_account: {type(sa_info_raw)}"
        )

    # --- Fix private_key newlines ---
    if "private_key" in sa_info and isinstance(sa_info["private_key"], str):
        sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")

    return sa_info


def get_gspread_client():
    """
    Builds a gspread client using Streamlit secrets.
    """
    if "gcp_service_account" not in st.secrets:
        st.error("Missing [gcp_service_account] in Streamlit secrets.")
        st.stop()

    try:
        sa_info = _normalize_sa_info(st.secrets["gcp_service_account"])
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
            "Failed to create Google credentials. Possible issues:\n"
            "- Wrong TOML formatting\n"
            "- Missing fields in service account\n"
            "- Incorrect private key formatting\n\n"
            f"Underlying error: {e}"
        )
        st.stop()


def load_data(sheet_name="Generated Data", json_key="secrets/service_account.json"):
    """
    Function used to load data from Google sheet.
    """
    client = get_gspread_client()
    try:
        sheet = client.open("Weyland-Yutani Data Generator").worksheet(sheet_name)
    except Exception as e:
        st.error(f"Cannot open worksheet '{sheet_name}': {e}")
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
        st.error(f"Cannot open sheet1: {e}")
        st.stop()

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

        try:
            events.append({
                "date": event_date,
                "duration": int(duration),
                "factor": float(factor),
                "prob": float(prob),
            })
        except Exception:
            continue

    return events
