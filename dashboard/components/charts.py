import plotly.express as px
import plotly.graph_objects as go

CHART_LAYOUT = dict(
    plot_bgcolor='#FFFFFF',
    paper_bgcolor='#FFFFFF',
    font_color='#1A1A2E',
    margin=dict(l=0, r=0, t=40, b=0),
    showlegend=False,
)

def on_time_bar_chart(df):
    """Bar chart colored by performance level."""
    colors = []
    for pct in df['on_time_pct']:
        if pct >= 60:   colors.append('#16A34A')
        elif pct >= 40: colors.append('#D97706')
        else:           colors.append('#DC2626')

    fig = go.Figure(go.Bar(
        x=df['route'],
        y=df['on_time_pct'],
        marker_color=colors,
        text=[f"{p:.1f}%" for p in df['on_time_pct']],
        textposition='outside',
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title="On-Time Performance by Route",
        yaxis=dict(
            gridcolor='#F0EEE8',
            ticksuffix='%',
            range=[0, 110]
        ),
        xaxis=dict(showgrid=False),
        bargap=0.3
    )
    return fig

def bunching_hourly_chart(df):
    """Line chart of bunching events by hour."""
    if df.empty:
        return None
    peak_idx    = df['events'].idxmax()
    peak_hour   = int(df.loc[peak_idx, 'hour'])
    peak_events = int(df.loc[peak_idx, 'events'])

    fig = go.Figure(go.Scatter(
        x=df['hour'], y=df['events'],
        mode='lines+markers',
        line=dict(color='#2563EB', width=2),
        marker=dict(size=6, color='#2563EB'),
    ))
    fig.add_vline(
        x=peak_hour, line_dash="dash",
        line_color="#DC2626",
        annotation_text=f"Peak: {peak_events} events",
        annotation_position="top right",
        annotation_font_color="#DC2626"
    )
    fig.update_layout(
        **CHART_LAYOUT,
        title="Bunching Events by Hour (Today)",
        xaxis=dict(
            tickmode='linear', tick0=0, dtick=1,
            range=[-0.5, 23.5], showgrid=False,
            title="Hour of Day"
        ),
        yaxis=dict(
            gridcolor='#F0EEE8',
            rangemode='tozero',
            title="Number of Events"
        )
    )
    return fig

def delay_heatmap(df):
    """Heatmap of avg delay by route and hour."""
    if df.empty:
        return None
    pivot = df.pivot(
        index='route',
        columns='hour',
        values='avg_delay'
    )
    fig = px.imshow(
        pivot,
        color_continuous_scale='RdYlGn_r',
        labels=dict(
            x="Hour of Day", y="Route",
            color="Avg Delay (min)"
        ),
        title="Average Delay Heatmap (Today)"
    )
    fig.update_layout(**CHART_LAYOUT, showlegend=True)
    return fig
