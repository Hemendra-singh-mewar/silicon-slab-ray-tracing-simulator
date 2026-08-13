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
    initial_sidebar_state="expanded",
)


# ============================================================
# PAGE STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .subtitle {
        font-size: 16px;
        color: #6b7280;
        margin-bottom: 24px;
    }

    .section-title {
        font-size: 26px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .status-normal {
        padding: 14px 18px;
        border-radius: 9px;
        background-color: #eef6ff;
        border: 1px solid #c9e0ff;
        margin-bottom: 18px;
    }

    .status-tir {
        padding: 14px 18px;
        border-radius: 9px;
        background-color: #fff4e5;
        border: 1px solid #ffd18a;
        margin-bottom: 18px;
    }

    .physics-note {
        padding: 14px 18px;
        border-radius: 9px;
        background-color: #f7f7f7;
        border: 1px solid #dddddd;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">Silicon Ray Optics Simulator</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Live ray tracing through a plane parallel silicon slab. '
    'The complete optical geometry updates immediately when a control changes.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# PRESETS
# ============================================================

PRESETS = {
    "Small sample": {
        "thickness": 29.7,
        "diameter": 42.0,
        "incidence": 45.0,
    },
    "Large sample": {
        "thickness": 100.0,
        "diameter": 100.0,
        "incidence": 45.0,
    },
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

if "previous_preset" not in st.session_state:
    st.session_state.previous_preset = "Small sample"


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## Simulation")

preset = st.sidebar.radio(
    "Sample preset",
    ["Small sample", "Large sample", "Custom"],
    index=0,
)


# Apply preset only when the preset itself changes.
# This means the user can subsequently move the sliders
# without the values being reset.

if preset != st.session_state.previous_preset:

    if preset in PRESETS:

        st.session_state.thickness = PRESETS[preset]["thickness"]
        st.session_state.diameter = PRESETS[preset]["diameter"]
        st.session_state.incidence = PRESETS[preset]["incidence"]

    st.session_state.previous_preset = preset


# ============================================================
# GEOMETRY CONTROLS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("## Geometry")

thickness = st.sidebar.slider(
    "Silicon thickness, t (mm)",
    min_value=1.0,
    max_value=250.0,
    value=float(st.session_state.thickness),
    step=0.1,
)

st.session_state.thickness = thickness


incidence = st.sidebar.slider(
    "External incidence angle, i (°)",
    min_value=0.0,
    max_value=89.9,
    value=float(st.session_state.incidence),
    step=0.1,
)

st.session_state.incidence = incidence


diameter = st.sidebar.number_input(
    "Sample diameter (mm)",
    min_value=1.0,
    max_value=1000.0,
    value=float(st.session_state.diameter),
    step=1.0,
)

st.session_state.diameter = diameter


# ============================================================
# OPTICAL PROPERTY CONTROLS
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
)

st.session_state.n_si = n_si


n_air = st.sidebar.number_input(
    "Air refractive index, nair",
    min_value=1.0,
    max_value=2.0,
    value=float(st.session_state.n_air),
    step=0.0001,
    format="%.4f",
)

st.session_state.n_air = n_air


wavelength = st.sidebar.number_input(
    "Wavelength (nm)",
    min_value=200.0,
    max_value=5000.0,
    value=float(st.session_state.wavelength),
    step=1.0,
)

st.session_state.wavelength = wavelength


polarisation = st.sidebar.selectbox(
    "Polarisation for Fresnel values",
    ["Unpolarised", "s", "p"],
)


# ============================================================
# BASIC ANGLES
# ============================================================

i_deg = incidence
i_rad = np.deg2rad(i_deg)


# ============================================================
# SNELL'S LAW
# ============================================================

sin_r = (n_air / n_si) * np.sin(i_rad)

# Numerical protection
sin_r = np.clip(sin_r, -1.0, 1.0)

r_rad = np.arcsin(sin_r)
r_deg = np.rad2deg(r_rad)


# ============================================================
# CRITICAL ANGLE
# ============================================================

if n_si > n_air:

    critical_rad = np.arcsin(n_air / n_si)
    critical_deg = np.rad2deg(critical_rad)

else:

    critical_rad = np.pi / 2
    critical_deg = 90.0


# ============================================================
# TIR CONDITION
#
# IMPORTANT:
#
# TIR at the silicon -> air interface depends on the
# INTERNAL incidence angle at the back surface.
#
# Therefore:
#
#       r > theta_c
#
# NOT:
#
#       i > theta_c
# ============================================================

tir = r_deg >= critical_deg


# ============================================================
# RAY GEOMETRY
# ============================================================

# Coordinate system:
#
#                AIR
#
#              y > 0
#
# -------------------------------  front surface
#                 |
#                 | normal
#                 |
#                SILICON
#                 |
#                 |
# -------------------------------  back surface
#
#              y < 0
#
#
# Front reflection point:
#
#       P1 = (0, 0)
#
# Refracted ray reaches back surface at:
#
#       x1 = t tan(r)
#
# After internal reflection it reaches front surface at:
#
#       x2 = 2 t tan(r)
#
# This is the origin of the second external reflected beam.

x1 = thickness * np.tan(r_rad)

x2 = 2.0 * x1


# ============================================================
# PERPENDICULAR BEAM GAP
# ============================================================

# The two reflected beams are parallel.
#
# Direction of the reflected beams:
#
#       u = (sin(i), cos(i))
#
# A perpendicular unit vector is:
#
#       n = (cos(i), -sin(i))
#
# The perpendicular separation is:
#
#       G = 2 t tan(r) cos(i)

beam_gap = abs(
    2.0
    * thickness
    * np.tan(r_rad)
    * np.cos(i_rad)
)


# ============================================================
# FRESNEL COEFFICIENTS
# ============================================================

cos_i = np.cos(i_rad)
cos_r = np.cos(r_rad)


# s polarisation

rs = (
    (n_air * cos_i - n_si * cos_r)
    /
    (n_air * cos_i + n_si * cos_r)
)

ts = (
    2.0 * n_air * cos_i
    /
    (n_air * cos_i + n_si * cos_r)
)


# p polarisation

rp = (
    (n_si * cos_i - n_air * cos_r)
    /
    (n_si * cos_i + n_air * cos_r)
)

tp = (
    2.0 * n_air * cos_i
    /
    (n_si * cos_i + n_air * cos_r)
)


R_s = rs ** 2
R_p = rp ** 2

T_s = (
    (n_si * cos_r)
    /
    (n_air * cos_i)
) * ts ** 2

T_p = (
    (n_si * cos_r)
    /
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
# STATUS
# ============================================================

if tir:

    st.markdown(
        f"""
        <div class="status-tir">

        <b>🔴 Total internal reflection at the back surface</b><br><br>

        The ray inside the silicon reaches the back surface at

        <b>{r_deg:.2f}°</b>

        to the normal.

        The silicon → air critical angle is

        <b>{critical_deg:.2f}°</b>.

        Therefore

        <b>{r_deg:.2f}° &gt; {critical_deg:.2f}°</b>

        and the ray undergoes total internal reflection.

        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        f"""
        <div class="status-normal">

        <b>🟢 Transmission through the back silicon → air surface</b><br><br>

        The ray inside the silicon reaches the back surface at

        <b>{r_deg:.2f}°</b>

        to the normal.

        The silicon → air critical angle is

        <b>{critical_deg:.2f}°</b>.

        Therefore

        <b>{r_deg:.2f}° &lt; {critical_deg:.2f}°</b>

        and transmission through the back surface occurs.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LIVE QUANTITIES
# ============================================================

st.markdown(
    '<div class="section-title">Live optical geometry</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "External angle, i",
        f"{i_deg:.2f}°",
    )

with c2:
    st.metric(
        "Internal angle, r",
        f"{r_deg:.2f}°",
    )

with c3:
    st.metric(
        "Critical angle, θc",
        f"{critical_deg:.2f}°",
    )

with c4:
    st.metric(
        "Perpendicular beam gap, G",
        f"{beam_gap:.2f} mm",
    )


# ============================================================
# PLOT GEOMETRY
# ============================================================

# ------------------------------------------------------------
# Incident ray
# ------------------------------------------------------------

air_length = max(
    0.8 * thickness,
    20.0,
)

incident_start_x = -air_length * np.sin(i_rad)
incident_start_y = air_length * np.cos(i_rad)


# ------------------------------------------------------------
# Front reflected beam
# ------------------------------------------------------------

front_reflected_length = max(
    0.9 * thickness,
    20.0,
)

front_reflected_end_x = (
    front_reflected_length * np.sin(i_rad)
)

front_reflected_end_y = (
    front_reflected_length * np.cos(i_rad)
)


# ------------------------------------------------------------
# Refracted ray inside silicon
# ------------------------------------------------------------

back_x = x1
back_y = -thickness


# ------------------------------------------------------------
# Internal reflection
# ------------------------------------------------------------

second_front_x = x2
second_front_y = 0.0


# ------------------------------------------------------------
# Second external reflected beam
# ------------------------------------------------------------

back_reflected_length = max(
    0.9 * thickness,
    20.0,
)

back_reflected_end_x = (
    second_front_x
    + back_reflected_length * np.sin(i_rad)
)

back_reflected_end_y = (
    back_reflected_length * np.cos(i_rad)
)


# ------------------------------------------------------------
# Back transmitted beam
# ------------------------------------------------------------

if not tir:

    transmitted_length = max(
        0.8 * thickness,
        20.0,
    )

    back_transmitted_end_x = (
        back_x
        + transmitted_length * np.sin(i_rad)
    )

    back_transmitted_end_y = (
        -thickness
        - transmitted_length * np.cos(i_rad)
    )


# ============================================================
# PLOTLY FIGURE
# ============================================================

fig = go.Figure()


# ============================================================
# SILICON SLAB
# ============================================================

slab_left = -diameter / 2.0
slab_right = diameter / 2.0

fig.add_trace(
    go.Scatter(
        x=[
            slab_left,
            slab_right,
            slab_right,
            slab_left,
            slab_left,
        ],
        y=[
            0,
            0,
            -thickness,
            -thickness,
            0,
        ],
        mode="lines",
        fill="toself",
        fillcolor="rgba(80,140,210,0.12)",
        line=dict(width=2),
        name="Silicon",
        hoverinfo="skip",
    )
)


# ============================================================
# FRONT SURFACE
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[slab_left, slab_right],
        y=[0, 0],
        mode="lines",
        line=dict(width=4),
        name="Front surface",
        hoverinfo="skip",
    )
)


# ============================================================
# BACK SURFACE
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[slab_left, slab_right],
        y=[-thickness, -thickness],
        mode="lines",
        line=dict(width=4),
        name="Back surface",
        hoverinfo="skip",
    )
)


# ============================================================
# FRONT NORMAL
# ============================================================

normal_length = max(
    0.25 * thickness,
    10.0,
)

fig.add_trace(
    go.Scatter(
        x=[0, 0],
        y=[
            -normal_length,
            normal_length,
        ],
        mode="lines",
        line=dict(
            width=2,
            dash="dash",
        ),
        name="Front normal",
        hoverinfo="skip",
    )
)


# ============================================================
# BACK NORMAL
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[back_x, back_x],
        y=[
            -thickness - normal_length,
            -thickness + normal_length,
        ],
        mode="lines",
        line=dict(
            width=2,
            dash="dash",
        ),
        name="Back normal",
        hoverinfo="skip",
    )
)


# ============================================================
# INCIDENT RAY
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            incident_start_x,
            0,
        ],
        y=[
            incident_start_y,
            0,
        ],
        mode="lines",
        line=dict(width=4),
        name="Incident ray",
        hoverinfo="skip",
    )
)

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
    arrowwidth=2.5,
)


# ============================================================
# FRONT REFLECTED BEAM
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            0,
            front_reflected_end_x,
        ],
        y=[
            0,
            front_reflected_end_y,
        ],
        mode="lines",
        line=dict(width=4),
        name="Front reflected beam",
        hoverinfo="skip",
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
    arrowsize=1.1,
    arrowwidth=2.2,
)


# ============================================================
# REFRACTED RAY INSIDE SILICON
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            0,
            back_x,
        ],
        y=[
            0,
            back_y,
        ],
        mode="lines",
        line=dict(width=4),
        name="Refracted ray inside silicon",
        hoverinfo="skip",
    )
)


# ============================================================
# INTERNAL REFLECTION FROM BACK SURFACE
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            back_x,
            second_front_x,
        ],
        y=[
            back_y,
            0,
        ],
        mode="lines",
        line=dict(width=4),
        name="Internal reflection from back surface",
        hoverinfo="skip",
    )
)

fig.add_annotation(
    x=second_front_x,
    y=0,
    ax=back_x,
    ay=back_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.1,
    arrowwidth=2.2,
)


# ============================================================
# SECOND REFLECTED BEAM
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            second_front_x,
            back_reflected_end_x,
        ],
        y=[
            0,
            back_reflected_end_y,
        ],
        mode="lines",
        line=dict(width=4),
        name="Back reflected beam",
        hoverinfo="skip",
    )
)

fig.add_annotation(
    x=back_reflected_end_x,
    y=back_reflected_end_y,
    ax=second_front_x,
    ay=0,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.1,
    arrowwidth=2.2,
)


# ============================================================
# BACK TRANSMITTED BEAM
# ============================================================

if not tir:

    fig.add_trace(
        go.Scatter(
            x=[
                back_x,
                back_transmitted_end_x,
            ],
            y=[
                back_y,
                back_transmitted_end_y,
            ],
            mode="lines",
            line=dict(width=4),
            name="Back transmitted beam",
            hoverinfo="skip",
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
        arrowsize=1.1,
        arrowwidth=2.2,
    )


# ============================================================
# PERPENDICULAR BEAM GAP
#
# IMPORTANT:
#
# The shortest perpendicular between the two infinite
# parallel reflected beam lines would intersect the second
# line below the front surface if drawn from the first
# reflection point.
#
# Therefore we choose a point further along the first
# reflected beam. The perpendicular is then drawn between
# the actual two visible reflected rays.
# ============================================================

u_x = np.sin(i_rad)
u_y = np.cos(i_rad)

normal_x = np.cos(i_rad)
normal_y = -np.sin(i_rad)


# Choose a point along the first reflected beam far enough
# from the surface that the perpendicular endpoint also
# lies on the visible second reflected beam.

minimum_s = x2 * np.sin(i_rad) + 0.15 * air_length

gap_ray_position = max(
    0.45 * front_reflected_length,
    minimum_s,
)


# Point A on first reflected beam
A_x = gap_ray_position * u_x
A_y = gap_ray_position * u_y


# Point B on second reflected beam
B_x = A_x + beam_gap * normal_x
B_y = A_y + beam_gap * normal_y


# ------------------------------------------------------------
# Gap line
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter(
        x=[A_x, B_x],
        y=[A_y, B_y],
        mode="lines",
        line=dict(
            width=2.5,
            dash="dot",
        ),
        name="Perpendicular beam gap",
        hoverinfo="skip",
    )
)


# ------------------------------------------------------------
# Gap arrows at both ends
# ------------------------------------------------------------

fig.add_annotation(
    x=A_x,
    y=A_y,
    ax=B_x,
    ay=B_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
)

fig.add_annotation(
    x=B_x,
    y=B_y,
    ax=A_x,
    ay=A_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
)


# ============================================================
# GAP LABEL
# ============================================================

fig.add_annotation(
    x=(A_x + B_x) / 2,
    y=(A_y + B_y) / 2,
    text=f"<b>G = {beam_gap:.2f} mm</b>",
    showarrow=False,
    font=dict(size=13),
    bgcolor="rgba(255,255,255,0.85)",
)


# ============================================================
# ANGLE LABELS
# ============================================================

fig.add_annotation(
    x=-0.55 * np.sin(i_rad) * air_length,
    y=0.55 * np.cos(i_rad) * air_length,
    text=f"i = {i_deg:.2f}°",
    showarrow=False,
    font=dict(size=13),
)


fig.add_annotation(
    x=0.5 * x1,
    y=-0.5 * thickness,
    text=f"r = {r_deg:.2f}°",
    showarrow=False,
    font=dict(size=13),
)


# ============================================================
# MATERIAL LABELS
# ============================================================

fig.add_annotation(
    x=slab_left + 0.15 * diameter,
    y=-0.18 * thickness,
    text="<b>SILICON</b>",
    showarrow=False,
    font=dict(size=13),
)


fig.add_annotation(
    x=slab_left + 0.15 * diameter,
    y=0.12 * thickness,
    text="<b>AIR</b>",
    showarrow=False,
    font=dict(size=13),
)


# ============================================================
# NORMAL LABELS
# ============================================================

fig.add_annotation(
    x=0,
    y=0.70 * normal_length,
    text="Normal",
    showarrow=False,
    font=dict(size=12),
)


fig.add_annotation(
    x=back_x,
    y=-thickness + 0.70 * normal_length,
    text="Normal",
    showarrow=False,
    font=dict(size=12),
)


# ============================================================
# RAY LABELS
# ============================================================

fig.add_annotation(
    x=0.65 * incident_start_x,
    y=0.65 * incident_start_y,
    text="Incident ray",
    showarrow=False,
    font=dict(size=12),
)


fig.add_annotation(
    x=0.65 * front_reflected_end_x,
    y=0.65 * front_reflected_end_y,
    text="Front reflected beam",
    showarrow=False,
    font=dict(size=12),
)


fig.add_annotation(
    x=0.5 * x1,
    y=-0.75 * thickness,
    text="Refracted ray",
    showarrow=False,
    font=dict(size=12),
)


fig.add_annotation(
    x=second_front_x + 0.55 * (
        back_reflected_end_x - second_front_x
    ),
    y=0.55 * back_reflected_end_y,
    text="Back reflected beam",
    showarrow=False,
    font=dict(size=12),
)


# ============================================================
# AXIS LIMITS
# ============================================================

x_values = [
    incident_start_x,
    front_reflected_end_x,
    back_reflected_end_x,
    back_x,
    second_front_x,
    A_x,
    B_x,
]

y_values = [
    incident_start_y,
    front_reflected_end_y,
    back_reflected_end_y,
    back_y,
    A_y,
    B_y,
]


if not tir:

    x_values.append(back_transmitted_end_x)
    y_values.append(back_transmitted_end_y)


x_min = min(x_values)
x_max = max(x_values)

y_min = min(y_values)
y_max = max(y_values)


x_span = max(x_max - x_min, 1.0)
y_span = max(y_max - y_min, 1.0)


x_padding = 0.15 * x_span
y_padding = 0.15 * y_span


# ============================================================
# FINAL FIGURE LAYOUT
# ============================================================

fig.update_layout(
    height=760,

    margin=dict(
        l=30,
        r=30,
        t=100,
        b=30,
    ),

    xaxis=dict(
        title="Distance parallel to surface (mm)",
        range=[
            x_min - x_padding,
            x_max + x_padding,
        ],
        showgrid=True,
        zeroline=False,
    ),

    yaxis=dict(
        title="Distance normal to surface (mm)",
        range=[
            y_min - y_padding,
            y_max + y_padding,
        ],
        showgrid=True,
        zeroline=False,

        # Preserve physical angles.
        scaleanchor="x",
        scaleratio=1,
    ),

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),

    hovermode="closest",

    plot_bgcolor="white",

    showlegend=True,
)


# ============================================================
# DISPLAY DIAGRAM
# ============================================================

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displaylogo": False,
        "responsive": True,
    },
)


# ============================================================
# OPTICAL PHYSICS
# ============================================================

st.markdown(
    '<div class="section-title">Live optical quantities</div>',
    unsafe_allow_html=True,
)


col1, col2, col3 = st.columns(3)


with col1:

    st.markdown("### Snell's law")

    st.latex(
        r"""
        n_{\mathrm{air}}\sin i
        =
        n_{\mathrm{Si}}\sin r
        """
    )

    st.write(
        f"External incidence angle: **{i_deg:.2f}°**"
    )

    st.write(
        f"Internal angle: **{r_deg:.2f}°**"
    )


with col2:

    st.markdown("### Critical angle")

    st.latex(
        r"""
        \theta_c =
        \sin^{-1}
        \left(
        \frac{n_{\mathrm{air}}}
        {n_{\mathrm{Si}}}
        \right)
        """
    )

    st.write(
        f"Critical angle: **{critical_deg:.2f}°**"
    )

    if tir:

        st.write(
            f"Internal angle > critical angle"
        )

    else:

        st.write(
            f"Internal angle < critical angle"
        )


with col3:

    st.markdown("### Perpendicular beam gap")

    st.latex(
        r"""
        G =
        2t\tan(r)\cos(i)
        """
    )

    st.write(
        f"Beam separation: **{beam_gap:.2f} mm**"
    )


# ============================================================
# TIR EXPLANATION
# ============================================================

st.markdown(
    '<div class="section-title">Back surface condition</div>',
    unsafe_allow_html=True,
)


if tir:

    st.markdown(
        f"""
        <div class="status-tir">

        <b>Total internal reflection occurs at the silicon → air
        back surface.</b>

        <br><br>

        At the back surface the ray is travelling inside silicon
        and its incidence angle is measured from the back surface
        normal.

        <br><br>

        Internal incidence angle:

        <b>{r_deg:.2f}°</b>

        <br>

        Critical angle:

        <b>{critical_deg:.2f}°</b>

        <br><br>

        Therefore:

        <b>{r_deg:.2f}° &gt; {critical_deg:.2f}°</b>

        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        f"""
        <div class="physics-note">

        <b>Transmission occurs at the silicon → air back surface.</b>

        <br><br>

        At the back surface the relevant angle is the
        <b>internal incidence angle</b> inside silicon.

        <br><br>

        Internal incidence angle:

        <b>{r_deg:.2f}°</b>

        <br>

        Critical angle:

        <b>{critical_deg:.2f}°</b>

        <br><br>

        Therefore:

        <b>{r_deg:.2f}° &lt; {critical_deg:.2f}°</b>

        and the ray can transmit into air.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FRESNEL OPTICS
# ============================================================
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
    initial_sidebar_state="expanded",
)


# ============================================================
# PAGE STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .subtitle {
        font-size: 16px;
        color: #6b7280;
        margin-bottom: 24px;
    }

    .section-title {
        font-size: 26px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .status-normal {
        padding: 14px 18px;
        border-radius: 9px;
        background-color: #eef6ff;
        border: 1px solid #c9e0ff;
        margin-bottom: 18px;
    }

    .status-tir {
        padding: 14px 18px;
        border-radius: 9px;
        background-color: #fff4e5;
        border: 1px solid #ffd18a;
        margin-bottom: 18px;
    }

    .physics-note {
        padding: 14px 18px;
        border-radius: 9px;
        background-color: #f7f7f7;
        border: 1px solid #dddddd;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">Silicon Ray Optics Simulator</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Live ray tracing through a plane parallel silicon slab. '
    'The complete optical geometry updates immediately when a control changes.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# PRESETS
# ============================================================

PRESETS = {
    "Small sample": {
        "thickness": 29.7,
        "diameter": 42.0,
        "incidence": 45.0,
    },
    "Large sample": {
        "thickness": 180.0,
        "diameter": 450.0,
        "incidence": 45.0,
    },
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

if "previous_preset" not in st.session_state:
    st.session_state.previous_preset = "Small sample"


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## Simulation")

preset = st.sidebar.radio(
    "Sample preset",
    ["Small sample", "Large sample", "Custom"],
    index=0,
)


# Apply preset only when the preset itself changes.
# This means the user can subsequently move the sliders
# without the values being reset.

if preset != st.session_state.previous_preset:

    if preset in PRESETS:

        st.session_state.thickness = PRESETS[preset]["thickness"]
        st.session_state.diameter = PRESETS[preset]["diameter"]
        st.session_state.incidence = PRESETS[preset]["incidence"]

    st.session_state.previous_preset = preset


# ============================================================
# GEOMETRY CONTROLS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("## Geometry")

thickness = st.sidebar.slider(
    "Silicon thickness, t (mm)",
    min_value=1.0,
    max_value=250.0,
    value=float(st.session_state.thickness),
    step=0.1,
)

st.session_state.thickness = thickness


incidence = st.sidebar.slider(
    "External incidence angle, i (°)",
    min_value=0.0,
    max_value=89.9,
    value=float(st.session_state.incidence),
    step=0.1,
)

st.session_state.incidence = incidence


diameter = st.sidebar.number_input(
    "Sample diameter (mm)",
    min_value=1.0,
    max_value=1000.0,
    value=float(st.session_state.diameter),
    step=1.0,
)

st.session_state.diameter = diameter


# ============================================================
# OPTICAL PROPERTY CONTROLS
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
)

st.session_state.n_si = n_si


n_air = st.sidebar.number_input(
    "Air refractive index, nair",
    min_value=1.0,
    max_value=2.0,
    value=float(st.session_state.n_air),
    step=0.0001,
    format="%.4f",
)

st.session_state.n_air = n_air


wavelength = st.sidebar.number_input(
    "Wavelength (nm)",
    min_value=200.0,
    max_value=5000.0,
    value=float(st.session_state.wavelength),
    step=1.0,
)

st.session_state.wavelength = wavelength


polarisation = st.sidebar.selectbox(
    "Polarisation for Fresnel values",
    ["Unpolarised", "s", "p"],
)


# ============================================================
# BASIC ANGLES
# ============================================================

i_deg = incidence
i_rad = np.deg2rad(i_deg)


# ============================================================
# SNELL'S LAW
# ============================================================

sin_r = (n_air / n_si) * np.sin(i_rad)

# Numerical protection
sin_r = np.clip(sin_r, -1.0, 1.0)

r_rad = np.arcsin(sin_r)
r_deg = np.rad2deg(r_rad)


# ============================================================
# CRITICAL ANGLE
# ============================================================

if n_si > n_air:

    critical_rad = np.arcsin(n_air / n_si)
    critical_deg = np.rad2deg(critical_rad)

else:

    critical_rad = np.pi / 2
    critical_deg = 90.0


# ============================================================
# TIR CONDITION
#
# IMPORTANT:
#
# TIR at the silicon -> air interface depends on the
# INTERNAL incidence angle at the back surface.
#
# Therefore:
#
#       r > theta_c
#
# NOT:
#
#       i > theta_c
# ============================================================

tir = r_deg >= critical_deg


# ============================================================
# RAY GEOMETRY
# ============================================================

# Coordinate system:
#
#                AIR
#
#              y > 0
#
# -------------------------------  front surface
#                 |
#                 | normal
#                 |
#                SILICON
#                 |
#                 |
# -------------------------------  back surface
#
#              y < 0
#
#
# Front reflection point:
#
#       P1 = (0, 0)
#
# Refracted ray reaches back surface at:
#
#       x1 = t tan(r)
#
# After internal reflection it reaches front surface at:
#
#       x2 = 2 t tan(r)
#
# This is the origin of the second external reflected beam.

x1 = thickness * np.tan(r_rad)

x2 = 2.0 * x1


# ============================================================
# PERPENDICULAR BEAM GAP
# ============================================================

# The two reflected beams are parallel.
#
# Direction of the reflected beams:
#
#       u = (sin(i), cos(i))
#
# A perpendicular unit vector is:
#
#       n = (cos(i), -sin(i))
#
# The perpendicular separation is:
#
#       G = 2 t tan(r) cos(i)

beam_gap = abs(
    2.0
    * thickness
    * np.tan(r_rad)
    * np.cos(i_rad)
)


# ============================================================
# FRESNEL COEFFICIENTS
# ============================================================

cos_i = np.cos(i_rad)
cos_r = np.cos(r_rad)


# s polarisation

rs = (
    (n_air * cos_i - n_si * cos_r)
    /
    (n_air * cos_i + n_si * cos_r)
)

ts = (
    2.0 * n_air * cos_i
    /
    (n_air * cos_i + n_si * cos_r)
)


# p polarisation

rp = (
    (n_si * cos_i - n_air * cos_r)
    /
    (n_si * cos_i + n_air * cos_r)
)

tp = (
    2.0 * n_air * cos_i
    /
    (n_si * cos_i + n_air * cos_r)
)


R_s = rs ** 2
R_p = rp ** 2

T_s = (
    (n_si * cos_r)
    /
    (n_air * cos_i)
) * ts ** 2

T_p = (
    (n_si * cos_r)
    /
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
# STATUS
# ============================================================

if tir:

    st.markdown(
        f"""
        <div class="status-tir">

        <b>🔴 Total internal reflection at the back surface</b><br><br>

        The ray inside the silicon reaches the back surface at

        <b>{r_deg:.2f}°</b>

        to the normal.

        The silicon → air critical angle is

        <b>{critical_deg:.2f}°</b>.

        Therefore

        <b>{r_deg:.2f}° &gt; {critical_deg:.2f}°</b>

        and the ray undergoes total internal reflection.

        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        f"""
        <div class="status-normal">

        <b>🟢 Transmission through the back silicon → air surface</b><br><br>

        The ray inside the silicon reaches the back surface at

        <b>{r_deg:.2f}°</b>

        to the normal.

        The silicon → air critical angle is

        <b>{critical_deg:.2f}°</b>.

        Therefore

        <b>{r_deg:.2f}° &lt; {critical_deg:.2f}°</b>

        and transmission through the back surface occurs.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LIVE QUANTITIES
# ============================================================

st.markdown(
    '<div class="section-title">Live optical geometry</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "External angle, i",
        f"{i_deg:.2f}°",
    )

with c2:
    st.metric(
        "Internal angle, r",
        f"{r_deg:.2f}°",
    )

with c3:
    st.metric(
        "Critical angle, θc",
        f"{critical_deg:.2f}°",
    )

with c4:
    st.metric(
        "Perpendicular beam gap, G",
        f"{beam_gap:.2f} mm",
    )


# ============================================================
# PLOT GEOMETRY
# ============================================================

# ------------------------------------------------------------
# Incident ray
# ------------------------------------------------------------

air_length = max(
    0.8 * thickness,
    20.0,
)

incident_start_x = -air_length * np.sin(i_rad)
incident_start_y = air_length * np.cos(i_rad)


# ------------------------------------------------------------
# Front reflected beam
# ------------------------------------------------------------

front_reflected_length = max(
    0.9 * thickness,
    20.0,
)

front_reflected_end_x = (
    front_reflected_length * np.sin(i_rad)
)

front_reflected_end_y = (
    front_reflected_length * np.cos(i_rad)
)


# ------------------------------------------------------------
# Refracted ray inside silicon
# ------------------------------------------------------------

back_x = x1
back_y = -thickness


# ------------------------------------------------------------
# Internal reflection
# ------------------------------------------------------------

second_front_x = x2
second_front_y = 0.0


# ------------------------------------------------------------
# Second external reflected beam
# ------------------------------------------------------------

back_reflected_length = max(
    0.9 * thickness,
    20.0,
)

back_reflected_end_x = (
    second_front_x
    + back_reflected_length * np.sin(i_rad)
)

back_reflected_end_y = (
    back_reflected_length * np.cos(i_rad)
)


# ------------------------------------------------------------
# Back transmitted beam
# ------------------------------------------------------------

if not tir:

    transmitted_length = max(
        0.8 * thickness,
        20.0,
    )

    back_transmitted_end_x = (
        back_x
        + transmitted_length * np.sin(i_rad)
    )

    back_transmitted_end_y = (
        -thickness
        - transmitted_length * np.cos(i_rad)
    )


# ============================================================
# PLOTLY FIGURE
# ============================================================

fig = go.Figure()


# ============================================================
# SILICON SLAB
# ============================================================

slab_left = -diameter / 2.0
slab_right = diameter / 2.0

fig.add_trace(
    go.Scatter(
        x=[
            slab_left,
            slab_right,
            slab_right,
            slab_left,
            slab_left,
        ],
        y=[
            0,
            0,
            -thickness,
            -thickness,
            0,
        ],
        mode="lines",
        fill="toself",
        fillcolor="rgba(80,140,210,0.12)",
        line=dict(width=2),
        name="Silicon",
        hoverinfo="skip",
    )
)


# ============================================================
# FRONT SURFACE
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[slab_left, slab_right],
        y=[0, 0],
        mode="lines",
        line=dict(width=4),
        name="Front surface",
        hoverinfo="skip",
    )
)


# ============================================================
# BACK SURFACE
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[slab_left, slab_right],
        y=[-thickness, -thickness],
        mode="lines",
        line=dict(width=4),
        name="Back surface",
        hoverinfo="skip",
    )
)


# ============================================================
# FRONT NORMAL
# ============================================================

normal_length = max(
    0.25 * thickness,
    10.0,
)

fig.add_trace(
    go.Scatter(
        x=[0, 0],
        y=[
            -normal_length,
            normal_length,
        ],
        mode="lines",
        line=dict(
            width=2,
            dash="dash",
        ),
        name="Front normal",
        hoverinfo="skip",
    )
)


# ============================================================
# BACK NORMAL
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[back_x, back_x],
        y=[
            -thickness - normal_length,
            -thickness + normal_length,
        ],
        mode="lines",
        line=dict(
            width=2,
            dash="dash",
        ),
        name="Back normal",
        hoverinfo="skip",
    )
)


# ============================================================
# INCIDENT RAY
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            incident_start_x,
            0,
        ],
        y=[
            incident_start_y,
            0,
        ],
        mode="lines",
        line=dict(width=4),
        name="Incident ray",
        hoverinfo="skip",
    )
)

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
    arrowwidth=2.5,
)


# ============================================================
# FRONT REFLECTED BEAM
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            0,
            front_reflected_end_x,
        ],
        y=[
            0,
            front_reflected_end_y,
        ],
        mode="lines",
        line=dict(width=4),
        name="Front reflected beam",
        hoverinfo="skip",
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
    arrowsize=1.1,
    arrowwidth=2.2,
)


# ============================================================
# REFRACTED RAY INSIDE SILICON
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            0,
            back_x,
        ],
        y=[
            0,
            back_y,
        ],
        mode="lines",
        line=dict(width=4),
        name="Refracted ray inside silicon",
        hoverinfo="skip",
    )
)


# ============================================================
# INTERNAL REFLECTION FROM BACK SURFACE
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            back_x,
            second_front_x,
        ],
        y=[
            back_y,
            0,
        ],
        mode="lines",
        line=dict(width=4),
        name="Internal reflection from back surface",
        hoverinfo="skip",
    )
)

fig.add_annotation(
    x=second_front_x,
    y=0,
    ax=back_x,
    ay=back_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.1,
    arrowwidth=2.2,
)


# ============================================================
# SECOND REFLECTED BEAM
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            second_front_x,
            back_reflected_end_x,
        ],
        y=[
            0,
            back_reflected_end_y,
        ],
        mode="lines",
        line=dict(width=4),
        name="Back reflected beam",
        hoverinfo="skip",
    )
)

fig.add_annotation(
    x=back_reflected_end_x,
    y=back_reflected_end_y,
    ax=second_front_x,
    ay=0,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.1,
    arrowwidth=2.2,
)


# ============================================================
# BACK TRANSMITTED BEAM
# ============================================================

if not tir:

    fig.add_trace(
        go.Scatter(
            x=[
                back_x,
                back_transmitted_end_x,
            ],
            y=[
                back_y,
                back_transmitted_end_y,
            ],
            mode="lines",
            line=dict(width=4),
            name="Back transmitted beam",
            hoverinfo="skip",
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
        arrowsize=1.1,
        arrowwidth=2.2,
    )


# ============================================================
# PERPENDICULAR BEAM GAP
#
# IMPORTANT:
#
# The shortest perpendicular between the two infinite
# parallel reflected beam lines would intersect the second
# line below the front surface if drawn from the first
# reflection point.
#
# Therefore we choose a point further along the first
# reflected beam. The perpendicular is then drawn between
# the actual two visible reflected rays.
# ============================================================

u_x = np.sin(i_rad)
u_y = np.cos(i_rad)

normal_x = np.cos(i_rad)
normal_y = -np.sin(i_rad)


# Choose a point along the first reflected beam far enough
# from the surface that the perpendicular endpoint also
# lies on the visible second reflected beam.

minimum_s = x2 * np.sin(i_rad) + 0.15 * air_length

gap_ray_position = max(
    0.45 * front_reflected_length,
    minimum_s,
)


# Point A on first reflected beam
A_x = gap_ray_position * u_x
A_y = gap_ray_position * u_y


# Point B on second reflected beam
B_x = A_x + beam_gap * normal_x
B_y = A_y + beam_gap * normal_y


# ------------------------------------------------------------
# Gap line
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter(
        x=[A_x, B_x],
        y=[A_y, B_y],
        mode="lines",
        line=dict(
            width=2.5,
            dash="dot",
        ),
        name="Perpendicular beam gap",
        hoverinfo="skip",
    )
)


# ------------------------------------------------------------
# Gap arrows at both ends
# ------------------------------------------------------------

fig.add_annotation(
    x=A_x,
    y=A_y,
    ax=B_x,
    ay=B_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
)

fig.add_annotation(
    x=B_x,
    y=B_y,
    ax=A_x,
    ay=A_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
)


# ============================================================
# GAP LABEL
# ============================================================

fig.add_annotation(
    x=(A_x + B_x) / 2,
    y=(A_y + B_y) / 2,
    text=f"<b>G = {beam_gap:.2f} mm</b>",
    showarrow=False,
    font=dict(size=13),
    bgcolor="rgba(255,255,255,0.85)",
)


# ============================================================
# ANGLE LABELS
# ============================================================

fig.add_annotation(
    x=-0.55 * np.sin(i_rad) * air_length,
    y=0.55 * np.cos(i_rad) * air_length,
    text=f"i = {i_deg:.2f}°",
    showarrow=False,
    font=dict(size=13),
)


fig.add_annotation(
    x=0.5 * x1,
    y=-0.5 * thickness,
    text=f"r = {r_deg:.2f}°",
    showarrow=False,
    font=dict(size=13),
)


# ============================================================
# MATERIAL LABELS
# ============================================================

fig.add_annotation(
    x=slab_left + 0.15 * diameter,
    y=-0.18 * thickness,
    text="<b>SILICON</b>",
    showarrow=False,
    font=dict(size=13),
)


fig.add_annotation(
    x=slab_left + 0.15 * diameter,
    y=0.12 * thickness,
    text="<b>AIR</b>",
    showarrow=False,
    font=dict(size=13),
)


# ============================================================
# NORMAL LABELS
# ============================================================

fig.add_annotation(
    x=0,
    y=0.70 * normal_length,
    text="Normal",
    showarrow=False,
    font=dict(size=12),
)


fig.add_annotation(
    x=back_x,
    y=-thickness + 0.70 * normal_length,
    text="Normal",
    showarrow=False,
    font=dict(size=12),
)


# ============================================================
# RAY LABELS
# ============================================================

fig.add_annotation(
    x=0.65 * incident_start_x,
    y=0.65 * incident_start_y,
    text="Incident ray",
    showarrow=False,
    font=dict(size=12),
)


fig.add_annotation(
    x=0.65 * front_reflected_end_x,
    y=0.65 * front_reflected_end_y,
    text="Front reflected beam",
    showarrow=False,
    font=dict(size=12),
)


fig.add_annotation(
    x=0.5 * x1,
    y=-0.75 * thickness,
    text="Refracted ray",
    showarrow=False,
    font=dict(size=12),
)


fig.add_annotation(
    x=second_front_x + 0.55 * (
        back_reflected_end_x - second_front_x
    ),
    y=0.55 * back_reflected_end_y,
    text="Back reflected beam",
    showarrow=False,
    font=dict(size=12),
)


# ============================================================
# AXIS LIMITS
# ============================================================

x_values = [
    incident_start_x,
    front_reflected_end_x,
    back_reflected_end_x,
    back_x,
    second_front_x,
    A_x,
    B_x,
]

y_values = [
    incident_start_y,
    front_reflected_end_y,
    back_reflected_end_y,
    back_y,
    A_y,
    B_y,
]


if not tir:

    x_values.append(back_transmitted_end_x)
    y_values.append(back_transmitted_end_y)


x_min = min(x_values)
x_max = max(x_values)

y_min = min(y_values)
y_max = max(y_values)


x_span = max(x_max - x_min, 1.0)
y_span = max(y_max - y_min, 1.0)


x_padding = 0.15 * x_span
y_padding = 0.15 * y_span


# ============================================================
# FINAL FIGURE LAYOUT
# ============================================================

fig.update_layout(
    height=760,

    margin=dict(
        l=30,
        r=30,
        t=100,
        b=30,
    ),

    xaxis=dict(
        title="Distance parallel to surface (mm)",
        range=[
            x_min - x_padding,
            x_max + x_padding,
        ],
        showgrid=True,
        zeroline=False,
    ),

    yaxis=dict(
        title="Distance normal to surface (mm)",
        range=[
            y_min - y_padding,
            y_max + y_padding,
        ],
        showgrid=True,
        zeroline=False,

        # Preserve physical angles.
        scaleanchor="x",
        scaleratio=1,
    ),

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),

    hovermode="closest",

    plot_bgcolor="white",

    showlegend=True,
)


# ============================================================
# DISPLAY DIAGRAM
# ============================================================

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displaylogo": False,
        "responsive": True,
    },
)


# ============================================================
# OPTICAL PHYSICS
# ============================================================

st.markdown(
    '<div class="section-title">Live optical quantities</div>',
    unsafe_allow_html=True,
)


col1, col2, col3 = st.columns(3)


with col1:

    st.markdown("### Snell's law")

    st.latex(
        r"""
        n_{\mathrm{air}}\sin i
        =
        n_{\mathrm{Si}}\sin r
        """
    )

    st.write(
        f"External incidence angle: **{i_deg:.2f}°**"
    )

    st.write(
        f"Internal angle: **{r_deg:.2f}°**"
    )


with col2:

    st.markdown("### Critical angle")

    st.latex(
        r"""
        \theta_c =
        \sin^{-1}
        \left(
        \frac{n_{\mathrm{air}}}
        {n_{\mathrm{Si}}}
        \right)
        """
    )

    st.write(
        f"Critical angle: **{critical_deg:.2f}°**"
    )

    if tir:

        st.write(
            f"Internal angle > critical angle"
        )

    else:

        st.write(
            f"Internal angle < critical angle"
        )


with col3:

    st.markdown("### Perpendicular beam gap")

    st.latex(
        r"""
        G =
        2t\tan(r)\cos(i)
        """
    )

    st.write(
        f"Beam separation: **{beam_gap:.2f} mm**"
    )


# ============================================================
# TIR EXPLANATION
# ============================================================

st.markdown(
    '<div class="section-title">Back surface condition</div>',
    unsafe_allow_html=True,
)


if tir:

    st.markdown(
        f"""
        <div class="status-tir">

        <b>Total internal reflection occurs at the silicon → air
        back surface.</b>

        <br><br>

        At the back surface the ray is travelling inside silicon
        and its incidence angle is measured from the back surface
        normal.

        <br><br>

        Internal incidence angle:

        <b>{r_deg:.2f}°</b>

        <br>

        Critical angle:

        <b>{critical_deg:.2f}°</b>

        <br><br>

        Therefore:

        <b>{r_deg:.2f}° &gt; {critical_deg:.2f}°</b>

        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        f"""
        <div class="physics-note">

        <b>Transmission occurs at the silicon → air back surface.</b>

        <br><br>

        At the back surface the relevant angle is the
        <b>internal incidence angle</b> inside silicon.

        <br><br>

        Internal incidence angle:

        <b>{r_deg:.2f}°</b>

        <br>

        Critical angle:

        <b>{critical_deg:.2f}°</b>

        <br><br>

        Therefore:

        <b>{r_deg:.2f}° &lt; {critical_deg:.2f}°</b>

        and the ray can transmit into air.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# INTERFACE OPTICS AND POWER FLOW
# ============================================================

st.markdown("## Interface optics")

# Fresnel coefficients at the front surface
# R_front and T_front are fractions of the incident power
R_front = float(R_front)
T_front = float(T_front)

# Fresnel coefficients at the silicon -> air back surface
# These describe what happens to the light ARRIVING at the back surface.
R_back = float(R_back)
T_back = float(T_back)

# Power flow relative to the ORIGINAL incident beam
#
# Power reaching the back surface:
P_back_incident = T_front

# First reflection from the back surface:
P_back_reflected = P_back_incident * R_back

# First transmission through the back surface:
P_back_transmitted = P_back_incident * T_back

# Display the distinction clearly
st.markdown("### Fresnel coefficients")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Front surface reflectance",
        f"{R_front * 100:.2f}%"
    )

with col2:
    st.metric(
        "Front surface transmittance",
        f"{T_front * 100:.2f}%"
    )

with col3:
    st.metric(
        "Back surface reflectance",
        f"{R_back * 100:.2f}%"
    )

with col4:
    st.metric(
        "Back surface transmittance",
        f"{T_back * 100:.2f}%"
    )

st.markdown("### Power flow relative to original incident beam")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Power reaching back surface",
        f"{P_back_incident * 100:.2f}%"
    )

with col2:
    st.metric(
        "Power reflected at back surface",
        f"{P_back_reflected * 100:.2f}%"
    )

with col3:
    st.metric(
        "Power transmitted through back surface",
        f"{P_back_transmitted * 100:.2f}%"
    )

st.caption(
    f"At the back surface, {P_back_incident * 100:.2f}% of the "
    f"original incident power arrives. Of this, "
    f"{R_back * 100:.2f}% is reflected and "
    f"{T_back * 100:.2f}% is transmitted."
)
