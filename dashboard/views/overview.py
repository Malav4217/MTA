import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))
from database.connection import safe_query
from dashboard.components.cards import (
    page_header, section_header, divider, kpi_card, grade_card
)
from dashboard.components.charts import on_time_bar_chart, delay_heatmap


def _normalize_route_names(df):
    if 'route' in df.columns:
        df['route'] = df['route'].astype(str).str.replace('MTA NYCT_', '', regex=False)
    return df


def _get_route_grade(on_time_pct):
    if on_time_pct > 80:  return 'A', '🟩'
    if on_time_pct >= 60: return 'B', '🟢'
    if on_time_pct >= 40: return 'C', '🟡'
    if on_time_pct >= 20: return 'D', '🟠'
    return 'F', '🔴'


def _get_data(table_name, where_clause=None):
    query = f"SELECT * FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    result = safe_query(query)
    return result if result is not None else pd.DataFrame()


def render():
    today = str(date.today())

    st.markdown(f"""
    <div style="margin-bottom: 32px;">
      <div style="font-size: 13px; color: #6B6B8A; margin-bottom: 4px;">
        {datetime.now().strftime('%A, %B %d')} · Live dashboard
      </div>
      <h1 style="font-family: Bricolage Grotesque; font-size: 36px;
                  font-weight: 700; color: #1A1A2E; margin: 0;">
        Performance Overview
      </h1>
    </div>
    """, unsafe_allow_html=True)

    arrivals_df = _normalize_route_names(
        _get_data("bus_arrivals", f"CAST(date AS DATE) = '{today}'")
    )
    if arrivals_df.empty:
        st.warning("No data available yet.")
        return

    total_buses = arrivals_df['vehicle_id'].nunique()
    on_time_pct = (arrivals_df['is_on_time'].sum() / len(arrivals_df)) * 100

    avg_delay_df = safe_query(f"""
        SELECT ROUND(AVG(delay_minutes), 2) as v
        FROM bus_arrivals
        WHERE CAST(date AS VARCHAR) = '{today}'
        AND delay_minutes BETWEEN -5 AND 30
    """)
    avg_delay = float(avg_delay_df.iloc[0, 0]) if (
        avg_delay_df is not None and not avg_delay_df.empty
        and avg_delay_df.iloc[0, 0] is not None
    ) else 0.0

    ghosts_df = _normalize_route_names(
        _get_data("ghost_buses", f"CAST(captured_date AS DATE) = '{today}'")
    )
    ghost_count = len(ghosts_df) if not ghosts_df.empty else 0

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                    border-radius: 16px; padding: 20px 24px;">
          <div style="font-size: 12px; font-weight: 600; color: #6B6B8A;
                      text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            Buses Tracked
          </div>
          <div style="font-size: 32px; font-weight: 700; color: #1A1A2E;
                      margin-bottom: 10px; font-family: Bricolage Grotesque;">
            {total_buses}
          </div>
          <div style="display: inline-flex; align-items: center; gap: 4px;
                      background: #DBEAFE; color: #2563EB;
                      padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            ↑ Live now
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        delay_good = avg_delay < 2
        bg = "#DCFCE7" if delay_good else "#FEE2E2"
        color = "#16A34A" if delay_good else "#DC2626"
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                    border-radius: 16px; padding: 20px 24px;">
          <div style="font-size: 12px; font-weight: 600; color: #6B6B8A;
                      text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            Avg Delay
          </div>
          <div style="font-size: 32px; font-weight: 700; color: #1A1A2E;
                      margin-bottom: 10px; font-family: Bricolage Grotesque;">
            {avg_delay:.1f}min
          </div>
          <div style="display: inline-flex; align-items: center; gap: 4px;
                      background: {bg}; color: {color};
                      padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            {'↓' if delay_good else '↑'} {'Below' if delay_good else 'Above'} schedule
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        on_time_good = on_time_pct >= 60
        bg = "#DCFCE7" if on_time_good else "#FEE2E2"
        color = "#16A34A" if on_time_good else "#DC2626"
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                    border-radius: 16px; padding: 20px 24px;">
          <div style="font-size: 12px; font-weight: 600; color: #6B6B8A;
                      text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            On-Time Rate
          </div>
          <div style="font-size: 32px; font-weight: 700; color: #1A1A2E;
                      margin-bottom: 10px; font-family: Bricolage Grotesque;">
            {on_time_pct:.1f}%
          </div>
          <div style="display: inline-flex; align-items: center; gap: 4px;
                      background: {bg}; color: {color};
                      padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            {'↑' if on_time_good else '↓'} Of all arrivals
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        ghost_good = ghost_count < 10
        bg = "#DCFCE7" if ghost_good else "#FEE2E2"
        color = "#16A34A" if ghost_good else "#DC2626"
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                    border-radius: 16px; padding: 20px 24px;">
          <div style="font-size: 12px; font-weight: 600; color: #6B6B8A;
                      text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            Ghost Buses
          </div>
          <div style="font-size: 32px; font-weight: 700; color: #1A1A2E;
                      margin-bottom: 10px; font-family: Bricolage Grotesque;">
            {ghost_count}
          </div>
          <div style="display: inline-flex; align-items: center; gap: 4px;
                      background: {bg}; color: {color};
                      padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            {'↓' if ghost_good else '↑'} Today
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""<div style="height: 1px; background: #E8E6E0; margin: 28px 0;"></div>""", unsafe_allow_html=True)

    # Route Report Card
    st.markdown("""
    <div style="margin: 32px 0 16px;">
      <h2 style="font-family: Bricolage Grotesque; font-size: 22px;
                  font-weight: 700; color: #1A1A2E;">Route report card</h2>
      <p style="color: #6B6B8A; font-size: 14px; margin-top: 4px;">
        Based on today's on-time performance
      </p>
    </div>
    """, unsafe_allow_html=True)

    on_time_by_route = arrivals_df.groupby('route')['is_on_time'].mean().reset_index()
    on_time_by_route['is_on_time'] *= 100

    report_cols = st.columns(4)
    for idx, row in on_time_by_route.iterrows():
        grade, _ = _get_route_grade(row['is_on_time'])
        pct = row['is_on_time']

        if grade == 'A':   bg, tc = '#DCFCE7', '#15803D'
        elif grade == 'B': bg, tc = '#DBEAFE', '#1D4ED8'
        elif grade == 'C': bg, tc = '#FEF3C7', '#B45309'
        elif grade == 'D': bg, tc = '#FED7AA', '#C2410C'
        else:              bg, tc = '#FEE2E2', '#B91C1C'

        with report_cols[idx % 4]:
            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                        border-radius: 16px; padding: 24px; text-align: center;">
              <div style="font-size: 13px; font-weight: 600; color: #6B6B8A;
                          margin-bottom: 12px;">{row['route']}</div>
              <div style="width: 64px; height: 64px; border-radius: 50%;
                          background: {bg}; margin: 0 auto 12px;
                          display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 28px; font-weight: 700; color: {tc};
                             font-family: Bricolage Grotesque;">{grade}</span>
              </div>
              <div style="font-size: 22px; font-weight: 700; color: #1A1A2E;
                          margin-bottom: 4px;">{pct:.1f}%</div>
              <div style="font-size: 12px; color: #6B6B8A;">on time today</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""<div style="height: 1px; background: #E8E6E0; margin: 28px 0;"></div>""", unsafe_allow_html=True)

    # Delay distribution
    try:
        delay_dist = safe_query(f"""
            SELECT
                CASE
                    WHEN delay_minutes < 0 THEN 'Early'
                    WHEN delay_minutes <= 5 THEN 'On time'
                    WHEN delay_minutes <= 10 THEN 'Slightly late'
                    WHEN delay_minutes <= 20 THEN 'Late'
                    ELSE 'Very late'
                END as category,
                COUNT(*) as count
            FROM bus_arrivals
            WHERE CAST(date AS VARCHAR) = '{today}'
            AND delay_minutes BETWEEN -10 AND 60
            GROUP BY category
        """)

        if delay_dist is None or delay_dist.empty:
            return

        total = delay_dist['count'].sum()
        delay_dist['pct'] = (delay_dist['count'] / total * 100).round(1)

        category_config = {
            'Early':        {'color': '#2563EB', 'bg': '#DBEAFE', 'icon': '⚡',  'desc': 'Arrived ahead of schedule'},
            'On time':      {'color': '#16A34A', 'bg': '#DCFCE7', 'icon': '✓',   'desc': 'Within 5 min of schedule'},
            'Slightly late':{'color': '#D97706', 'bg': '#FEF3C7', 'icon': '!',   'desc': '5 to 10 min behind'},
            'Late':         {'color': '#EA580C', 'bg': '#FED7AA', 'icon': '!!',  'desc': '10 to 20 min behind'},
            'Very late':    {'color': '#DC2626', 'bg': '#FEE2E2', 'icon': '!!!', 'desc': 'More than 20 min late'},
        }
        ordered_categories = ['Early', 'On time', 'Slightly late', 'Late', 'Very late']

        st.markdown("""
        <div style="margin: 32px 0 16px;">
          <h2 style="font-family: Bricolage Grotesque; font-size: 22px;
                      font-weight: 700; color: #1A1A2E;">
            Delay distribution today
          </h2>
          <p style="color: #6B6B8A; font-size: 14px; margin-top: 4px;">
            Breaking down exactly how late buses are running
          </p>
        </div>
        """, unsafe_allow_html=True)

        dist_lookup = {}
        for _, row in delay_dist.iterrows():
            dist_lookup[row['category']] = {
                'count': int(row['count']),
                'pct': float(row['pct'])
            }

        for cat in ordered_categories:
            if cat not in dist_lookup:
                continue
            data   = dist_lookup[cat]
            config = category_config[cat]
            pct    = data['pct']
            count  = data['count']
            color  = config['color']
            bg     = config['bg']
            desc   = config['desc']
            icon   = config['icon']

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                        border-radius: 14px; padding: 16px 20px;
                        margin-bottom: 10px;">
              <div style="display: flex; align-items: center;
                          justify-content: space-between; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                  <div style="width: 36px; height: 36px; background: {bg};
                              border-radius: 10px; display: flex;
                              align-items: center; justify-content: center;
                              font-size: 13px; font-weight: 700; color: {color};
                              flex-shrink: 0;">
                    {icon}
                  </div>
                  <div>
                    <div style="font-size: 15px; font-weight: 600; color: #1A1A2E;">
                      {cat}
                    </div>
                    <div style="font-size: 12px; color: #6B6B8A;">
                      {desc}
                    </div>
                  </div>
                </div>
                <div style="text-align: right;">
                  <div style="font-size: 22px; font-weight: 700; color: {color};">
                    {pct}%
                  </div>
                  <div style="font-size: 12px; color: #6B6B8A;">
                    {count:,} arrivals
                  </div>
                </div>
              </div>
              <div style="background: #F5F4F0; border-radius: 100px;
                          height: 8px; overflow: hidden;">
                <div style="background: {color}; width: {min(pct, 100):.1f}%;
                            height: 100%; border-radius: 100px;
                            transition: width 0.3s ease;">
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        on_time_pct_dist = dist_lookup.get('On time', {}).get('pct', 0)
        early_pct        = dist_lookup.get('Early', {}).get('pct', 0)
        very_late_pct    = dist_lookup.get('Very late', {}).get('pct', 0)
        good_pct         = round(on_time_pct_dist + early_pct, 1)

        st.markdown(f"""
        <div style="background: #F5F4F0; border-radius: 14px;
                    padding: 16px 20px; margin-top: 4px;
                    display: flex; align-items: center; gap: 12px;">
          <div style="font-size: 24px;">💡</div>
          <div style="font-size: 14px; color: #1A1A2E; line-height: 1.6;">
            <strong>{good_pct}%</strong> of buses arrive on time or early today.
            <strong style="color: #DC2626;">{very_late_pct}%</strong> are
            more than 20 minutes behind schedule.
            Across <strong>{total:,}</strong> recorded arrivals.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""<div style="height: 1px; background: #E8E6E0; margin: 28px 0;"></div>""", unsafe_allow_html=True)

    except Exception:
        pass
