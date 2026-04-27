import streamlit as st
import requests
import os
from streamlit.components.v1 import html as st_html
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))
from database.connection import safe_query
from dashboard.components.cards import page_header

ROUTE_COLORS = {
    'M15': '#2563EB', 'BX12': '#16A34A',
    'B46': '#DC2626', 'Q58':  '#D97706',
}


def get_live_buses(routes):
    all_buses = []
    api_key = os.getenv('MTA_API_KEY')
    for route in routes:
        try:
            params = {
                'key': api_key,
                'LineRef': f'MTA NYCT_{route}',
                'VehicleMonitoringDetailLevel': 'calls'
            }
            r = requests.get(
                'http://bustime.mta.info/api/siri/vehicle-monitoring.json',
                params=params, timeout=10
            )
            vehicles = (r.json()['Siri']['ServiceDelivery']
                       ['VehicleMonitoringDelivery'][0]
                       .get('VehicleActivity', []))
            for v in vehicles:
                mvj = v['MonitoredVehicleJourney']
                mc  = mvj.get('MonitoredCall', {})
                all_buses.append({
                    'route':      route,
                    'vehicle_id': mvj.get('VehicleRef', ''),
                    'latitude':   float(mvj['VehicleLocation']['Latitude']),
                    'longitude':  float(mvj['VehicleLocation']['Longitude']),
                    'stop_name':  mc.get('StopPointName', 'Unknown'),
                    'distance':   mc.get('Extensions', {})
                                    .get('Distances', {})
                                    .get('PresentableDistance', 'N/A'),
                    'aimed':      mc.get('AimedArrivalTime', 'N/A'),
                    'expected':   mc.get('ExpectedArrivalTime') or mc.get('AimedArrivalTime', 'N/A'),
                })
        except Exception as e:
            st.warning(f"Error fetching {route}: {e}")
    return all_buses


def render():
    st.markdown(f"""
    <div style="margin-bottom: 32px;">
      <div style="font-size: 13px; color: #6B6B8A; margin-bottom: 4px;">
        {datetime.now().strftime('%A, %B %d')} · Live
      </div>
      <h1 style="font-family: Bricolage Grotesque; font-size: 36px;
                  font-weight: 700; color: #1A1A2E; margin: 0;">
        Live Map
      </h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .stButton > button {
        border-radius: 20px !important;
        font-weight: 600 !important;
        border: 2px solid !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if 'selected_routes' not in st.session_state:
        st.session_state.selected_routes = ['M15', 'BX12', 'B46', 'Q58']

    all_routes   = ['M15', 'BX12', 'B46', 'Q58']
    route_colors = {'M15': '#2563EB', 'BX12': '#16A34A', 'B46': '#DC2626', 'Q58': '#D97706'}
    route_bgs    = {'M15': '#DBEAFE', 'BX12': '#DCFCE7', 'B46': '#FEE2E2', 'Q58': '#FEF3C7'}

    st.markdown(
        "<p style='font-size:13px; color:#6B6B8A; margin-bottom:8px;'>Filter by route</p>",
        unsafe_allow_html=True
    )

    try:
        selected_routes = st.pills(
            label="",
            options=all_routes,
            default=st.session_state.selected_routes,
            selection_mode="multi",
            key="route_pills",
            label_visibility="collapsed"
        )
        st.session_state.selected_routes = selected_routes
    except AttributeError:
        btn_cols = st.columns(4)
        for i, route in enumerate(all_routes):
            with btn_cols[i]:
                is_active   = route in st.session_state.selected_routes
                button_type = "primary" if is_active else "secondary"
                if st.button(route, key=f"toggle_{route}", type=button_type, use_container_width=True):
                    if route in st.session_state.selected_routes:
                        if len(st.session_state.selected_routes) > 1:
                            st.session_state.selected_routes.remove(route)
                    else:
                        st.session_state.selected_routes.append(route)
                    st.rerun()

    selected_routes = st.session_state.selected_routes

    if selected_routes:
        buses = get_live_buses(selected_routes)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        count_cols  = st.columns(4)
        route_counts = {}
        for bus in buses:
            route_counts[bus['route']] = route_counts.get(bus['route'], 0) + 1

        for i, route in enumerate(all_routes):
            color = route_colors[route]
            bg    = route_bgs[route]
            count = route_counts.get(route, 0)
            with count_cols[i]:
                st.markdown(f"""
                <div style="background:{bg}; border-radius:12px; padding:16px;
                            text-align:center; margin-bottom:12px;">
                  <div style="width:8px; height:8px; border-radius:50%;
                              background:{color}; margin:0 auto 8px;"></div>
                  <div style="font-size:24px; font-weight:700; color:{color};">
                    {count}
                  </div>
                  <div style="font-size:12px; font-weight:600; color:{color};
                              margin-top:2px;">
                    {route}
                  </div>
                </div>
                """, unsafe_allow_html=True)

        from live_map import get_live_map_html
        map_html = get_live_map_html(os.getenv('MTA_API_KEY'), selected_routes, buses)
        st_html(map_html, height=570)
    else:
        st.warning("Select at least one route to view the map.")
