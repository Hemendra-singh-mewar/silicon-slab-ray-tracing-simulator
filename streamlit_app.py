import math
import time
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Silicon Ray Optics Simulator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1500px;}
h1 {font-weight: 700; letter-spacing: -0.02em;}
.small-note {color:#6b7280; font-size:0.9rem;}
.metric-card {
    border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px;
    background: #ffffff; min-height: 95px;
}
.metric-label {font-size:0.82rem; color:#6b7280;}
.metric-value {font-size:1.45rem; font-weight:700; margin-top:4px;}
section[data-testid="stSidebar"] {border-right: 1px solid #e5e7eb;}
</style>
""", unsafe_allow_html=True)

st.title("Silicon Ray Optics Simulator")
st.caption("Interactive geometry for reflected-beam separation and the silicon → air critical angle")

with st.sidebar:
    st.header("Simulation")
    mode = st.radio(
        "Mode",
        ["Reflected beam gap", "Critical angle"],
        label_visibility="collapsed",
    )

    st.divider()
    st.subheader("Optical parameters")

    if mode == "Reflected beam gap":
        preset = st.selectbox(
            "Preset",
            ["Your 29.7 mm example", "Custom"],
            index=0,
        )
        if preset == "Your 29.7 mm example":
            t = 29.7
            incidence_deg = 45.0
            n_si = 3.48
            n_air = 1.0003
            wavelength = 1550.0
        else:
            t = st.slider("Silicon thickness, t (mm)", 0.1, 100.0, 29.7, 0.1)
            incidence_deg = st.slider("Angle of incidence, i (°)", 0.0, 89.0, 45.0, 0.1)
            n_si = st.number_input("Silicon refractive index", 1.0001, 10.0, 3.48, 0.0001, format="%.4f")
            n_air = st.number_input("Air refractive index", 1.0, 1.1, 1.0003, 0.0001, format="%.4f")
            wavelength = st.number_input("Wavelength (nm)", 200.0, 5000.0, 1550.0, 1.0)

        st.divider()
        st.subheader("Display")
        show_normals = st.checkbox("Show surface normals", True)
        show_dimensions = st.checkbox("Show dimensions", True)

    else:
        n_from = st.number_input("Incident medium refractive index", 1.0001, 10.0, 3.48, 0.0001, format="%.4f")
        n_to = st.number_input("Second medium refractive index", 1.0, 10.0, 1.0003, 0.0001, format="%.4f")
        critical_deg = math.degrees(math.asin(n_to / n_from)) if n_from > n_to else None

        animate = st.button("▶ Animate incidence angle", use_container_width=True)
        angle = st.slider("Incidence angle (°)", 0.0, 89.9, 10.0, 0.1)
        st.divider()
        st.subheader("Display")
        show_normals = st.checkbox("Show normal", True)

def add_segment(fig, x, y, name, width=4, dash=None, showlegend=True):
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", name=name,
        line=dict(width=width, dash=dash) if dash else dict(width=width),
        hoverinfo="skip", showlegend=showlegend
    ))

def base_figure(x_range=(-35, 65), y_range=(-40, 25)):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        height=650,
        margin=dict(l=30, r=20, t=20, b=30),
        xaxis=dict(title="Distance (mm)", range=list(x_range), zeroline=False, showgrid=True),
        yaxis=dict(title="Distance (mm)", range=list(y_range), zeroline=False, showgrid=True, scaleanchor="x", scaleratio=1),
        legend=dict(orientation="h", y=1.02, x=0),
        hovermode=False,
    )
    return fig

if mode == "Reflected beam gap":
    i = math.radians(incidence_deg)

    # Snell's law, air -> silicon
    sin_r = (n_air / n_si) * math.sin(i)
    sin_r = max(-1.0, min(1.0, sin_r))
    r = math.asin(sin_r)

    # User's geometrical definition of the separation.
    gap = 2.0 * t * math.tan(r) * math.cos(i)
    internal_shift = 2.0 * t * math.tan(r)
    critical = math.degrees(math.asin(n_air / n_si)) if n_si > n_air else 90.0

    # Geometry: top surface y=0, back surface y=-t.
    # Incident ray arrives at x=0, y=0.
    x_inc_start = -25.0
    y_inc_start = -x_inc_start * math.tan(i)
    x_back = t * math.tan(r)
    x_front_backray = 2.0 * x_back

    fig = base_figure(
        x_range=(min(-30, x_inc_start-5), max(45, x_front_backray+15)),
        y_range=(-max(40, t*1.25), max(20, y_inc_start+5))
    )

    # Surfaces
    fig.add_hrect(y0=-t, y1=0, fillcolor="rgba(100,160,210,0.10)", line_width=0)
    add_segment(fig, [-40, 70], [0, 0], "Front surface", width=3, showlegend=False)
    add_segment(fig, [-40, 70], [-t, -t], "Back surface", width=3, showlegend=False)

    # Incident ray
    add_segment(fig, [x_inc_start, 0], [y_inc_start, 0], "Incident beam", width=4)

    # Front reflected ray
    x_front_end = 22
    y_front_end = x_front_end * math.tan(i)
    add_segment(fig, [0, x_front_end], [0, y_front_end], "Front reflected beam", width=4)

    # Refracted/internal ray down to back surface
    add_segment(fig, [0, x_back], [0, -t], "Refracted beam", width=4)

    # Internal reflection back to front
    add_segment(fig, [x_back, x_front_backray], [-t, 0], "Internal reflection", width=3)

    # Back reflected beam emerging from front
    x_back_end = x_front_backray + 22
    y_back_end = (x_back_end - x_front_backray) * math.tan(i)
    add_segment(fig, [x_front_backray, x_back_end], [0, y_back_end], "Back reflected beam", width=4)

    if show_normals:
        normal_len = max(8, t * 0.25)
        add_segment(fig, [0, 0], [-normal_len, normal_len], "Normal", width=1.5, dash="dash", showlegend=False)
        add_segment(fig, [x_back, x_back], [-t-normal_len*0.15, -t+normal_len], "Normal", width=1.5, dash="dash", showlegend=False)

    if show_dimensions:
        # Thickness marker
        xdim = -10
        add_segment(fig, [xdim, xdim], [0, -t], "Thickness", width=1.5, dash="dot", showlegend=False)
        fig.add_annotation(x=xdim-2, y=-t/2, text=f"t = {t:.2f} mm", textangle=-90, showarrow=False)
        # Gap marker, measured perpendicular to the reflected rays
        # The separation between the two parallel reflected rays is gap.
        fig.add_annotation(
            x=(x_front_end + x_back_end)/2,
            y=max(y_front_end, y_back_end)/2 + 4,
            text=f"Gap = {gap:.2f} mm",
            showarrow=False,
            font=dict(size=15)
        )

    fig.add_annotation(x=3, y=4, text=f"i = {incidence_deg:.2f}°", showarrow=False)
    fig.add_annotation(x=2.5, y=-min(t*0.25, 8), text=f"r = {math.degrees(r):.2f}°", showarrow=False)

    st.subheader("Reflected beam separation")

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("Refracted angle, r", f"{math.degrees(r):.2f}°"),
        ("Internal displacement", f"{internal_shift:.2f} mm"),
        ("Reflected beam gap", f"{gap:.2f} mm"),
        ("Critical angle", f"{critical:.2f}°"),
    ]
    for col, (label, value) in zip([c1,c2,c3,c4], cards):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with st.expander("Equations and calculation", expanded=True):
        st.latex(r"n_{\rm air}\sin i=n_{\rm Si}\sin r")
        st.latex(r"r=\sin^{-1}\left(\frac{n_{\rm air}}{n_{\rm Si}}\sin i\right)")
        st.latex(r"G=2t\tan(r)\cos(i)")
        st.write(
            f"For the current parameters: "
            f"$r={math.degrees(r):.4f}^\\circ$, "
            f"$2t\\tan(r)={internal_shift:.4f}\\,\\mathrm{{mm}}$, "
            f"and $G={gap:.4f}\\,\\mathrm{{mm}}$."
        )

else:
    if n_from > n_to:
        critical_deg = math.degrees(math.asin(n_to / n_from))
    else:
        critical_deg = None

    is_tir = critical_deg is not None and angle > critical_deg
    a = math.radians(angle)

    # Draw a silicon region below y=0, with incidence from inside silicon.
    fig = base_figure(x_range=(-30, 35), y_range=(-25, 25))
    fig.add_hrect(y0=-25, y1=0, fillcolor="rgba(100,160,210,0.10)", line_width=0)
    add_segment(fig, [-40, 45], [0, 0], "Interface", width=3, showlegend=False)

    # Incident ray ends at origin.
    inc_len = 22
    xi = -inc_len * math.sin(a)
    yi = -inc_len * math.cos(a)
    add_segment(fig, [xi, 0], [yi, 0], "Incident ray", width=4)

    if show_normals:
        add_segment(fig, [0,0], [0,18], "Normal", width=1.5, dash="dash", showlegend=False)

    if not is_tir and critical_deg is not None:
        sin_t = (n_from / n_to) * math.sin(a)
        if abs(sin_t) <= 1:
            b = math.asin(sin_t)
            refr_len = 25
            xr = refr_len * math.sin(b)
            yr = refr_len * math.cos(b)
            add_segment(fig, [0, xr], [0, yr], "Refracted ray", width=4)
    else:
        # TIR: reflected ray remains in incident medium.
        xr = inc_len * math.sin(a)
        yr = -inc_len * math.cos(a)
        add_segment(fig, [0, xr], [0, yr], "Reflected ray (TIR)", width=4)

    title_state = "TOTAL INTERNAL REFLECTION" if is_tir else "REFRACTION"
    if critical_deg is not None:
        fig.add_annotation(
            x=0, y=21,
            text=f"{title_state}  |  θc = {critical_deg:.2f}°",
            showarrow=False, font=dict(size=16)
        )

    st.subheader("Critical angle and total internal reflection")

    if critical_deg is None:
        st.error("A critical angle exists only when the incident medium has the higher refractive index.")
    else:
        c1, c2, c3 = st.columns(3)
        vals = [
            ("Critical angle", f"{critical_deg:.2f}°"),
            ("Current angle", f"{angle:.2f}°"),
            ("Regime", "TIR" if is_tir else "Refraction"),
        ]
        for col, (label, value) in zip([c1,c2,c3], vals):
            with col:
                st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.latex(r"\theta_c=\sin^{-1}\left(\frac{n_2}{n_1}\right)")
        st.caption(
            f"Here n₁ = {n_from:.4f} and n₂ = {n_to:.4f}. "
            f"At angles above θc the transmitted ray is replaced by total internal reflection."
        )

        if animate:
            progress = st.progress(0)
            status = st.empty()
            for deg in np.linspace(0, min(35.0, 1.8*critical_deg), 70):
                progress.progress(int((deg / min(35.0, 1.8*critical_deg)) * 100))
                status.write(f"Animating incidence angle: **{deg:.1f}°**")
                time.sleep(0.025)
            status.write("Animation complete. Use the slider to inspect the transition in detail.")
