import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))
from database.connection import safe_query
from dashboard.components.cards import (
    page_header, section_header, divider, explainer_card
)


def _normalize_route_names(df):
    if 'route' in df.columns:
        df['route'] = df['route'].astype(str).str.replace('MTA NYCT_', '', regex=False)
    return df


def render():
    today = str(date.today())

    st.markdown(f"""
    <div style="margin-bottom: 32px;">
      <div style="font-size: 13px; color: #6B6B8A; margin-bottom: 4px;">
        {datetime.now().strftime('%A, %B %d')} · Live tracking
      </div>
      <h1 style="font-family: Bricolage Grotesque; font-size: 36px;
                  font-weight: 700; color: #1A1A2E; margin: 0;">
        Ghost Bus Tracker
      </h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 16px;
                padding: 20px 24px; margin-bottom: 24px; display: flex; gap: 16px;">
      <div style="font-size: 24px; flex-shrink: 0;">👻</div>
      <div>
        <div style="font-weight: 600; color: #1E40AF; margin-bottom: 4px; font-size: 15px;">
          What is a ghost bus?
        </div>
        <div style="color: #3B82F6; font-size: 14px; line-height: 1.6;">
          A ghost bus appears in the MTA app with a promised arrival time
          but vanishes before reaching your stop — leaving riders stranded
          with no warning. Our pipeline detects these automatically.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    ghost_df = safe_query(f"""
        SELECT
            route,
            vehicle_id,
            last_seen_at,
            distance_at_disappear,
            captured_date
        FROM ghost_buses
        WHERE CAST(captured_date AS DATE) = '{today}'
        ORDER BY last_seen_at DESC
    """)

    if ghost_df is None:
        ghost_df = pd.DataFrame()
    else:
        ghost_df = _normalize_route_names(ghost_df)

    if not ghost_df.empty:
        ghost_count  = len(ghost_df)
        worst_route  = ghost_df['route'].value_counts().index[0]
        worst_count  = ghost_df['route'].value_counts().values[0]

        total_df = safe_query(f"""
            SELECT COUNT(DISTINCT vehicle_id)
            FROM raw_bus_snapshots
            WHERE CAST(captured_at AS DATE) = '{today}'
        """)
        total_scheduled = int(total_df.iloc[0, 0]) if (
            total_df is not None and not total_df.empty
        ) else 0
        ghost_rate = round((ghost_count / total_scheduled * 100), 1) if total_scheduled > 0 else 0

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div style="background:#FFFFFF;
                        border:1px solid #E8E6E0;
                        border-radius:16px;
                        padding:20px 24px;">
              <div style="font-size:12px; font-weight:600;
                          color:#6B6B8A; text-transform:uppercase;
                          letter-spacing:0.5px; margin-bottom:8px;">
                Total Ghosts
              </div>
              <div style="font-size:36px; font-weight:700;
                          color:#1A1A2E;
                          font-family:Bricolage Grotesque;">
                {ghost_count}
              </div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div style="background:#FFFFFF;
                        border:1px solid #E8E6E0;
                        border-radius:16px;
                        padding:20px 24px;">
              <div style="font-size:12px; font-weight:600;
                          color:#6B6B8A; text-transform:uppercase;
                          letter-spacing:0.5px; margin-bottom:8px;">
                Worst Route
              </div>
              <div style="font-size:36px; font-weight:700;
                          color:#DC2626;
                          font-family:Bricolage Grotesque;">
                {worst_route}
              </div>
              <div style="font-size:13px; color:#6B6B8A;
                          margin-top:4px;">
                {worst_count} incidents today
              </div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div style="background:#FFFFFF;
                        border:1px solid #E8E6E0;
                        border-radius:16px;
                        padding:20px 24px;">
              <div style="font-size:12px; font-weight:600;
                          color:#6B6B8A; text-transform:uppercase;
                          letter-spacing:0.5px; margin-bottom:8px;">
                Ghost Rate
              </div>
              <div style="font-size:36px; font-weight:700;
                          color:#1A1A2E;
                          font-family:Bricolage Grotesque;">
                {ghost_rate}%
              </div>
              <div style="font-size:13px; color:#6B6B8A;
                          margin-top:4px;">
                of vehicles ghosted today
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""<div style="height: 1px; background: #E8E6E0; margin: 28px 0;"></div>""", unsafe_allow_html=True)

        st.markdown("### Recent Incidents")

        for _, row in ghost_df.head(15).iterrows():
            vanished_time = pd.to_datetime(row['last_seen_at']).strftime('%H:%M')
            distance_text = (
                f"Was {row['distance_at_disappear']:.0f}m from stop"
                if pd.notna(row['distance_at_disappear'])
                else "Distance unknown"
            )

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E8E6E0; border-radius: 12px;
                        padding: 16px 20px; margin-bottom: 10px;">
              <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <div style="background: #FEE2E2; color: #DC2626; font-size: 12px;
                            font-weight: 600; padding: 4px 10px; border-radius: 20px;">
                  {row['route']}
                </div>
                <div style="color: #6B6B8A; font-size: 13px; font-weight: 500;">
                  Vehicle MTA_{row['vehicle_id']}
                </div>
                <div style="color: #6B6B8A; font-size: 13px; font-weight: 500;">
                  Vanished at {vanished_time}
                </div>
                <div style="color: #6B6B8A; font-size: 13px; font-weight: 500;">
                  {distance_text}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No ghost buses detected today!")
