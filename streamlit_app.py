import numpy as np
import streamlit as st
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Silicon Ray Optics Simulator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 16px;
        color: #6b7280;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .info-box {
        padding: 14px 18px;
        border-radius: 8px;
        background-color: #eef6ff;
        border: 1px solid #cfe3ff;
        margin-bottom: 18px;
    }

    .tir-box {
        padding: 14px 18px;
        border-radius: 8px;
        background-color: #fff4e5;
        border: 1px solid #ffd18a;
        margin-bottom: 18px;
    }

    .normal-box {
        padding: 14px 18px;
        border-radius: 8px;
        background-color: #f5f5f5;
        border: 1px solid #dddddd;
        margin-bottom: 18px;
    }

    [data-testid="stMetricValue"] {
        font-size: 28px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">Silicon Ray Optics Simulator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Live ray tracing through a plane parallel silicon slab. '
    'All optical geometry updates immediately when a control changes.'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# PRESETS
# ============================================================

st.sidebar.markdown("## Simulation")

preset = st.sidebar.radio(
    "Sample preset",
    ["Small sample", "Large sample", "Custom"],
    index=0
)

# ------------------------------------------------------------
# Preset definitions
# ------------------------------------------------------------

PRESETS = {
    "Small sample": {
        "thickness": 29.7,
        "diameter": 42.0,
        "incidence": 45.0
    },
    "Large sample": {
        "thickness": 180.0,
        "diameter": 450.0,
        "incidence": 45.0
    }
}

# ============================================================
# SESSION STATE
# ============================================================

if "thickness" not in st.session_state:
    st.session_state.thickness = 29.7

if "diameter" not in st.session_state:
    st.session_state.diameter = 42.0

if "incidence" not in st.session_state:
    st.session_state.incidence = 45.0

if "n_si" not in st.session_state:
    st.session_state.n_si = 3.48

if "n_air" not in st.session_state:
    st.session_state.n_air = 1.0003

if "wavelength" not in st.session_state:
    st.session_state.wavelength = 1550.0

# Apply preset whenever selected
if preset in PRESETS:
    st.session_state.thickness = PRESETS[preset]["thickness"]
    st.session_state.diameter = PRESETS[preset]["diameter"]
    st.session_state.incidence = PRESETS[preset]["incidence"]

# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("## Geometry")

thickness = st.sidebar.slider(
    "Silicon thickness, t (mm)",
    min_value=1.0,
    max_value=250.0,
    value=float(st.session_state.thickness),
    step=0.1,
    key="thickness_slider"
)

st.session_state.thickness = thickness

incidence = st.sidebar.slider(
    "External incidence angle, i (°)",
    min_value=0.0,
    max_value=89.9,
    value=float(st.session_state.incidence),
    step=0.1,
    key="incidence_slider"
)

st.session_state.incidence = incidence

diameter = st.sidebar.number_input(
    "Sample diameter (mm)",
    min_value=1.0,
    max_value=1000.0,
    value=float(st.session_state.diameter),
    step=1.0,
    key="diameter_input"
)

st.session_state.diameter = diameter

# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("## Optical properties")

n_si = st.sidebar.number_input(
    "Silicon refractive index, nSi",
    min_value=1.0,
    max_value=10.0,
    value=float(st.session_state.n_si),
    step=0.0001,
    format="%.4f",
    key="n_si_input"
)

st.session_state.n_si = n_si

n_air = st.sidebar.number_input(
    "Air refractive index, nair",
    min_value=1.0,
    max_value=2.0,
    value=float(st.session_state.n_air),
    step=0.0001,
    format="%.4f",
    key="n_air_input"
)

st.session_state.n_air = n_air

wavelength = st.sidebar.number_input(
    "Wavelength (nm)",
    min_value=200.0,
    max_value=5000.0,
    value=float(st.session_state.wavelength),
    step=1.0,
    key="wavelength_input"
)

st.session_state.wavelength = wavelength

# ============================================================
# POLARISATION
# ============================================================

polarisation = st.sidebar.selectbox(
    "Polarisation for Fresnel values",
    ["Unpolarised", "s", "p"]
)

# ============================================================
# OPTICAL CALCULATIONS
# ============================================================

i_deg = incidence
i_rad = np.deg2rad(i_deg)

# Snell's law:
# n_air sin(i) = n_si sin(r)

sin_r = (n_air / n_si) * np.sin(i_rad)

# Numerical protection
sin_r = np.clip(sin_r, -1.0, 1.0)

r_rad = np.arcsin(sin_r)
r_deg = np.rad2deg(r_rad)

# Critical angle for silicon -> air
critical_ratio = n_air / n_si

if critical_ratio < 1:
    critical_rad = np.arcsin(critical_ratio)
    critical_deg = np.rad2deg(critical_rad)
else:
    critical_deg = 90.0
    critical_rad = np.pi / 2

# TIR is determined by the ANGLE INSIDE SILICON,
# not by the external angle in air.
tir = r_deg >= critical_deg

# ============================================================
# BEAM SEPARATION
# ============================================================

# Lateral displacement between the two reflection points
# at the front surface:
#
#     2 t tan(r)
#
# Perpendicular separation between the two parallel
# reflected beams:
#
#     G = 2 t tan(r) cos(i)
#
# This is the perpendicular distance between the
# front reflected beam and the back reflected beam.

beam_gap = 2.0 * thickness * np.tan(r_rad) * np.cos(i_rad)

# ============================================================
# FRESNEL COEFFICIENTS
# ============================================================

cos_i = np.cos(i_rad)
cos_r = np.cos(r_rad)

# Air -> silicon amplitude coefficients
rs = (n_air * cos_i - n_si * cos_r) / (
    n_air * cos_i + n_si * cos_r
)

rp = (n_si * cos_i - n_air * cos_r) / (
    n_si * cos_i + n_air * cos_r
)

ts = (2 * n_air * cos_i) / (
    n_air * cos_i + n_si * cos_r
)

tp = (2 * n_air * cos_i) / (
    n_si * cos_i + n_air * cos_r
)

R_s = rs ** 2
R_p = rp ** 2

# Power transmission coefficients
T_s = (
    (n_si * cos_r) /
    (n_air * cos_i)
) * ts ** 2

T_p = (
    (n_si * cos_r) /
    (n_air * cos_i)
) * tp ** 2

if polarisation == "s":
    R_front = R_s
    T_front = T_s

elif polarisation == "p":
    R_front = R_p
    T_front = T_p

else:
    R_front = 0.5 * (R_s + R_p)
    T_front = 0.5 * (T_s + T_p)

# ============================================================
# STATUS MESSAGE
# ============================================================

if tir:

    st.markdown(
        f"""
        <div class="tir-box">
        <b>🔴 Total internal reflection</b><br>
        The ray inside silicon has an incidence angle of
        <b>{r_deg:.2f}°</b>, which is greater than the
        silicon → air critical angle of <b>{critical_deg:.2f}°</b>.
        Therefore, no transmitted ray leaves the back surface.
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        f"""
        <div class="info-box">
        <b>🟢 Transmission through the back silicon → air surface</b><br>
        The ray inside silicon reaches the back surface at
        <b>{r_deg:.2f}°</b>. The critical angle is
        <b>{critical_deg:.2f}°</b>, so transmission through the
        back surface occurs.
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# LIVE OPTICAL QUANTITIES
# ============================================================

st.markdown(
    '<div class="section-title">Live optical geometry</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "External angle, i",
        f"{i_deg:.2f}°"
    )

with c2:
    st.metric(
        "Internal angle, r",
        f"{r_deg:.2f}°"
    )

with c3:
    st.metric(
        "Critical angle, θc",
        f"{critical_deg:.2f}°"
    )

with c4:
    st.metric(
        "Perpendicular beam gap, G",
        f"{beam_gap:.2f} mm"
    )

# ============================================================
# OPTICAL DIAGRAM
# ============================================================

# The slab is centred around x = 0.
#
# Front surface: y = 0
# Back surface:  y = -t
#
# Incident ray comes from above-left.
#
# Front reflected ray goes upwards-right.
#
# Refracted ray travels downwards-right.
#
# At the back surface it reflects upwards-right.
#
# It then exits the front surface as the
# "back reflected beam".
#
# The two reflected beams are parallel.

half_t = thickness / 2.0

# Ray lengths for visualisation
air_ray = max(thickness * 0.8, 20.0)
internal_ray = thickness
output_ray = max(thickness * 0.8, 20.0)

# Incident ray starts above the front surface.
incident_start_x = -air_ray * np.sin(i_rad)
incident_start_y = air_ray * np.cos(i_rad)

# Front reflection
front_reflected_end_x = air_ray * np.sin(i_rad)
front_reflected_end_y = air_ray * np.cos(i_rad)

# Internal refraction
internal_dx = thickness * np.tan(r_rad)

# Back surface intersection
back_x = internal_dx
back_y = -thickness

# Internal reflection returns to front surface
front_second_x = 2.0 * internal_dx
front_second_y = 0.0

# Back reflected beam after leaving front surface
back_reflected_end_x = (
    front_second_x + output_ray * np.sin(i_rad)
)

back_reflected_end_y = (
    output_ray * np.cos(i_rad)
)

# ============================================================
# FIGURE
# ============================================================

fig = go.Figure()

# ------------------------------------------------------------
# Silicon slab
# ------------------------------------------------------------

slab_x = [
    -diameter / 2,
    diameter / 2,
    diameter / 2,
    -diameter / 2,
    -diameter / 2
]

slab_y = [
    0,
    0,
    -thickness,
    -thickness,
    0
]

fig.add_trace(
    go.Scatter(
        x=slab_x,
        y=slab_y,
        mode="lines",
        line=dict(width=3),
        fill="toself",
        fillcolor="rgba(100,150,220,0.15)",
        name="Silicon slab",
        hoverinfo="skip"
    )
)

# ------------------------------------------------------------
# Front surface
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter(
        x=[-diameter / 2, diameter / 2],
        y=[0, 0],
        mode="lines",
        line=dict(width=4),
        name="Front surface"
    )
)

# ------------------------------------------------------------
# Back surface
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter(
        x=[-diameter / 2, diameter / 2],
        y=[-thickness, -thickness],
        mode="lines",
        line=dict(width=4),
        name="Back surface"
    )
)

# ============================================================
# NORMALS
# ============================================================

normal_length = max(thickness * 0.20, 10.0)

# Front normal
fig.add_trace(
    go.Scatter(
        x=[0, 0],
        y=[-normal_length, normal_length],
        mode="lines",
        line=dict(
            width=2,
            dash="dash"
        ),
        name="Front normal"
    )
)

# Back normal
fig.add_trace(
    go.Scatter(
        x=[back_x, back_x],
        y=[
            -thickness - normal_length,
            -thickness + normal_length
        ],
        mode="lines",
        line=dict(
            width=2,
            dash="dash"
        ),
        name="Back normal"
    )
)

# ============================================================
# INCIDENT RAY WITH ARROW
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[incident_start_x, 0],
        y=[incident_start_y, 0],
        mode="lines+markers",
        line=dict(width=4),
        marker=dict(
            size=[0, 9],
            symbol=["circle", "arrow"]
        ),
        name="Incident ray"
    )
)

# Add explicit arrow annotation for incident direction
fig.add_annotation(
    x=0,
    y=0,
    ax=incident_start_x,
    ay=incident_start_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.2,
    arrowwidth=2
)

# ============================================================
# FRONT REFLECTED BEAM
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[0, front_reflected_end_x],
        y=[0, front_reflected_end_y],
        mode="lines",
        line=dict(width=4),
        name="Front reflected beam"
    )
)

fig.add_annotation(
    x=front_reflected_end_x,
    y=front_reflected_end_y,
    ax=0,
    ay=0,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.2,
    arrowwidth=2
)

# ============================================================
# REFRACTED RAY INSIDE SILICON
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[0, back_x],
        y=[0, back_y],
        mode="lines",
        line=dict(width=4),
        name="Refracted ray inside silicon"
    )
)

# ============================================================
# INTERNAL REFLECTION
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[back_x, front_second_x],
        y=[back_y, front_second_y],
        mode="lines",
        line=dict(width=4),
        name="Internal reflection from back surface"
    )
)

# Arrow showing internal reflected direction
fig.add_annotation(
    x=front_second_x,
    y=front_second_y,
    ax=back_x,
    ay=back_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.1,
    arrowwidth=2
)

# ============================================================
# BACK REFLECTED BEAM
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[front_second_x, back_reflected_end_x],
        y=[front_second_y, back_reflected_end_y],
        mode="lines",
        line=dict(width=4),
        name="Back reflected beam"
    )
)

fig.add_annotation(
    x=back_reflected_end_x,
    y=back_reflected_end_y,
    ax=front_second_x,
    ay=front_second_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.2,
    arrowwidth=2
)

# ============================================================
# BACK TRANSMITTED BEAM
# ============================================================

if not tir:

    # At a parallel interface the transmitted ray exits
    # at the same angle to the normal as the original
    # incident ray, but on the other side of the slab.

    transmitted_length = output_ray

    back_transmitted_end_x = (
        back_x + transmitted_length * np.sin(i_rad)
    )

    back_transmitted_end_y = (
        -thickness - transmitted_length * np.cos(i_rad)
    )

    fig.add_trace(
        go.Scatter(
            x=[back_x, back_transmitted_end_x],
            y=[back_y, back_transmitted_end_y],
            mode="lines",
            line=dict(width=4),
            name="Back transmitted beam"
        )
    )

    fig.add_annotation(
        x=back_transmitted_end_x,
        y=back_transmitted_end_y,
        ax=back_x,
        ay=back_y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.2,
        arrowwidth=2
    )

# ============================================================
# BEAM GAP
# ============================================================

# The beam gap is measured perpendicular to the two
# parallel reflected beams.
#
# Do NOT draw a horizontal dotted line here because that
# would not be perpendicular to the reflected beams.

# Unit vector perpendicular to reflected beam
perp_x = -np.cos(i_rad)
perp_y = np.sin(i_rad)

gap_start_x = 0.0
gap_start_y = 0.0

gap_end_x = (
    gap_start_x + beam_gap * perp_x
)

gap_end_y = (
    gap_start_y + beam_gap * perp_y
)

# Only draw the gap indicator if the gap is visually useful
if beam_gap > 0.01:

    fig.add_trace(
        go.Scatter(
            x=[gap_start_x, gap_end_x],
            y=[gap_start_y, gap_end_y],
            mode="lines",
            line=dict(
                width=2,
                dash="dot"
            ),
            name="Perpendicular beam gap"
        )
    )

    fig.add_annotation(
        x=gap_end_x,
        y=gap_end_y,
        ax=gap_start_x,
        ay=gap_start_y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.0,
        arrowwidth=1.5
    )

    fig.add_annotation(
        x=(gap_start_x + gap_end_x) / 2,
        y=(gap_start_y + gap_end_y) / 2,
        text=f"G = {beam_gap:.2f} mm",
        showarrow=False,
        font=dict(size=13)
    )

# ============================================================
# ANGLE LABELS
# ============================================================

fig.add_annotation(
    x=-0.8 * np.sin(i_rad),
    y=0.8 * np.cos(i_rad),
    text=f"i = {i_deg:.2f}°",
    showarrow=False,
    font=dict(size=13)
)

fig.add_annotation(
    x=0.45 * internal_dx,
    y=-0.45 * thickness,
    text=f"r = {r_deg:.2f}°",
    showarrow=False,
    font=dict(size=13)
)

# ============================================================
# MATERIAL LABELS
# ============================================================

fig.add_annotation(
    x=-diameter * 0.35,
    y=-thickness * 0.25,
    text="<b>SILICON</b>",
    showarrow=False,
    font=dict(size=13)
)

fig.add_annotation(
    x=-diameter * 0.35,
    y=thickness * 0.12,
    text="<b>AIR</b>",
    showarrow=False,
    font=dict(size=13)
)

# ============================================================
# NORMAL LABELS
# ============================================================

fig.add_annotation(
    x=0,
    y=normal_length * 0.65,
    text="Normal",
    showarrow=False,
    font=dict(size=12)
)

fig.add_annotation(
    x=back_x,
    y=-thickness + normal_length * 0.65,
    text="Normal",
    showarrow=False,
    font=dict(size=12)
)

# ============================================================
# FIGURE LAYOUT
# ============================================================

# Determine suitable display limits
all_x = [
    incident_start_x,
    front_reflected_end_x,
    back_reflected_end_x,
    back_x,
    front_second_x
]

all_y = [
    incident_start_y,
    front_reflected_end_y,
    back_reflected_end_y,
    0,
    -thickness
]

if not tir:
    all_x.append(back_transmitted_end_x)
    all_y.append(back_transmitted_end_y)

x_min = min(all_x)
x_max = max(all_x)
y_min = min(all_y)
y_max = max(all_y)

x_range = x_max - x_min
y_range = y_max - y_min

x_padding = max(x_range * 0.20, thickness * 0.25)
y_padding = max(y_range * 0.20, thickness * 0.20)

fig.update_layout(
    height=700,
    margin=dict(
        l=20,
        r=20,
        t=80,
        b=20
    ),
    xaxis=dict(
        title="Distance parallel to surface (mm)",
        range=[
            x_min - x_padding,
            x_max + x_padding
        ],
        zeroline=False,
        showgrid=True
    ),
    yaxis=dict(
        title="Distance normal to surface (mm)",
        range=[
            y_min - y_padding,
            y_max + y_padding
        ],
        zeroline=False,
        showgrid=True,
        scaleanchor="x",
        scaleratio=1
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    ),
    hovermode="closest"
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displaylogo": False,
        "responsive": True
    }
)

# ============================================================
# OPTICAL INFORMATION
# ============================================================

st.markdown(
    '<div class="section-title">Optical conditions</div>',
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### Snell's law")
    st.latex(
        r"""
        n_{\rm air}\sin i =
        n_{\rm Si}\sin r
        """
    )

    st.write(
        f"Internal angle: **{r_deg:.2f}°**"
    )

with c2:
    st.markdown("### Critical angle")
    st.latex(
        r"""
        \theta_c =
        \sin^{-1}
        \left(
        \frac{n_{\rm air}}{n_{\rm Si}}
        \right)
        """
    )

    st.write(
        f"Critical angle: **{critical_deg:.2f}°**"
    )

with c3:
    st.markdown("### Beam separation")
    st.latex(
        r"""
        G =
        2t\tan(r)\cos(i)
        """
    )

    st.write(
        f"Perpendicular separation: **{beam_gap:.2f} mm**"
    )

# ============================================================
# TIR EXPLANATION
# ============================================================

st.markdown("---")

if tir:

    st.markdown(
        f"""
        <div class="tir-box">
        <b>Total internal reflection occurs at the back surface.</b><br><br>
        The relevant angle for determining TIR is the angle of the ray
        <b>inside the silicon</b> measured from the normal.
        Here:
        <br><br>
        Internal incidence angle = <b>{r_deg:.2f}°</b><br>
        Critical angle = <b>{critical_deg:.2f}°</b>
        <br><br>
        Since <b>{r_deg:.2f}° &gt; {critical_deg:.2f}°</b>,
        the silicon → air interface undergoes total internal reflection.
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        f"""
        <div class="normal-box">
        <b>Transmission occurs at the back surface.</b><br><br>
        The relevant comparison is between the internal incidence angle
        and the critical angle:
        <br><br>
        Internal incidence angle = <b>{r_deg:.2f}°</b><br>
        Critical angle = <b>{critical_deg:.2f}°</b>
        <br><br>
        Since <b>{r_deg:.2f}° &lt; {critical_deg:.2f}°</b>,
        the ray can transmit from silicon into air.
        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# INTERFACE REFLECTIVITY
# ============================================================

st.markdown(
    '<div class="section-title">Interface optics</div>',
    unsafe_allow_html=True
)

c1, c2 = st.columns(2)

with c1:
    st.metric(
        "Front surface reflectance",
        f"{R_front * 100:.2f}%"
    )

with c2:
    st.metric(
        "Front surface transmission",
        f"{T_front * 100:.2f}%"
    )

st.caption(
    f"λ = {wavelength:.0f} nm | "
    f"nSi = {n_si:.4f} | "
    f"nair = {n_air:.4f} | "
    f"Polarisation = {polarisation}"
)

# ============================================================
# IMPORTANT NOTE
# ============================================================

st.markdown(
    """
    **Geometry convention:** The beam gap shown in the diagram is the
    perpendicular distance between the two parallel reflected beams.
    It is not the internal lateral displacement of the refracted ray.
    """
)
