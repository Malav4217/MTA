import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))
from database.connection import safe_query
from dashboard.components.cards import (
    page_header, section_header, divider
)


def render():
    from config import DATE_CONFIG
    start_date = st.session_state.get('start_date', DATE_CONFIG['start_date'])
    end_date   = st.session_state.get('end_date',   DATE_CONFIG['end_date'])
    start_str  = str(start_date)
    end_str    = str(end_date)

    st.markdown(f"""
    <div style="margin-bottom: 32px;">
      <div style="font-size: 13px; color: #6B6B8A; margin-bottom: 4px;">
        {start_str} → {end_str} · Live analysis
      </div>
      <h1 style="font-family: Bricolage Grotesque; font-size: 36px;
                  font-weight: 700; color: #1A1A2E; margin: 0;">
        Route Analysis
      </h1>
    </div>
    """, unsafe_allow_html=True)

    # Best time to ride today
    try:
        now = datetime.now()
        min_arrivals = 2 if now.hour < 12 else 10
        best_worst_hours = safe_query(f"""
            SELECT
                REPLACE(route, 'MTA NYCT_', '') as route,
                hour,
                ROUND(AVG(delay_minutes), 1) as avg_delay,
                COUNT(*) as arrivals
            FROM bus_arrivals
            WHERE date BETWEEN DATE '{start_str}' AND DATE '{end_str}'
            AND delay_minutes BETWEEN 0 AND 30
            AND hour IS NOT NULL
            GROUP BY route, hour
            HAVING COUNT(*) >= {min_arrivals}
            ORDER BY route, avg_delay ASC
        """)

        if best_worst_hours is None:
            best_worst_hours = pd.DataFrame()

        route_insights = {}
        for route in best_worst_hours['route'].unique():
            route_df = best_worst_hours[best_worst_hours['route'] == route]
            if len(route_df) >= 2:
                best  = route_df.iloc[0]
                worst = route_df.iloc[-1]
                route_insights[route] = {
                    'best_hour':   int(best['hour']),
                    'best_delay':  float(best['avg_delay']),
                    'worst_hour':  int(worst['hour']),
                    'worst_delay': float(worst['avg_delay'])
                }

        def format_hour(hour):
            if hour == 0:    return "12AM"
            elif hour < 12:  return f"{hour}AM"
            elif hour == 12: return "12PM"
            else:            return f"{hour-12}PM"

        st.markdown("""
        <div style="margin: 32px 0 16px;">
          <h2 style="font-family: Bricolage Grotesque; font-size: 22px;
                      font-weight: 700; color: #1A1A2E;">
            Best time to ride
          </h2>
          <p style="color: #6B6B8A; font-size: 14px; margin-top: 4px;">
            Based on average delay per hour across selected date range
          </p>
        </div>
        """, unsafe_allow_html=True)

        if not route_insights:
            st.info("Collecting hourly data — check back soon.")
        else:
            cols = st.columns(len(route_insights))
            for i, (route, data) in enumerate(route_insights.items()):
                best_hour_str  = format_hour(data['best_hour'])
                worst_hour_str = format_hour(data['worst_hour'])
                best_delay     = data['best_delay']
                worst_delay    = data['worst_delay']
                with cols[i]:
                    st.markdown(f"""
                    <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                                border-radius: 16px; padding: 20px; height: 100%;">
                      <div style="font-size: 14px; font-weight: 700;
                                  color: #1A1A2E; margin-bottom: 16px;
                                  padding-bottom: 12px;
                                  border-bottom: 1px solid #F0EEE8;">
                        Route {route}
                      </div>
                      <div style="margin-bottom: 14px;">
                        <div style="display: flex; align-items: center;
                                    gap: 8px; margin-bottom: 6px;">
                          <div style="width: 28px; height: 28px;
                                      background: #DCFCE7; border-radius: 50%;
                                      display: flex; align-items: center;
                                      justify-content: center;
                                      font-size: 14px; flex-shrink: 0;">
                            ✓
                          </div>
                          <div>
                            <div style="font-size: 11px; color: #6B6B8A;
                                        font-weight: 600;
                                        text-transform: uppercase;
                                        letter-spacing: 0.5px;">
                              Best time
                            </div>
                            <div style="font-size: 16px; font-weight: 700;
                                        color: #16A34A;">
                              {best_hour_str}
                            </div>
                          </div>
                        </div>
                        <div style="background: #F0FDF4; border-radius: 8px;
                                    padding: 8px 12px; margin-left: 36px;">
                          <span style="font-size: 13px; color: #16A34A;
                                       font-weight: 600;">
                            Only +{best_delay} min delay
                          </span>
                        </div>
                      </div>
                      <div style="margin-bottom: 4px;">
                        <div style="display: flex; align-items: center;
                                    gap: 8px; margin-bottom: 6px;">
                          <div style="width: 28px; height: 28px;
                                      background: #FEE2E2; border-radius: 50%;
                                      display: flex; align-items: center;
                                      justify-content: center;
                                      font-size: 14px; flex-shrink: 0;">
                            ✗
                          </div>
                          <div>
                            <div style="font-size: 11px; color: #6B6B8A;
                                        font-weight: 600;
                                        text-transform: uppercase;
                                        letter-spacing: 0.5px;">
                              Avoid
                            </div>
                            <div style="font-size: 16px; font-weight: 700;
                                        color: #DC2626;">
                              {worst_hour_str}
                            </div>
                          </div>
                        </div>
                        <div style="background: #FEF2F2; border-radius: 8px;
                                    padding: 8px 12px; margin-left: 36px;">
                          <span style="font-size: 13px; color: #DC2626;
                                       font-weight: 600;">
                            +{worst_delay} min avg delay
                          </span>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
        st.markdown("""<div style="height: 1px; background: #E8E6E0; margin: 28px 0;"></div>""", unsafe_allow_html=True)
    except Exception:
        pass

    # Top 5 worst stops
    st.markdown("""
    <div style="margin: 32px 0 16px;">
      <h2 style="font-family: Bricolage Grotesque; font-size: 22px;
                  font-weight: 700; color: #1A1A2E;">
        Top 5 worst stops
      </h2>
      <p style="color: #6B6B8A; font-size: 14px; margin-top: 4px;">
        Stops with highest average delay across selected date range
      </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        worst_stops = safe_query(f"""
            SELECT
                REPLACE(route, 'MTA NYCT_', '') as route,
                stop_name,
                ROUND(AVG(delay_minutes), 1) as avg_delay,
                COUNT(*) as total_arrivals
            FROM bus_arrivals
            WHERE date BETWEEN DATE '{start_str}' AND DATE '{end_str}'
            AND delay_minutes BETWEEN 0 AND 30
            AND stop_name IS NOT NULL
            AND stop_name != 'Unknown'
            GROUP BY route, stop_name
            HAVING COUNT(*) >= 5
            ORDER BY avg_delay DESC
            LIMIT 5
        """)
        if worst_stops is None:
            worst_stops = pd.DataFrame()
    except Exception:
        worst_stops = pd.DataFrame()

    if not worst_stops.empty:
        rank_colors = ['#DC2626', '#EA580C', '#D97706', '#CA8A04', '#65A30D']
        rank_bgs    = ['#FEE2E2', '#FED7AA', '#FEF3C7', '#FEF9C3', '#DCFCE7']
        medals      = ['1st', '2nd', '3rd', '4th', '5th']
        for i, row in worst_stops.iterrows():
            color = rank_colors[i]
            bg    = rank_bgs[i]
            medal = medals[i]
            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                        border-radius: 14px; padding: 16px 20px;
                        margin-bottom: 10px;
                        display: flex; align-items: center;
                        justify-content: space-between;">
              <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background: {bg}; color: {color};
                            font-size: 11px; font-weight: 700;
                            padding: 4px 10px; border-radius: 20px;
                            min-width: 36px; text-align: center;">
                  {medal}
                </div>
                <div>
                  <div style="font-weight: 600; color: #1A1A2E; font-size: 15px;">
                    {row['stop_name']}
                  </div>
                  <div style="color: #6B6B8A; font-size: 12px; margin-top: 2px;">
                    Route {row['route']} · {row['total_arrivals']} arrivals measured
                  </div>
                </div>
              </div>
              <div style="text-align: right;">
                <div style="font-size: 22px; font-weight: 700; color: {color};">
                  +{row['avg_delay']} min
                </div>
                <div style="font-size: 11px; color: #6B6B8A;">avg delay</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No stops with sufficient data to calculate average delays yet.")

    st.markdown("""<div style="height: 1px; background: #E8E6E0; margin: 28px 0;"></div>""", unsafe_allow_html=True)

    # Route comparison
    st.markdown("""
    <div style="margin: 32px 0 16px;">
      <h2 style="font-family: Bricolage Grotesque; font-size: 22px;
                  font-weight: 700; color: #1A1A2E;">
        Route comparison
      </h2>
      <p style="color: #6B6B8A; font-size: 14px; margin-top: 4px;">
        Grades based on on-time percentage (A=80%+, B=60%+, C=40%+, D=20%+, F&lt;20%)
      </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        now = datetime.now()
        min_arrivals = 2 if now.hour < 12 else 10
        route_stats = safe_query(f"""
            SELECT
                REPLACE(route, 'MTA NYCT_', '') as route,
                ROUND(AVG(CASE WHEN is_late = false THEN 1 ELSE 0 END) * 100, 1) as on_time_pct,
                ROUND(AVG(delay_minutes), 1) as avg_delay,
                COUNT(*) as total_arrivals
            FROM bus_arrivals
            WHERE date BETWEEN DATE '{start_str}' AND DATE '{end_str}'
            AND delay_minutes BETWEEN 0 AND 30
            AND is_late IS NOT NULL
            GROUP BY route
            HAVING COUNT(*) >= {min_arrivals}
            ORDER BY on_time_pct DESC
        """)
        if route_stats is None:
            route_stats = pd.DataFrame()
    except Exception:
        route_stats = pd.DataFrame()

    def get_grade(pct):
        if pct >= 80:  return 'A'
        elif pct >= 60: return 'B'
        elif pct >= 40: return 'C'
        elif pct >= 20: return 'D'
        else:           return 'F'

    grade_colors = {
        'A': ('#22C55E', '#DCFCE7'),
        'B': ('#2563EB', '#DBEAFE'),
        'C': ('#F59E42', '#FEF3C7'),
        'D': ('#EA580C', '#FED7AA'),
        'F': ('#DC2626', '#FEE2E2'),
    }

    if not route_stats.empty:
        for _, row in route_stats.iterrows():
            grade       = get_grade(row['on_time_pct'])
            color, bg   = grade_colors[grade]
            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E8E6E0; border-radius: 14px;
                        padding: 16px 20px; margin-bottom: 10px;
                        display: flex; align-items: center; justify-content: space-between;">
              <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background: {bg}; color: {color}; font-size: 15px; font-weight: 700;
                            padding: 6px 16px; border-radius: 20px; min-width: 36px; text-align: center;">
                  {grade}
                </div>
                <div>
                  <div style="font-weight: 600; color: #1A1A2E; font-size: 16px;">
                    Route {row['route']}
                  </div>
                  <div style="color: #6B6B8A; font-size: 13px; margin-top: 2px;">
                    {row['on_time_pct']}% on time · {row['total_arrivals']} arrivals
                  </div>
                </div>
              </div>
              <div style="text-align: right; min-width: 120px;">
                <div style="font-size: 18px; font-weight: 700; color: {color};">
                  +{row['avg_delay']} min avg delay
                </div>
                <div style="margin-top: 6px; width: 100%; background: #F3F4F6;
                            border-radius: 8px; height: 10px; position: relative;">
                  <div style="width: {row['on_time_pct']}%; background: {color};
                              height: 10px; border-radius: 8px;"></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Not enough data to compare routes yet.")
