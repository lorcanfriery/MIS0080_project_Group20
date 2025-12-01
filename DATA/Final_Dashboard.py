import streamlit as st
import numpy as np
import os
import pandas as pd
import builtins
from streamlit_autorefresh import st_autorefresh
import traceback
import runpy
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt


# ─────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "DATA"

# ─────────────────────────────────────────
# PAGE CONFIG  (real call ONCE, first Streamlit command)
# ─────────────────────────────────────────
_real_set_page_config = st.set_page_config
_real_set_page_config(page_title="Macroeconomics Dashboard", layout="wide")

# After we've set it once, make further calls a no-op so that
# other modules (e.g. Morgan_Dashboard, fx_graph, etc.) calling
# st.set_page_config do NOT crash the app.
def _noop_set_page_config(*args, **kwargs):
    pass

st.set_page_config = _noop_set_page_config

# Make st_autorefresh available globally so Morgan_Dashboard
# can use it even if it doesn't import it explicitly.
builtins.st_autorefresh = st_autorefresh

# ─────────────────────────────────────────
# PATCH pandas.read_csv FOR macro_data.csv
# (Morgan_Dashboard uses a hard-coded Windows path)
# ─────────────────────────────────────────
_original_read_csv = pd.read_csv

def _patched_read_csv(filepath_or_buffer, *args, **kwargs):
    if isinstance(filepath_or_buffer, str) and "macro_data.csv" in filepath_or_buffer:
        # Redirect to the local copy inside this project
        local_path = DATA_DIR / "macro_data.csv"
        return _original_read_csv(local_path, *args, **kwargs)
    return _original_read_csv(filepath_or_buffer, *args, **kwargs)

pd.read_csv = _patched_read_csv

# ─────────────────────────────────────────
# HELPER: run a dashboard script from DATA/ as __main__
# and temporarily switch CWD to DATA so relative CSV paths work
# ─────────────────────────────────────────
def run_dashboard(script_stem: str):
    """
    Run a dashboard Python file located in DATA/ (e.g. 'Oscar_Dashboard')
    as if it were the main script.

    We temporarily switch the working directory to DATA so that
    pd.read_csv("final_data.csv"), gdp_data.csv, etc. resolve correctly.

    If anything fails, show the traceback in the tab.
    """
    cwd = os.getcwd()
    try:
        os.chdir(DATA_DIR)
        script_path = DATA_DIR / f"{script_stem}.py"
        runpy.run_path(str(script_path), run_name="__main__")
    except Exception:
        st.error(f"Error while running {script_stem}.py. Full traceback:")
        tb = traceback.format_exc()
        st.code(tb, language="python")
    finally:
        os.chdir(cwd)

# ─────────────────────────────────────────
# MAIN APP LAYOUT
# ─────────────────────────────────────────
st.title("Macroeconomics Dashboard.")
st.write("An analysis of global economic indicators, currency trends, and inflation data.")

tab1, tab2, tab3, tab4 = st.tabs([
    "Effects on Macro Indicators",
    "USD FX Rates",
    "USD Inflation",
    "Correlation Heat Map",
])

# Tab 1 – Oscar macro dashboard
with tab1:
    run_dashboard("Oscar_Dashboard")

# Tab 2 – FX dashboard
with tab2:
    run_dashboard("fx_graph")

# Tab 3 – Morgan's FRED dashboard
with tab3:
    run_dashboard("Morgan_Dashboard")

# Tab 4 – Heat map
with tab4:
    run_dashboard("heat_map")

