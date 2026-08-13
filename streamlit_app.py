import numpy as np
import streamlit as st
import plotly.graph_objects as go

# ============================================================
# PAGE
# ============================================================
st.set_page_config(
    page_title="Silicon Ray Optics Simulator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-title {font-size:42px;font-weight:700;margin-bottom:2px;}
    .subtitle {font-size:16px;color:#6b7280;margin-bottom:24px;}
    .physics-note {
        padding:14px 18px;border-radius:9px;background:#f7f7f7;
        border:1px solid #ddd;margin:14px 0;
    }
    .status-normal {
        padding:14px 18px;border-radius:9px;background:#eef6ff;
        border:1px solid #c9e0ff;margin:14px 0;
    }
    .status-tir {
        padding:14px 18px;border-radius:9px;background:#fff4e5;
        border:1px solid #ffd18a;margin:14px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">Silicon Ray Optics Simulator</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Live ray tracing through a plane parallel silicon slab. '
    'Change the controls and the complete optical geometry updates immediately.</div>',
    unsafe_allow_html=True,
)

# ============================================================
# PRESETS
# ============================================================
PRESETS = {
    "Small sample": {"thickness": 29.7, "diameter": 42.0, "angle": 45.0},
    "Large sample": {"thickness": 180.0, "diameter": 450.0, "angle": 45.0},
}

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "sample_preset": "Small sample",
    "thickness": 29.7,
    "diameter": 42.0,
    "angle": 45.0,
    "n_si": 3.4800,
    "n_air": 1.0003,
    "wavelength": 1550.0,
    "polarisation": "Unpolarised",
    "_last_preset": "Small sample",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# SIDEBAR
# IMPORTANT: every widget has a unique key.
# ============================================================
st.sidebar.markdown("## Simulation")

preset = st.sidebar.radio(
    "Sample preset",
    ["Small sample", "Large sample", "Custom"],
    key="sample_preset_selector",
)

# Apply a preset only when the user changes the preset.
if preset != st.session_state["_last_preset"]:
    if preset in PRESETS:
        st.session_state["thickness"] = PRESETS[preset]["thickness"]
        st.session_state["diameter"] = PRESETS[preset]["diameter"]
        st.session_state["angle"] = PRESETS[preset]["angle"]
    st.session_state["_last_preset"] = preset

st.sidebar.markdown("---")
st.sidebar.markdown("## Geometry")

thickness = st.sidebar.slider(
    "Silicon thickness, t (mm)",
    min_value=1.0,
    max_value=250.0,
    step=0.1,
    key="thickness",
)

angle_deg = st.sidebar.slider(
    "External incidence angle, i (°)",
    min_value=0.0,
    max_value=89.9,
    step=0.1,
    key="angle",
)

diameter = st.sidebar.number_input(
    "Sample diameter (mm)",
    min_value=1.0,
    max_value=1000.0,
    step=1.0,
    key="diameter",
)

st.sidebar.markdown("---")
st.sidebar.markdown("## Optical properties")

n_si = st.sidebar.number_input(
    "Silicon refractive index, nSi",
    min_value=1.0001,
    max_value=10.0,
    step=0.0001,
    format="%.4f",
    key="n_si",
)

n_air = st.sidebar.number_input(
    "Air refractive index, nair",
    min_value=1.0000,
    max_value=2.0,
    step=0.0001,
    format="%.4f",
    key="n_air",
)

wavelength = st.sidebar.number_input(
    "Wavelength (nm)",
    min_value=200.0,
    max_value=5000.0,
    step=1.0,
    key="wavelength",
)

polarisation = st.sidebar.selectbox(
    "Polarisation",
    ["Unpolarised", "s", "p"],
    key="polarisation",
)

# ============================================================
# OPTICS
# ============================================================
i = np.deg2rad(angle_deg)

# Air -> silicon refraction.
sin_r = (n_air / n_si) * np.sin(i)

if abs(sin_r) <= 1.0:
    r = np.arcsin(np.clip(sin_r, -1.0, 1.0))
    transmission_into_silicon = True
else:
    # This only occurs for an unusual custom choice where n_air > n_si.
    r = np.nan
    transmission_into_silicon = False

r_deg = np.rad2deg(r) if transmission_into_silicon else np.nan

# Critical angle for silicon -> air.
if n_si > n_air:
    critical_deg = np.rad2deg(np.arcsin(n_air / n_si))
else:
    critical_deg = 90.0

# IMPORTANT PHYSICS:
# For a ray entering silicon from air, Snell's law guarantees
# r <= critical angle. Therefore the back surface is normally
# transmitting, not TIR. TIR can only occur if an internal ray
# arrives at the silicon -> air interface with angle > theta_c.
#
# Keep the general TIR calculation here, but do not incorrectly
# label the externally launched ray as TIR.
tir = (
    transmission_into_silicon
    and n_si > n_air
    and r_deg > critical_deg + 1e-10
)

# ============================================================
# FRESNEL POWER COEFFICIENTS
# ============================================================
def fresnel_power(n1, n2, theta1, pol):
    """Return power reflectance R and transmittance T."""
    sin_theta2 = (n1 / n2) * np.sin(theta1)

    # Total internal reflection.
    if abs(sin_theta2) >= 1.0:
        return 1.0, 0.0

    theta2 = np.arcsin(np.clip(sin_theta2, -1.0, 1.0))
    c1 = np.cos(theta1)
    c2 = np.cos(theta2)

    rs = ((n1 * c1 - n2 * c2) / (n1 * c1 + n2 * c2)) ** 2
    rp = ((n2 * c1 - n1 * c2) / (n2 * c1 + n1 * c2)) ** 2

    if pol == "s":
        R = rs
    elif pol == "p":
        R = rp
    else:
        R = 0.5 * (rs + rp)

    T = 1.0 - R
    return float(R), float(T)


R_front, T_front = fresnel_power(
    n_air, n_si, i, polarisation
)

if transmission_into_silicon:
    R_back, T_back = fresnel_power(
        n_si, n_air, r, polarisation
    )
else:
    R_back, T_back = 1.0, 0.0

# ============================================================
# POWER FLOW
# Every P quantity is relative to the ORIGINAL incident power.
# ============================================================
P_incident = 1.0

# At the front air -> silicon surface.
P_front_reflected = P_incident * R_front
P_entering_silicon = P_incident * T_front

# At the back silicon -> air surface.
P_back_incident = P_entering_silicon
P_back_reflected = P_back_incident * R_back
P_back_transmitted = P_back_incident * T_back

# The first back-reflected beam returns to the front surface.
P_second_front_transmitted = P_back_reflected * T_front
P_second_internal_reflected = P_back_reflected * R_front

# ============================================================
# GEOMETRY
# ============================================================
if transmission_into_silicon:
    x1 = thickness * np.tan(r)
else:
    x1 = 0.0

# Horizontal shift of the ray after going down and back through slab.
x2 = 2.0 * x1

# Perpendicular separation between the two external reflected rays.
# The two reflected rays are parallel and their perpendicular
# separation is:
#
#       G = 2 t tan(r) cos(i)
#
beam_gap = abs(2.0 * thickness * np.tan(r) * np.cos(i)) \
    if transmission_into_silicon else np.nan

# Directions in the plotted x-y plane.
# y > 0 is air, y < 0 is silicon.
u_ref = np.array([np.sin(i), np.cos(i)])
u_inc = np.array([np.sin(i), -np.cos(i)])
u_perp = np.array([np.cos(i), -np.sin(i)])

air_len = max(0.9 * thickness, 20.0)
ref_len = max(0.9 * thickness, 20.0)

incident_start = np.array(
    [-air_len * np.sin(i), air_len * np.cos(i)]
)

first_ref_end = np.array(
    [ref_len * np.sin(i), ref_len * np.cos(i)]
)

second_ref_start = np.array([x2, 0.0])
second_ref_end = second_ref_start + ref_len * u_ref

# A and B lie on the two external reflected rays and are connected
# by a line perpendicular to both rays.
if transmission_into_silicon:
    s_gap = max(0.35 * ref_len, 0.5 * x2 + 0.15 * air_len)
    A = s_gap * u_ref
    B = A + beam_gap * u_perp
else:
    A = np.array([0.0, 0.0])
    B = np.array([0.0, 0.0])

# ============================================================
# FIGURE
# ============================================================
fig = go.Figure()

left = -diameter / 2.0
right = diameter / 2.0

# Silicon slab.
fig.add_trace(
    go.Scatter(
        x=[left, right, right, left, left],
        y=[0, 0, -thickness, -thickness, 0],
        mode="lines",
        fill="toself",
        fillcolor="rgba(80,140,210,0.12)",
        line=dict(width=2),
        name="Silicon",
        hoverinfo="skip",
    )
)

# Surfaces.
fig.add_trace(
    go.Scatter(
        x=[left, right],
        y=[0, 0],
        mode="lines",
        line=dict(width=4),
        name="Front surface",
        hoverinfo="skip",
    )
)

fig.add_trace(
    go.Scatter(
        x=[left, right],
        y=[-thickness, -thickness],
        mode="lines",
        line=dict(width=4),
        name="Back surface",
        hoverinfo="skip",
    )
)

# Normals.
normal_len = max(0.25 * thickness, 10.0)

fig.add_trace(
    go.Scatter(
        x=[0, 0],
        y=[-normal_len, normal_len],
        mode="lines",
        line=dict(width=2, dash="dash"),
        name="Front normal",
        hoverinfo="skip",
    )
)

fig.add_trace(
    go.Scatter(
        x=[x1, x1],
        y=[-thickness - normal_len, -thickness + normal_len],
        mode="lines",
        line=dict(width=2, dash="dash"),
        name="Back normal",
        hoverinfo="skip",
    )
)

# ------------------------------------------------------------
# Incident ray
# ------------------------------------------------------------
fig.add_trace(
    go.Scatter(
        x=[incident_start[0], 0],
        y=[incident_start[1], 0],
        mode="lines",
        line=dict(width=4),
        name="Incident ray",
        hoverinfo="skip",
    )
)

fig.add_annotation(
    x=0,
    y=0,
    ax=incident_start[0],
    ay=incident_start[1],
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=1.1,
    arrowwidth=2.5,
)

# ------------------------------------------------------------
# Front reflected beam
# ------------------------------------------------------------
fig.add_trace(
    go.Scatter(
        x=[0, first_ref_end[0]],
        y=[0, first_ref_end[1]],
        mode="lines",
        line=dict(width=4),
        name="Front reflected beam",
        hoverinfo="skip",
    )
)

fig.add_annotation(
    x=first_ref_end[0],
    y=first_ref_end[1],
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

# ------------------------------------------------------------
# Refracted ray inside silicon
# ------------------------------------------------------------
if transmission_into_silicon:
    fig.add_trace(
        go.Scatter(
            x=[0, x1],
            y=[0, -thickness],
            mode="lines",
            line=dict(width=4),
            name="Refracted ray inside silicon",
            hoverinfo="skip",
        )
    )

# ------------------------------------------------------------
# Back-surface reflected ray inside silicon
# ------------------------------------------------------------
if transmission_into_silicon:
    fig.add_trace(
        go.Scatter(
            x=[x1, x2],
            y=[-thickness, 0],
            mode="lines",
            line=dict(width=4),
            name="Internal reflection from back surface",
            hoverinfo="skip",
        )
    )

    fig.add_annotation(
        x=x2,
        y=0,
        ax=x1,
        ay=-thickness,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.1,
        arrowwidth=2.2,
    )

# ------------------------------------------------------------
# Second external reflected beam
# ------------------------------------------------------------
if transmission_into_silicon:
    fig.add_trace(
        go.Scatter(
            x=[second_ref_start[0], second_ref_end[0]],
            y=[second_ref_start[1], second_ref_end[1]],
            mode="lines",
            line=dict(width=4),
            name="Back reflected beam",
            hoverinfo="skip",
        )
    )

    fig.add_annotation(
        x=second_ref_end[0],
        y=second_ref_end[1],
        ax=second_ref_start[0],
        ay=second_ref_start[1],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.1,
        arrowwidth=2.2,
    )

# ------------------------------------------------------------
# Back-transmitted beam
# ------------------------------------------------------------
if transmission_into_silicon and not tir:
    trans_len = max(0.8 * thickness, 20.0)

    tx = x1 + trans_len * np.sin(i)
    ty = -thickness - trans_len * np.cos(i)

    fig.add_trace(
        go.Scatter(
            x=[x1, tx],
            y=[-thickness, ty],
            mode="lines",
            line=dict(width=4),
            name="Back transmitted beam",
            hoverinfo="skip",
        )
    )

    fig.add_annotation(
        x=tx,
        y=ty,
        ax=x1,
        ay=-thickness,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.1,
        arrowwidth=2.2,
    )

# ------------------------------------------------------------
# Perpendicular reflected-beam gap
# ------------------------------------------------------------
if transmission_into_silicon and np.isfinite(beam_gap) and beam_gap > 1e-9:
    fig.add_trace(
        go.Scatter(
            x=[A[0], B[0]],
            y=[A[1], B[1]],
            mode="lines",
            line=dict(width=2.5, dash="dot"),
            name="Perpendicular beam gap",
            hoverinfo="skip",
        )
    )

    fig.add_annotation(
        x=(A[0] + B[0]) / 2,
        y=(A[1] + B[1]) / 2,
        text=f"<b>G = {beam_gap:.2f} mm</b>",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.90)",
    )

# ------------------------------------------------------------
# Labels
# ------------------------------------------------------------
fig.add_annotation(
    x=incident_start[0] * 0.62,
    y=incident_start[1] * 0.62,
    text="Incident ray →",
    showarrow=False,
)

fig.add_annotation(
    x=first_ref_end[0] * 0.62,
    y=first_ref_end[1] * 0.62,
    text="Front reflected beam",
    showarrow=False,
)

if transmission_into_silicon:
    fig.add_annotation(
        x=0.55 * x1,
        y=-0.50 * thickness,
        text=f"r = {r_deg:.2f}°",
        showarrow=False,
    )

fig.add_annotation(
    x=0,
    y=0.72 * normal_len,
    text="Normal",
    showarrow=False,
)

fig.add_annotation(
    x=x1,
    y=-thickness + 0.72 * normal_len,
    text="Normal",
    showarrow=False,
)

fig.add_annotation(
    x=left + 0.15 * diameter,
    y=-0.18 * thickness,
    text="<b>SILICON</b>",
    showarrow=False,
)

fig.add_annotation(
    x=left + 0.15 * diameter,
    y=0.12 * thickness,
    text="<b>AIR</b>",
    showarrow=False,
)

# ------------------------------------------------------------
# Plot limits
# ------------------------------------------------------------
all_x = [
    incident_start[0],
    first_ref_end[0],
    second_ref_end[0],
    x1,
    x2,
]
all_y = [
    incident_start[1],
    first_ref_end[1],
    second_ref_end[1],
    -thickness,
    0,
]

if transmission_into_silicon:
    all_x += [A[0], B[0]]
    all_y += [A[1], B[1]]

if transmission_into_silicon and not tir:
    all_x.append(tx)
    all_y.append(ty)

xmin, xmax = min(all_x), max(all_x)
ymin, ymax = min(all_y), max(all_y)

xp = max(0.15 * (xmax - xmin), 1.0)
yp = max(0.15 * (ymax - ymin), 1.0)

fig.update_layout(
    height=760,
    margin=dict(l=30, r=30, t=90, b=30),
    plot_bgcolor="white",
    hovermode="closest",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        x=0,
    ),
    xaxis=dict(
        title="Distance parallel to surface (mm)",
        range=[xmin - xp, xmax + xp],
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        title="Distance normal to surface (mm)",
        range=[ymin - yp, ymax + yp],
        showgrid=True,
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
    ),
    showlegend=True,
)

st.plotly_chart(
    fig,
    width="stretch",
    config={"displaylogo": False, "responsive": True},
)

# ============================================================
# LIVE QUANTITIES
# ============================================================
st.markdown("## Live optical quantities")

c1, c2, c3, c4 = st.columns(4)

c1.metric("External angle, i", f"{angle_deg:.2f}°")
c2.metric(
    "Internal angle, r",
    f"{r_deg:.2f}°" if transmission_into_silicon else "No transmission",
)
c3.metric("Critical angle, θc", f"{critical_deg:.2f}°")
c4.metric(
    "Perpendicular beam gap, G",
    f"{beam_gap:.2f} mm" if np.isfinite(beam_gap) else "—",
)

# ============================================================
# BACK-SURFACE PHYSICAL CONDITION
# ============================================================
if tir:
    st.markdown(
        f"""
        <div class="status-tir">
        <b>Total internal reflection at the silicon → air back surface.</b>
        <br><br>
        The relevant angle is the <b>internal incidence angle</b> at the
        back surface.
        <br><br>
        Internal incidence angle: <b>{r_deg:.2f}°</b><br>
        Critical angle: <b>{critical_deg:.2f}°</b><br><br>
        Therefore <b>{r_deg:.2f}° &gt; {critical_deg:.2f}°</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="status-normal">
        <b>Transmission occurs at the silicon → air back surface.</b>
        <br><br>
        At the back surface, the relevant angle is the
        <b>internal incidence angle</b> inside silicon.
        <br><br>
        Internal incidence angle: <b>{r_deg:.2f}°</b><br>
        Critical angle: <b>{critical_deg:.2f}°</b><br><br>
        Therefore <b>{r_deg:.2f}° &lt; {critical_deg:.2f}°</b>,
        so the ray is below the critical angle and can transmit into air.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# INTERFACE OPTICS
# ============================================================
st.markdown("## Interface optics")

st.markdown("### Fresnel coefficients at each interface")

f1, f2, f3, f4 = st.columns(4)

f1.metric(
    "Front surface reflectance R",
    f"{100 * R_front:.2f}%",
)

f2.metric(
    "Front surface transmittance T",
    f"{100 * T_front:.2f}%",
)

f3.metric(
    "Back surface reflectance R",
    f"{100 * R_back:.2f}%",
)

f4.metric(
    "Back surface transmittance T",
    f"{100 * T_back:.2f}%",
)

st.markdown("### Power flow relative to the original incident beam")

p1, p2, p3 = st.columns(3)

p1.metric(
    "Power entering silicon",
    f"{100 * P_entering_silicon:.2f}%",
)

p2.metric(
    "Back-reflected power",
    f"{100 * P_back_reflected:.2f}%",
)

p3.metric(
    "Back-transmitted power",
    f"{100 * P_back_transmitted:.2f}%",
)

st.markdown(
    f"""
    <div class="physics-note">
    <b>Power accounting</b><br><br>

    Original incident power: <b>100%</b><br>

    Front surface:<br>
    → <b>{100 * P_front_reflected:.2f}%</b> is reflected immediately<br>
    → <b>{100 * P_entering_silicon:.2f}%</b> enters the silicon<br><br>

    At the back surface, the incoming power is
    <b>{100 * P_back_incident:.2f}%</b> of the original beam:<br>
    → <b>{100 * P_back_reflected:.2f}%</b> is reflected back inside the silicon<br>
    → <b>{100 * P_back_transmitted:.2f}%</b> leaves through the back surface<br><br>

    The back-reflected beam then reaches the front surface again:<br>
    → <b>{100 * P_second_front_transmitted:.2f}%</b> of the original incident
    power leaves through the front surface<br>
    → <b>{100 * P_second_internal_reflected:.2f}%</b> is reflected back
    into the silicon.
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"λ = {wavelength:.0f} nm | nSi = {n_si:.4f} | "
    f"nair = {n_air:.4f} | Polarisation = {polarisation}"
)

st.markdown(
    """
    <div class="physics-note">
    <b>Beam gap:</b> G is the shortest, perpendicular distance between
    the two parallel external reflected beam paths. It is not an internal
    displacement and it is not measured along the surface normal.
    </div>
    """,
    unsafe_allow_html=True,
)
