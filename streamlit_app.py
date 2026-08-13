from pathlib import Path

code = r'''
import numpy as np
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Silicon Ray Optics Simulator",
    page_icon="🔬",
    layout="wide",
)

st.markdown("""
<style>
.main-title {font-size:42px;font-weight:700;margin-bottom:2px;}
.subtitle {font-size:16px;color:#6b7280;margin-bottom:24px;}
.physics-note {padding:14px 18px;border-radius:9px;background:#f7f7f7;
border:1px solid #ddd;margin:14px 0;}
.status-normal {padding:14px 18px;border-radius:9px;background:#eef6ff;
border:1px solid #c9e0ff;margin:14px 0;}
.status-tir {padding:14px 18px;border-radius:9px;background:#fff4e5;
border:1px solid #ffd18a;margin:14px 0;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Silicon Ray Optics Simulator</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Live ray tracing through a plane parallel silicon slab. '
    'Change the controls and the complete optical geometry updates immediately.</div>',
    unsafe_allow_html=True
)

# ------------------------------------------------------------
# PRESETS
# ------------------------------------------------------------
PRESETS = {
    "Small sample": {"thickness": 29.7, "diameter": 42.0, "angle": 45.0},
    "Large sample": {"thickness": 180.0, "diameter": 450.0, "angle": 45.0},
}

if "sample_preset" not in st.session_state:
    st.session_state.sample_preset = "Small sample"
    st.session_state.thickness = PRESETS["Small sample"]["thickness"]
    st.session_state.diameter = PRESETS["Small sample"]["diameter"]
    st.session_state.angle = PRESETS["Small sample"]["angle"]

preset = st.sidebar.radio(
    "Sample preset",
    ["Small sample", "Large sample", "Custom"],
    key="sample_preset",
)

if preset in PRESETS and st.session_state.get("_last_preset") != preset:
    st.session_state.thickness = PRESETS[preset]["thickness"]
    st.session_state.diameter = PRESETS[preset]["diameter"]
    st.session_state.angle = PRESETS[preset]["angle"]

st.session_state._last_preset = preset

st.sidebar.markdown("---")
st.sidebar.markdown("## Geometry")

thickness = st.sidebar.slider(
    "Silicon thickness, t (mm)", 1.0, 250.0,
    float(st.session_state.thickness), 0.1,
    key="thickness"
)

angle_deg = st.sidebar.slider(
    "External incidence angle, i (°)", 0.0, 89.9,
    float(st.session_state.angle), 0.1,
    key="angle"
)

diameter = st.sidebar.number_input(
    "Sample diameter (mm)", 1.0, 1000.0,
    float(st.session_state.diameter), 1.0,
    key="diameter"
)

st.sidebar.markdown("---")
st.sidebar.markdown("## Optical properties")

n_si = st.sidebar.number_input(
    "Silicon refractive index, nSi",
    1.0, 10.0, 3.4800, 0.0001, format="%.4f"
)

n_air = st.sidebar.number_input(
    "Air refractive index, nair",
    1.0, 2.0, 1.0003, 0.0001, format="%.4f"
)

wavelength = st.sidebar.number_input(
    "Wavelength (nm)", 200.0, 5000.0, 1550.0, 1.0
)

polarisation = st.sidebar.selectbox(
    "Polarisation", ["Unpolarised", "s", "p"]
)

# ------------------------------------------------------------
# ANGLES AND SNELL'S LAW
# ------------------------------------------------------------
i = np.deg2rad(angle_deg)

sin_r = np.clip((n_air / n_si) * np.sin(i), -1.0, 1.0)
r = np.arcsin(sin_r)
r_deg = np.rad2deg(r)

critical_deg = np.rad2deg(np.arcsin(n_air / n_si)) if n_si > n_air else 90.0
tir = r_deg >= critical_deg

# ------------------------------------------------------------
# FRESNEL FUNCTION
# ------------------------------------------------------------
def fresnel(n1, n2, theta, pol):
    s = np.sin(theta)
    c1 = np.cos(theta)
    value = np.clip((n1 / n2) * s, -1.0, 1.0)

    if abs(value) >= 1.0:
        return 1.0, 0.0

    theta2 = np.arcsin(value)
    c2 = np.cos(theta2)

    rs = ((n1*c1 - n2*c2) / (n1*c1 + n2*c2)) ** 2
    rp = ((n2*c1 - n1*c2) / (n2*c1 + n1*c2)) ** 2

    ts = 1.0 - rs
    tp = 1.0 - rp

    if pol == "s":
        return rs, ts
    if pol == "p":
        return rp, tp
    return 0.5*(rs + rp), 0.5*(ts + tp)

R_front, T_front = fresnel(n_air, n_si, i, polarisation)
R_back, T_back = fresnel(n_si, n_air, r, polarisation)

if tir:
    R_back = 1.0
    T_back = 0.0

# ------------------------------------------------------------
# POWER FLOW
# All powers below are fractions of ORIGINAL incident power.
# ------------------------------------------------------------
P_incident = 1.0
P_front_reflected = P_incident * R_front
P_entering_silicon = P_incident * T_front

P_back_incident = P_entering_silicon
P_back_reflected = P_back_incident * R_back
P_back_transmitted = P_back_incident * T_back

# The first back-reflected beam reaches the front surface.
P_second_front_transmitted = P_back_reflected * T_front
P_second_internal_reflected = P_back_reflected * R_front

# ------------------------------------------------------------
# GEOMETRY
# ------------------------------------------------------------
x1 = thickness * np.tan(r)
x2 = 2.0 * x1

# Perpendicular separation between the two external reflected rays.
beam_gap = abs(2.0 * thickness * np.tan(r) * np.cos(i))

air_len = max(0.9 * thickness, 20.0)
incident_x = -air_len * np.sin(i)
incident_y = air_len * np.cos(i)

ref_len = max(0.9 * thickness, 20.0)

front_end_x = ref_len * np.sin(i)
front_end_y = ref_len * np.cos(i)

second_end_x = x2 + ref_len * np.sin(i)
second_end_y = ref_len * np.cos(i)

# A point on first reflected ray and its perpendicular projection
# onto the second parallel reflected ray.
u = np.array([np.sin(i), np.cos(i)])
perp = np.array([np.cos(i), -np.sin(i)])

s_gap = max(0.45 * ref_len, x2 * np.sin(i) + 0.15 * air_len)
A = s_gap * u
B = A + beam_gap * perp

# ------------------------------------------------------------
# FIGURE
# ------------------------------------------------------------
fig = go.Figure()

left = -diameter / 2
right = diameter / 2

fig.add_trace(go.Scatter(
    x=[left, right, right, left, left],
    y=[0, 0, -thickness, -thickness, 0],
    mode="lines",
    fill="toself",
    fillcolor="rgba(80,140,210,0.12)",
    line=dict(width=2),
    name="Silicon",
    hoverinfo="skip"
))

# Surfaces
fig.add_trace(go.Scatter(
    x=[left, right], y=[0, 0], mode="lines",
    line=dict(width=4), name="Front surface", hoverinfo="skip"
))
fig.add_trace(go.Scatter(
    x=[left, right], y=[-thickness, -thickness], mode="lines",
    line=dict(width=4), name="Back surface", hoverinfo="skip"
))

# Normals
normal_len = max(0.25 * thickness, 10.0)

fig.add_trace(go.Scatter(
    x=[0, 0], y=[-normal_len, normal_len],
    mode="lines", line=dict(width=2, dash="dash"),
    name="Front normal", hoverinfo="skip"
))
fig.add_trace(go.Scatter(
    x=[x1, x1], y=[-thickness-normal_len, -thickness+normal_len],
    mode="lines", line=dict(width=2, dash="dash"),
    name="Back normal", hoverinfo="skip"
))

# Incident ray
fig.add_trace(go.Scatter(
    x=[incident_x, 0], y=[incident_y, 0],
    mode="lines", line=dict(width=4), name="Incident ray",
    hoverinfo="skip"
))
fig.add_annotation(
    x=0, y=0, ax=incident_x, ay=incident_y,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=2.5
)

# First reflected ray
fig.add_trace(go.Scatter(
    x=[0, front_end_x], y=[0, front_end_y],
    mode="lines", line=dict(width=4),
    name="Front reflected beam", hoverinfo="skip"
))
fig.add_annotation(
    x=front_end_x, y=front_end_y, ax=0, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=2.2
)

# Refracted ray
fig.add_trace(go.Scatter(
    x=[0, x1], y=[0, -thickness],
    mode="lines", line=dict(width=4),
    name="Refracted ray", hoverinfo="skip"
))

# Back reflection
fig.add_trace(go.Scatter(
    x=[x1, x2], y=[-thickness, 0],
    mode="lines", line=dict(width=4),
    name="Back surface reflected path", hoverinfo="skip"
))
fig.add_annotation(
    x=x2, y=0, ax=x1, ay=-thickness,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=2.2
)

# Second external reflected ray
fig.add_trace(go.Scatter(
    x=[x2, second_end_x], y=[0, second_end_y],
    mode="lines", line=dict(width=4),
    name="Second reflected beam", hoverinfo="skip"
))
fig.add_annotation(
    x=second_end_x, y=second_end_y, ax=x2, ay=0,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=2.2
)

# Back transmitted ray, only below critical angle
if not tir:
    trans_len = max(0.8 * thickness, 20.0)
    tx = x1 + trans_len * np.sin(i)
    ty = -thickness - trans_len * np.cos(i)

    fig.add_trace(go.Scatter(
        x=[x1, tx], y=[-thickness, ty],
        mode="lines", line=dict(width=4),
        name="Back transmitted beam", hoverinfo="skip"
    ))
    fig.add_annotation(
        x=tx, y=ty, ax=x1, ay=-thickness,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=2.2
    )

# Perpendicular gap
fig.add_trace(go.Scatter(
    x=[A[0], B[0]], y=[A[1], B[1]],
    mode="lines",
    line=dict(width=2.5, dash="dot"),
    name="Perpendicular beam gap",
    hoverinfo="skip"
))

fig.add_annotation(
    x=(A[0]+B[0])/2, y=(A[1]+B[1])/2,
    text=f"<b>G = {beam_gap:.2f} mm</b>",
    showarrow=False,
    bgcolor="rgba(255,255,255,0.85)"
)

# Labels
fig.add_annotation(
    x=incident_x*0.62, y=incident_y*0.62,
    text="Incident ray", showarrow=False
)
fig.add_annotation(
    x=front_end_x*0.62, y=front_end_y*0.62,
    text="Front reflected beam", showarrow=False
)
fig.add_annotation(
    x=0.5*x1, y=-0.55*thickness,
    text=f"r = {r_deg:.2f}°", showarrow=False
)
fig.add_annotation(
    x=0, y=0.72*normal_len,
    text="Normal", showarrow=False
)
fig.add_annotation(
    x=x1, y=-thickness+0.72*normal_len,
    text="Normal", showarrow=False
)
fig.add_annotation(
    x=left+0.15*diameter, y=-0.18*thickness,
    text="<b>SILICON</b>", showarrow=False
)
fig.add_annotation(
    x=left+0.15*diameter, y=0.12*thickness,
    text="<b>AIR</b>", showarrow=False
)

all_x = [incident_x, front_end_x, second_end_x, x1, x2, A[0], B[0]]
all_y = [incident_y, front_end_y, second_end_y, -thickness, A[1], B[1]]

if not tir:
    all_x.append(tx)
    all_y.append(ty)

xmin, xmax = min(all_x), max(all_x)
ymin, ymax = min(all_y), max(all_y)

xp = max(0.15*(xmax-xmin), 1)
yp = max(0.15*(ymax-ymin), 1)

fig.update_layout(
    height=760,
    margin=dict(l=30, r=30, t=90, b=30),
    plot_bgcolor="white",
    hovermode="closest",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    xaxis=dict(
        title="Distance parallel to surface (mm)",
        range=[xmin-xp, xmax+xp],
        showgrid=True, zeroline=False
    ),
    yaxis=dict(
        title="Distance normal to surface (mm)",
        range=[ymin-yp, ymax+yp],
        showgrid=True, zeroline=False,
        scaleanchor="x", scaleratio=1
    ),
    showlegend=True
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displaylogo": False, "responsive": True}
)

# ------------------------------------------------------------
# LIVE QUANTITIES
# ------------------------------------------------------------
st.markdown("## Live optical quantities")

c1, c2, c3, c4 = st.columns(4)

c1.metric("External angle, i", f"{angle_deg:.2f}°")
c2.metric("Internal angle, r", f"{r_deg:.2f}°")
c3.metric("Critical angle, θc", f"{critical_deg:.2f}°")
c4.metric("Perpendicular beam gap, G", f"{beam_gap:.2f} mm")

# ------------------------------------------------------------
# TIR CONDITION
# ------------------------------------------------------------
if tir:
    st.markdown(
        f"""
        <div class="status-tir">
        <b>Total internal reflection at the silicon → air back surface.</b>
        <br><br>
        The relevant angle is the <b>internal incidence angle</b> at the
        back surface, not the external incidence angle.
        <br><br>
        Internal angle: <b>{r_deg:.2f}°</b><br>
        Critical angle: <b>{critical_deg:.2f}°</b><br><br>
        Therefore <b>{r_deg:.2f}° &gt; {critical_deg:.2f}°</b>.
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div class="status-normal">
        <b>Transmission occurs at the silicon → air back surface.</b>
        <br><br>
        Internal incidence angle: <b>{r_deg:.2f}°</b><br>
        Critical angle: <b>{critical_deg:.2f}°</b><br><br>
        Therefore <b>{r_deg:.2f}° &lt; {critical_deg:.2f}°</b>.
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------------------------------------------------
# INTERFACE OPTICS
# ------------------------------------------------------------
st.markdown("## Interface optics")

st.markdown("### Fresnel coefficients")

f1, f2, f3, f4 = st.columns(4)
f1.metric("Front reflectance R", f"{100*R_front:.2f}%")
f2.metric("Front transmittance T", f"{100*T_front:.2f}%")
f3.metric("Back reflectance R", f"{100*R_back:.2f}%")
f4.metric("Back transmittance T", f"{100*T_back:.2f}%")

st.markdown("### Power flow relative to the original incident beam")

p1, p2, p3 = st.columns(3)
p1.metric("Power reaching back surface", f"{100*P_back_incident:.2f}%")
p2.metric("Power reflected at back", f"{100*P_back_reflected:.2f}%")
p3.metric("Power transmitted at back", f"{100*P_back_transmitted:.2f}%")

st.markdown("### Subsequent front surface interaction")

q1, q2 = st.columns(2)
q1.metric(
    "Back-reflected power transmitted out front",
    f"{100*P_second_front_transmitted:.2f}%"
)
q2.metric(
    "Back-reflected power reflected internally again",
    f"{100*P_second_internal_reflected:.2f}%"
)

st.markdown(
    f"""
    <div class="physics-note">
    <b>Power accounting:</b><br><br>
    100% incident<br>
    → {100*P_front_reflected:.2f}% reflected at the front surface<br>
    → {100*P_entering_silicon:.2f}% enters silicon<br><br>
    Of the {100*P_back_incident:.2f}% reaching the back surface:<br>
    → {100*P_back_reflected:.2f}% is reflected<br>
    → {100*P_back_transmitted:.2f}% is transmitted
    through the back surface.
    <br><br>
    The back reflected beam then returns to the front surface, where
    {100*P_second_front_transmitted:.2f}% of the original incident power
    exits through the front surface and
    {100*P_second_internal_reflected:.2f}% is reflected internally again.
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    f"λ = {wavelength:.0f} nm | nSi = {n_si:.4f} | "
    f"nair = {n_air:.4f} | Polarisation = {polarisation}"
)

st.markdown(
    """
    <div class="physics-note">
    <b>Note:</b> the dotted line labelled G is the perpendicular
    separation between the two external reflected beam paths. It is
    not an internal displacement Δx and is not measured from the normal.
    </div>
    """,
    unsafe_allow_html=True
)
'''

path = "/mnt/data/streamlit_app.py"
Path(path).write_text(code, encoding="utf-8")
print(path)
