import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))
from database.connection import safe_query
from dashboard.components.cards import (
    page_header, section_header, divider, explainer_card, severity_bar
)
from dashboard.components.charts import bunching_hourly_chart


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
        Bus Bunching Analysis
      </h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 16px;
                padding: 20px 24px; margin-bottom: 24px; display: flex; gap: 16px;">
      <div style="font-size: 24px; flex-shrink: 0;">🚌</div>
      <div>
        <div style="font-weight: 600; color: #C2410C; margin-bottom: 4px; font-size: 15px;">
          What is bus bunching?
        </div>
        <div style="color: #EA580C; font-size: 14px; line-height: 1.6;">
          When buses cluster together on the same route instead of staying evenly spaced.
          You wait 20 minutes then 3 buses arrive at once. Our pipeline detects this automatically.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    bunching_df = safe_query(f"SELECT * FROM bunching_events WHERE CAST(timestamp AS DATE) = '{today}'")
    if bunching_df is not None:
        bunching_df = _normalize_route_names(bunching_df)
    else:
        bunching_df = pd.DataFrame()

    if not bunching_df.empty:
        bunching_by_route = bunching_df['route'].value_counts().reset_index()
        bunching_by_route.columns = ['route', 'count']

        st.markdown("### Bunching Severity")

        max_count = bunching_by_route['count'].max()

        for _, row in bunching_by_route.iterrows():
            count = row['count']
            pct   = (count / max_count) * 100

            if count > 100:
                label, color, bg = 'Critical', '#DC2626', '#FEE2E2'
            elif count > 50:
                label, color, bg = 'High',     '#EA580C', '#FED7AA'
            elif count > 20:
                label, color, bg = 'Medium',   '#D97706', '#FEF3C7'
            else:
                label, color, bg = 'Low',      '#16A34A', '#DCFCE7'

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E8E6E0;
                        border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between;
                          align-items: center; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <span style="font-weight: 600; font-size: 15px; color: #1A1A2E;">{row['route']}</span>
                  <span style="background: {bg}; color: {color}; font-size: 11px;
                               font-weight: 600; padding: 2px 8px; border-radius: 20px;">
                    {label}
                  </span>
                </div>
                <span style="font-size: 15px; font-weight: 700; color: #1A1A2E;">
                  {count} events
                </span>
              </div>
              <div style="background: #F5F4F0; border-radius: 100px; height: 8px; overflow: hidden;">
                <div style="background: {color}; width: {pct:.0f}%; height: 100%;
                            border-radius: 100px;"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""<div style="height: 1px; background: #E8E6E0; margin: 28px 0;"></div>""", unsafe_allow_html=True)

        bunching_by_hour = safe_query(f"""
            SELECT
                EXTRACT(HOUR FROM timestamp) as hour,
                COUNT(*) as events
            FROM bunching_events
            WHERE CAST(timestamp AS DATE) = '{today}'
            GROUP BY hour
            ORDER BY hour
        """)

        if bunching_by_hour is not None and not bunching_by_hour.empty:
            bunching_by_hour['hour'] = bunching_by_hour['hour'].astype(int)

            peak_hour   = bunching_by_hour.loc[bunching_by_hour['events'].idxmax(), 'hour']
            peak_events = bunching_by_hour['events'].max()

            fig = px.line(
                bunching_by_hour,
                x='hour',
                y='events',
                title='Bunching events by hour of day (today)',
                markers=True
            )

            fig.add_vline(x=peak_hour, line_width=2, line_dash="dash", line_color="#DC2626")
            fig.add_annotation(
                x=peak_hour,
                y=peak_events,
                text=f"Peak: {peak_events} events",
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-40,
                font=dict(size=12, color="#DC2626")
            )

            fig.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#F5F4F0',
                font_color='#1A1A2E',
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(size=13, color='#1A1A2E'),
                    tickmode='linear',
                    tick0=0,
                    dtick=1,
                    range=[0, 23]
                ),
                yaxis=dict(gridcolor='#E8E6E0', tickfont=dict(size=12, color='#6B6B8A')),
                margin=dict(l=0, r=0, t=0, b=0),
                height=300
            )

            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No bunching events today!")
