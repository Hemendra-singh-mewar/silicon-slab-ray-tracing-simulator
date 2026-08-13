
import math
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Silicon Ray Optics Laboratory",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Physics
# ============================================================
def snell(n1, n2, theta_deg):
    s = (n1 / n2) * math.sin(math.radians(theta_deg))
    if abs(s) > 1.0:
        return None
    return math.degrees(math.asin(s))

def fresnel_unpolarised(n1, n2, theta_i_deg):
    """Power reflectance/transmittance at a dielectric interface."""
    theta_i = math.radians(theta_i_deg)
    s = (n1 / n2) * math.sin(theta_i)
    if abs(s) >= 1:
        return 1.0, 0.0, None

    theta_t = math.asin(s)
    rs = ((n1 * math.cos(theta_i) - n2 * math.cos(theta_t)) /
          (n1 * math.cos(theta_i) + n2 * math.cos(theta_t))) ** 2
    rp = ((n1 * math.cos(theta_t) - n2 * math.cos(theta_i)) /
          (n1 * math.cos(theta_t) + n2 * math.cos(theta_i))) ** 2
    R = 0.5 * (rs + rp)
    return R, 1 - R, math.degrees(theta_t)

def calculate(t, i_deg, n_si, n_air):
    critical = math.degrees(math.asin(min(1, n_air / n_si)))
    r_deg = snell(n_air, n_si, i_deg)

    if r_deg is None:
        return {
            "critical": critical,
            "r": None,
            "gap": None,
            "horizontal": None,
            "back_x": None,
            "regime": "TIR at front surface",
        }

    r = math.radians(r_deg)
    i = math.radians(i_deg)

    # Distance along the front surface between the two emerging
    # reflected rays.
    horizontal = 2 * t * math.tan(r)

    # Perpendicular distance between the two parallel reflected rays.
    # This is the quantity used in the user's original figure.
    gap = horizontal * math.cos(i)

    # Internal reflection point at the back surface.
    back_x = t * math.tan(r)

    R_front, T_front, _ = fresnel_unpolarised(n_air, n_si, i_deg)
    R_back, T_back, _ = fresnel_unpolarised(n_si, n_air, r_deg)

    return {
        "critical": critical,
        "r": r_deg,
        "gap": gap,
        "horizontal": horizontal,
        "back_x": back_x,
        "R_front": R_front,
        "T_front": T_front,
        "R_back": R_back,
        "T_back": T_back,
        "regime": "Refraction + internal reflection",
    }

# ============================================================
# Sidebar controls
# ============================================================
with st.sidebar:
    st.header("🔬 Silicon Ray Optics")

    st.subheader("Sample")
    preset = st.radio(
        "Choose sample",
        ["Small sample", "Large sample"],
        index=0,
    )

    if preset == "Small sample":
        preset_t = 29.7
        preset_i = 45.0
    else:
        preset_t = 100.0
        preset_i = 45.0

    st.caption(
        "The sliders remain fully adjustable after choosing a preset."
    )

    st.divider()
    st.subheader("Geometry")

    t = st.slider(
        "Silicon thickness, t (mm)",
        1.0, 150.0, float(preset_t), 0.1,
        help="Physical thickness of the silicon slab."
    )

    i_deg = st.slider(
        "Angle of incidence, i (°)",
        0.0, 89.9, float(preset_i), 0.1,
        help="Angle measured from the surface normal."
    )

    st.subheader("Optical properties")

    n_si = st.number_input(
        "Silicon refractive index, nSi",
        min_value=1.0, max_value=6.0,
        value=3.4800, step=0.001, format="%.4f"
    )

    n_air = st.number_input(
        "Air refractive index, nair",
        min_value=1.0, max_value=2.0,
        value=1.0003, step=0.0001, format="%.4f"
    )

    wavelength = st.number_input(
        "Wavelength (nm)",
        min_value=200.0, max_value=5000.0,
        value=1550.0, step=1.0
    )

    st.divider()
    st.subheader("Diagram")
    show_fresnel = st.checkbox("Show Fresnel information", True)
    show_labels = st.checkbox("Show all labels", True)

# ============================================================
# Main calculation
# ============================================================
d = calculate(t, i_deg, n_si, n_air)
critical = d["critical"]

st.title("Silicon Ray Optics Laboratory")
st.caption(
    "One continuous simulation: incidence → reflection → refraction → "
    "internal reflection → second reflected beam → beam separation → critical angle."
)

# ============================================================
# Live results
# ============================================================
if d["r"] is not None:
    r_deg = d["r"]
    gap = d["gap"]
    horizontal = d["horizontal"]
    back_x = d["back_x"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Incidence angle, i", f"{i_deg:.2f}°")
    c2.metric("Refracted angle, r", f"{r_deg:.2f}°")
    c3.metric("Perpendicular gap", f"{gap:.2f} mm")
    c4.metric("Horizontal separation", f"{horizontal:.2f} mm")
    c5.metric("Critical angle", f"{critical:.2f}°")
else:
    st.error("No refracted ray exists for this configuration.")
    st.stop()

# ============================================================
# Main ray diagram
# ============================================================
i = math.radians(i_deg)
r = math.radians(r_deg)

# Geometry:
# front surface y=0
# back surface y=-t
# incident point = (0,0)
# refracted ray reaches back at x=back_x
# after internal reflection it reaches front at x=2*back_x
x_back = back_x
x_exit = 2 * back_x

# Choose view scale so changes remain obvious.
incident_len = max(18, 0.65 * (t + abs(x_exit) + 20))
exit_len = incident_len
inside_margin = max(5, 0.12 * t)

x_inc = -incident_len * math.sin(i)
y_inc = incident_len * math.cos(i)

x_front_ref = incident_len * math.sin(i)
y_front_ref = incident_len * math.cos(i)

# The reflected rays are parallel. Their perpendicular separation
# is gap = horizontal * cos(i).
# We draw a perpendicular connector between them.
# Direction vector along the reflected ray = (sin i, cos i).
# Unit perpendicular = (cos i, -sin i).
perp_x = gap * math.cos(i)
perp_y = -gap * math.sin(i)

# Start point on front reflected beam, and end point on back reflected beam.
# Choose the connector centred near the top right for visibility.
connector_start_x = x_exit + 0.18 * exit_len * math.sin(i)
connector_start_y = 0.18 * exit_len * math.cos(i)
connector_end_x = connector_start_x + perp_x
connector_end_y = connector_start_y + perp_y

# For readability, keep connector close to the actual two rays.
# Project the start onto the front reflected ray using a distance s.
s = min(exit_len * 0.45, max(5, 0.20 * (t + abs(x_exit) + 20)))
connector_start_x = s * math.sin(i)
connector_start_y = s * math.cos(i)
connector_end_x = connector_start_x + perp_x
connector_end_y = connector_start_y + perp_y

fig = go.Figure()

# Silicon slab
x_left = min(x_inc, -20) - 5
x_right = max(x_exit + exit_len * math.sin(i), 20) + 5

fig.add_shape(
    type="rect",
    x0=x_left, x1=x_right, y0=-t, y1=0,
    fillcolor="rgba(50,130,200,0.11)",
    line=dict(color="rgba(80,80,80,0.7)", width=1.5)
)

# Surface lines
fig.add_trace(go.Scatter(
    x=[x_left, x_right], y=[0, 0],
    mode="lines", line=dict(color="black", width=3),
    name="Front surface", hoverinfo="skip"
))
fig.add_trace(go.Scatter(
    x=[x_left, x_right], y=[-t, -t],
    mode="lines", line=dict(color="black", width=3),
    name="Back surface", hoverinfo="skip"
))

# Normal at the point of incidence
normal_len = max(10, 0.30 * t)
fig.add_trace(go.Scatter(
    x=[0, 0], y=[-normal_len, normal_len],
    mode="lines",
    line=dict(color="grey", width=2, dash="dash"),
    name="Normal",
    hoverinfo="skip"
))

# Incident ray with arrow direction
fig.add_trace(go.Scatter(
    x=[x_inc, 0], y=[y_inc, 0],
    mode="lines+markers",
    line=dict(color="#00A878", width=5),
    marker=dict(size=6),
    name="Incident ray"
))
# Arrow placed near incidence
fig.add_annotation(
    x=x_inc * 0.48, y=y_inc * 0.48,
    ax=x_inc * 0.58, ay=y_inc * 0.58,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.4,
    arrowwidth=3, arrowcolor="#00A878",
)

# Front reflected ray
fig.add_trace(go.Scatter(
    x=[0, x_front_ref], y=[0, y_front_ref],
    mode="lines",
    line=dict(color="#8E44AD", width=5),
    name="Front reflected ray"
))
fig.add_annotation(
    x=x_front_ref * 0.52, y=y_front_ref * 0.52,
    ax=x_front_ref * 0.43, ay=y_front_ref * 0.43,
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.3,
    arrowwidth=2.5, arrowcolor="#8E44AD",
)

# Refracted ray inside silicon
fig.add_trace(go.Scatter(
    x=[0, x_back], y=[0, -t],
    mode="lines",
    line=dict(color="#F2994A", width=5),
    name="Refracted ray"
))

# Internal reflected ray
fig.add_trace(go.Scatter(
    x=[x_back, x_exit], y=[-t, 0],
    mode="lines",
    line=dict(color="#00B8D9", width=5),
    name="Internal reflected ray"
))

# Back reflected ray emerging from front
fig.add_trace(go.Scatter(
    x=[x_exit, x_exit + exit_len * math.sin(i)],
    y=[0, exit_len * math.cos(i)],
    mode="lines",
    line=dict(color="#E74C78", width=5),
    name="Back reflected ray"
))
fig.add_annotation(
    x=x_exit + exit_len * 0.48 * math.sin(i),
    y=exit_len * 0.48 * math.cos(i),
    ax=x_exit + exit_len * 0.39 * math.sin(i),
    ay=exit_len * 0.39 * math.cos(i),
    xref="x", yref="y", axref="x", ayref="y",
    showarrow=True, arrowhead=3, arrowsize=1.3,
    arrowwidth=2.5, arrowcolor="#E74C78",
)

# Back surface transmitted ray
# A physically complete diagram includes the transmitted component at
# the rear interface. It is shown dashed because the focus is the
# reflected return path.
R_back = d["R_back"]
if R_back < 0.999:
    # At the back surface, transmitted angle into air is the same as i
    # because the two outside media are both air.
    tx_end = x_back + max(8, 0.35 * t) * math.sin(i)
    ty_end = -t - max(8, 0.35 * t) * math.cos(i)
    fig.add_trace(go.Scatter(
        x=[x_back, tx_end], y=[-t, ty_end],
        mode="lines",
        line=dict(color="rgba(80,80,80,0.55)", width=3, dash="dash"),
        name="Back surface transmitted ray"
    ))

# Perpendicular gap connector
fig.add_trace(go.Scatter(
    x=[connector_start_x, connector_end_x],
    y=[connector_start_y, connector_end_y],
    mode="lines+markers",
    line=dict(color="black", width=3, dash="dot"),
    marker=dict(size=7),
    name="Perpendicular gap"
))

fig.add_annotation(
    x=(connector_start_x + connector_end_x) / 2,
    y=(connector_start_y + connector_end_y) / 2,
    text=f"<b>⊥ Gap = {gap:.2f} mm</b>",
    showarrow=False,
    bgcolor="white",
    bordercolor="black",
    borderwidth=1,
    font=dict(size=15),
)

# Horizontal separation marker on the surface
fig.add_trace(go.Scatter(
    x=[0, x_exit], y=[0, 0],
    mode="lines",
    line=dict(color="rgba(40,40,40,0.55)", width=2, dash="dot"),
    name="Horizontal separation"
))

fig.add_annotation(
    x=x_exit / 2,
    y=0.0,
    text=f"2t tan(r) = {horizontal:.2f} mm",
    showarrow=False,
    yshift=20,
    bgcolor="rgba(255,255,255,0.9)",
)

# Angle arcs using line segments
arc_radius = max(4, min(9, 0.18 * t))

# Incident angle arc from normal to incident direction
arc_theta = [math.radians(a) for a in
             [90 + j * (i_deg / 30) for j in range(31)]]
# Easier visual: centre at (0,0), angle measured from +y.
arc_x = [arc_radius * math.sin(a) for a in arc_theta]
arc_y = [arc_radius * math.cos(a) for a in arc_theta]
fig.add_trace(go.Scatter(
    x=arc_x, y=arc_y,
    mode="lines", line=dict(color="#00A878", width=2),
    showlegend=False, hoverinfo="skip"
))

# Refracted angle arc
rr = [math.radians(a) for a in
      [j * (r_deg / 30) for j in range(31)]]
arc_rx = [arc_radius * math.sin(a) for a in rr]
arc_ry = [-arc_radius * math.cos(a) for a in rr]
fig.add_trace(go.Scatter(
    x=arc_rx, y=arc_ry,
    mode="lines", line=dict(color="#F2994A", width=2),
    showlegend=False, hoverinfo="skip"
))

if show_labels:
    fig.add_annotation(
        x=-arc_radius * 0.45, y=arc_radius * 0.65,
        text=f"<b>i = {i_deg:.2f}°</b>",
        showarrow=False
    )
    fig.add_annotation(
        x=arc_radius * 0.45, y=-arc_radius * 0.65,
        text=f"<b>r = {r_deg:.2f}°</b>",
        showarrow=False
    )
    fig.add_annotation(
        x=0, y=normal_len * 0.75,
        text="<b>Normal</b>",
        showarrow=False,
        xshift=35
    )
    fig.add_annotation(
        x=x_left + 4, y=-t / 2,
        text=f"<b>Silicon</b><br>t = {t:.2f} mm",
        showarrow=False,
        font=dict(size=14)
    )
    fig.add_annotation(
        x=x_back, y=-t,
        text="Internal reflection point",
        showarrow=False,
        yshift=-25
    )

fig.update_layout(
    height=760,
    margin=dict(l=25, r=25, t=55, b=35),
    xaxis=dict(
        title="Distance parallel to surface (mm)",
        zeroline=False,
        showgrid=True,
    ),
    yaxis=dict(
        title="Distance normal to surface (mm)",
        zeroline=False,
        showgrid=True,
        scaleanchor="x",
        scaleratio=1,
    ),
    legend=dict(
        orientation="h",
        y=1.035,
        x=0,
        font=dict(size=12)
    ),
    hovermode="closest",
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False, "scrollZoom": False},
)

# ============================================================
# Live physics panel
# ============================================================
st.subheader("Live optical quantities")

q1, q2, q3 = st.columns(3)

with q1:
    st.markdown("**Snell's law**")
    st.latex(
        r"r=\sin^{-1}\left(\frac{n_{\rm air}}{n_{\rm Si}}\sin i\right)"
    )
    st.write(
        f"r = sin⁻¹(({n_air:.4f}/{n_si:.4f}) sin({i_deg:.2f}°)) "
        f"= **{r_deg:.2f}°**"
    )

with q2:
    st.markdown("**Internal displacement**")
    st.latex(r"\Delta x=t\tan r")
    st.write(f"Δx = {t:.2f} × tan({r_deg:.2f}°) = **{back_x:.2f} mm**")

with q3:
    st.markdown("**Perpendicular reflected beam gap**")
    st.latex(r"G=2t\tan r\cos i")
    st.write(
        f"G = 2 × {t:.2f} × tan({r_deg:.2f}°) × cos({i_deg:.2f}°) "
        f"= **{gap:.2f} mm**"
    )

# ============================================================
# Critical angle integrated into the same simulation
# ============================================================
st.subheader("Critical angle in the same optical system")

cc1, cc2, cc3 = st.columns(3)
cc1.metric("Critical angle", f"{critical:.2f}°")
cc2.metric("Current angle / critical angle", f"{i_deg / critical:.2f}")
if i_deg < critical:
    cc3.success("Current incidence is below the critical angle: refraction occurs.")
else:
    cc3.warning("Current incidence is at/above the critical angle: total internal reflection occurs.")

st.latex(
    r"\theta_c=\sin^{-1}\left(\frac{n_{\rm air}}{n_{\rm Si}}\right)"
)

st.write(
    f"For nSi = {n_si:.4f} and nair = {n_air:.4f}, "
    f"θc = **{critical:.2f}°**. "
    "As you move the incidence angle through this value, the refraction "
    "part of the same simulation naturally changes into total internal reflection."
)

if show_fresnel:
    st.subheader("Interface optics")

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Front surface R", f"{100*d['R_front']:.2f}%")
    f2.metric("Front surface T", f"{100*d['T_front']:.2f}%")
    f3.metric("Back surface R", f"{100*d['R_back']:.2f}%")
    f4.metric("Back surface T", f"{100*d['T_back']:.2f}%")

st.caption(
    f"λ = {wavelength:.0f} nm  |  nSi = {n_si:.4f}  |  nair = {n_air:.4f}  |  "
    "All geometry updates live when a control is changed."
)
