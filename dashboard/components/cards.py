import streamlit as st
from datetime import datetime

def page_header(title, subtitle):
    """Render consistent page header."""
    st.markdown(f"""
    <div style="margin-bottom:32px;">
      <div style="font-size:13px; color:#6B6B8A;
                  margin-bottom:4px;">
        {datetime.now().strftime('%A, %B %d')} · {subtitle}
      </div>
      <h1 style="font-family:Bricolage Grotesque;
                 font-size:36px; font-weight:700;
                 color:#1A1A2E; margin:0;">
        {title}
      </h1>
    </div>
    """, unsafe_allow_html=True)

def divider():
    """Render section divider."""
    st.markdown("""
    <div style="height:1px; background:#E8E6E0;
                margin:28px 0;"></div>
    """, unsafe_allow_html=True)

def section_header(title, subtitle=""):
    """Render section heading."""
    subtitle_html = f"""
    <p style="color:#6B6B8A; font-size:14px;
              margin-top:4px;">{subtitle}</p>
    """ if subtitle else ""
    st.markdown(f"""
    <div style="margin:32px 0 16px;">
      <h2 style="font-family:Bricolage Grotesque;
                 font-size:22px; font-weight:700;
                 color:#1A1A2E !important;">{title}</h2>
      {subtitle_html}
    </div>
    """, unsafe_allow_html=True)

def kpi_card(label, value, delta_text, delta_good):
    """Render a KPI metric card."""
    color = "#16A34A" if delta_good else "#DC2626"
    bg    = "#DCFCE7" if delta_good else "#FEE2E2"
    arrow = "↑" if delta_good else "↓"
    return f"""
    <div style="background:#FFFFFF;
                border:1px solid #E8E6E0;
                border-radius:16px; padding:20px 24px;">
      <div style="font-size:12px; font-weight:600;
                  color:#6B6B8A; text-transform:uppercase;
                  letter-spacing:0.5px; margin-bottom:8px;">
        {label}
      </div>
      <div style="font-size:32px; font-weight:700;
                  color:#1A1A2E; margin-bottom:10px;
                  font-family:Bricolage Grotesque;">
        {value}
      </div>
      <div style="display:inline-flex; align-items:center;
                  gap:4px; background:{bg}; color:{color};
                  padding:3px 10px; border-radius:20px;
                  font-size:12px; font-weight:600;">
        {arrow} {delta_text}
      </div>
    </div>
    """

def grade_card(route, pct, grade):
    """Render a route grade card."""
    styles = {
        'A': ('#DCFCE7', '#15803D'),
        'B': ('#DBEAFE', '#1D4ED8'),
        'C': ('#FEF3C7', '#B45309'),
        'D': ('#FED7AA', '#C2410C'),
        'F': ('#FEE2E2', '#B91C1C'),
    }
    bg, tc = styles.get(grade, styles['F'])
    return f"""
    <div style="background:#FFFFFF;
                border:1px solid #E8E6E0;
                border-radius:16px; padding:24px;
                text-align:center;">
      <div style="font-size:13px; font-weight:600;
                  color:#6B6B8A; margin-bottom:12px;">
        {route}
      </div>
      <div style="width:64px; height:64px;
                  border-radius:50%; background:{bg};
                  margin:0 auto 12px; display:flex;
                  align-items:center;
                  justify-content:center;">
        <span style="font-size:28px; font-weight:700;
                     color:{tc};
                     font-family:Bricolage Grotesque;">
          {grade}
        </span>
      </div>
      <div style="font-size:22px; font-weight:700;
                  color:#1A1A2E; margin-bottom:4px;">
        {pct:.1f}%
      </div>
      <div style="font-size:12px; color:#6B6B8A;">
        on time today
      </div>
    </div>
    """

def explainer_card(icon, title, body,
                   bg="#EFF6FF", border="#BFDBFE",
                   title_color="#1E40AF",
                   body_color="#3B82F6"):
    """Render an educational explainer card."""
    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {border};
                border-radius:16px; padding:20px 24px;
                margin-bottom:24px;
                display:flex; gap:16px;">
      <div style="font-size:24px; flex-shrink:0;">
        {icon}
      </div>
      <div>
        <div style="font-weight:600; color:{title_color};
                    margin-bottom:4px; font-size:15px;">
          {title}
        </div>
        <div style="color:{body_color}; font-size:14px;
                    line-height:1.6;">
          {body}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def severity_bar(route, count, max_count):
    """Render a bunching severity progress bar."""
    pct = (count / max_count * 100) if max_count > 0 else 0
    if count > 100:
        label, color, bg = 'Critical','#DC2626','#FEE2E2'
    elif count > 50:
        label, color, bg = 'High','#EA580C','#FED7AA'
    elif count > 20:
        label, color, bg = 'Medium','#D97706','#FEF3C7'
    else:
        label, color, bg = 'Low','#16A34A','#DCFCE7'
    return f"""
    <div style="background:#FFFFFF;
                border:1px solid #E8E6E0;
                border-radius:12px; padding:16px 20px;
                margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between;
                  align-items:center; margin-bottom:10px;">
        <div style="display:flex; align-items:center;
                    gap:10px;">
          <span style="font-weight:600; font-size:15px;
                       color:#1A1A2E;">{route}</span>
          <span style="background:{bg}; color:{color};
                       font-size:11px; font-weight:600;
                       padding:2px 8px;
                       border-radius:20px;">{label}</span>
        </div>
        <span style="font-size:15px; font-weight:700;
                     color:#1A1A2E;">{count} events</span>
      </div>
      <div style="background:#F5F4F0; border-radius:100px;
                  height:8px; overflow:hidden;">
        <div style="background:{color};
                    width:{min(pct,100):.0f}%;
                    height:100%;
                    border-radius:100px;"></div>
      </div>
    </div>
    """
