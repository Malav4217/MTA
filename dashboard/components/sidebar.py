import streamlit as st
from datetime import datetime
import pandas as pd
import sys, os
from loguru import logger
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

def apply_global_styles():
    """Apply all custom CSS for the dashboard."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Bricolage+Grotesque:wght@400;600;700&display=swap');

    * { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    h1, h2, h3 { font-family: 'Bricolage Grotesque', sans-serif !important; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    [data-testid="stSidebarNav"] { display: none !important; }

    .block-container {
        padding-top: 2rem !important;
        max-width: 1200px !important;
    }

    .stApp { background: #F5F4F0 !important; }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        width: 260px !important;
    }

    section[data-testid="stSidebar"] > div {
        background-color: #FFFFFF !important;
    }

    .stApp p, .stApp span, .stApp div,
    .stApp label { color: #1A1A2E !important; }

    [data-testid="stMetricValue"] {
        color: #1A1A2E !important;
    }
    [data-testid="stMetricLabel"] {
        color: #6B6B8A !important;
    }

    section[data-testid="stSidebar"] .stRadio label {
        padding: 10px 16px !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #1A1A2E !important;
    }

    section[data-testid="stSidebar"] .stRadio label:hover {
        background: #F5F4F0 !important;
    }

    section[data-testid="stSidebar"] .stRadio label > div:first-child {
        display: none !important;
    }

    /* Nav items - unselected */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 10px 16px !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #6B6B8A !important;
        cursor: pointer !important;
        transition: all 0.15s !important;
        margin-bottom: 2px !important;
        display: flex !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #F5F4F0 !important;
        color: #1A1A2E !important;
    }

    /* Active item — targets label containing a checked input */
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: #EEF2FF !important;
        color: #2563EB !important;
        font-weight: 600 !important;
    }

    /* Override global label color for active nav item text */
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) span,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) div {
        color: #2563EB !important;
        font-weight: 600 !important;
    }

    /* Hide the radio circle dot */
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    /* Hide collapse button and its icon text */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    button[kind="header"] {
        display: none !important;
    }

    button[data-testid="baseButton-header"] {
        display: none !important;
    }

    .st-emotion-cache-1dp5vir {
        display: none !important;
    }

    /* Hide the keyboard_double_ icon text */
    section[data-testid="stSidebar"] button {
        display: none !important;
    }

    /* Hide any svg icon buttons in sidebar top */
    [data-testid="stSidebar"] > div > div > button {
        display: none !important;
    }

    /* Make sidebar always visible */
    section[data-testid="stSidebar"] {
        transform: none !important;
        min-width: 260px !important;
        width: 260px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar. Returns selected page name."""

    # Logo section
    st.sidebar.markdown("""
    <div style="padding:8px 16px 24px;
                border-bottom:1px solid #E8E6E0;
                margin-bottom:16px;">
      <div style="font-family:Bricolage Grotesque;
                  font-size:22px; font-weight:700;
                  color:#1A1A2E;">NYC Bus</div>
      <div style="display:flex; align-items:center;
                  gap:6px; margin-top:4px;">
        <span style="width:8px; height:8px;
                     border-radius:50%;
                     background:#EF4444;
                     display:inline-block;
                     animation:pulse 2s infinite;">
        </span>
        <span style="font-size:12px; color:#6B6B8A;">
          Live tracking
        </span>
      </div>
      <style>
        @keyframes pulse {
          0%,100%{opacity:1;transform:scale(1);}
          50%{opacity:0.5;transform:scale(0.85);}
        }
      </style>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    page = st.sidebar.radio("", [
        "Overview",
        "Ghost Bus Tracker",
        "Bus Bunching",
        "Route Analysis",
        "Live Map"
    ])

    # Pipeline status
    _render_pipeline_status()

    return page

def _render_pipeline_status():
    """Render pipeline status at bottom of sidebar."""
    from datetime import datetime
    import duckdb
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )))
    from config import DB_FILE

    # Read pipeline status from WRITER DB directly —
    # just a quick timestamp read, minimal conflict risk
    con = None
    result = None
    try:
        con = duckdb.connect(DB_FILE, read_only=True)
        result = con.execute("""
            SELECT
                MAX(captured_at) as latest,
                COUNT(*) as total_snapshots
            FROM raw_bus_snapshots
        """).df()
    except Exception as e:
        logger.warning(f"Pipeline status query failed: {e}")
    finally:
        if con:
            try:
                con.close()
            except:
                pass

    if result is None or result.empty:
        st.sidebar.markdown("""
        <div style="padding:0 8px; margin-top:24px;">
          <div style="background:#F5F4F0;
                      border-radius:12px; padding:14px;">
            <div style="font-size:11px; font-weight:600;
                        color:#6B6B8A; text-transform:uppercase;
                        letter-spacing:0.5px;">
              Pipeline Status
            </div>
            <div style="font-size:13px; color:#DC2626;
                        margin-top:8px;">
              No data found
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Safely extract values
    try:
        latest = result.iloc[0, 0]
        total  = int(result.iloc[0, 1])
    except Exception:
        return

    # Convert timestamp safely
    time_str     = "Unknown"
    status_color = "#DC2626"
    status_text  = "Stopped"

    try:
        if latest is not None and str(latest) != 'NaT':
            if hasattr(latest, 'to_pydatetime'):
                latest = latest.to_pydatetime()
            if hasattr(latest, 'tzinfo') and latest.tzinfo:
                latest = latest.replace(tzinfo=None)

            seconds_ago = int(
                (datetime.now() - latest).total_seconds()
            )

            if seconds_ago < 60:
                time_str = f"{seconds_ago}s ago"
            elif seconds_ago < 3600:
                time_str = f"{seconds_ago // 60}m ago"
            else:
                time_str = f"{seconds_ago // 3600}h ago"

            if seconds_ago < 90:
                status_color = "#16A34A"
                status_text  = "Running"
            elif seconds_ago < 300:
                status_color = "#D97706"
                status_text  = "Slow"
            else:
                status_color = "#DC2626"
                status_text  = "Stopped"
    except Exception:
        time_str = "Error"

    st.sidebar.markdown(f"""
    <div style="padding:0 8px; margin-top:24px;">
      <div style="background:#F5F4F0; border-radius:12px;
                  padding:14px;">
        <div style="font-size:11px; font-weight:600;
                    color:#6B6B8A; text-transform:uppercase;
                    letter-spacing:0.5px; margin-bottom:10px;">
          Pipeline Status
        </div>
        <div style="display:flex;
                    justify-content:space-between;
                    font-size:13px; margin-bottom:6px;">
          <span style="color:#6B6B8A;">Status</span>
          <span style="color:{status_color};
                       font-weight:600;">
            {status_text}
          </span>
        </div>
        <div style="display:flex;
                    justify-content:space-between;
                    font-size:13px; margin-bottom:6px;">
          <span style="color:#6B6B8A;">Last fetch</span>
          <span style="font-weight:500; color:#1A1A2E;">
            {time_str}
          </span>
        </div>
        <div style="display:flex;
                    justify-content:space-between;
                    font-size:13px;">
          <span style="color:#6B6B8A;">Snapshots</span>
          <span style="font-weight:500; color:#1A1A2E;">
            {total:,}
          </span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
