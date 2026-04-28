import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))

from dashboard.components.sidebar import (
    apply_global_styles,
    render_sidebar
)
from dashboard.views import (
    overview,
    ghost_buses,
    bunching,
    route_analysis,
    live_map
)

def main():
    st.set_page_config(
        page_title="NYC Bus Reliability Tracker",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    apply_global_styles()
    page = render_sidebar()

    if page == "Overview":
        overview.render()
    elif page == "Ghost Bus Tracker":
        ghost_buses.render()
    elif page == "Bus Bunching":
        bunching.render()
    elif page == "Route Analysis":
        route_analysis.render()
    elif page == "Live Map":
        live_map.render()

if __name__ == "__main__":
    main()
