
import math
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Silicon Ray Optics Simulator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def fresnel_unpolarised(n1, n2, theta_i_deg):
    """Power reflectance/transmittance for a lossless interface."""
    theta_i = math.radians(theta_i_deg)
    sin_t = (n1 / n2) * math.sin(theta_i)

    if abs(sin_t) > 1.0:
        return 1.0, 0.0, None, None, True

    theta_t = math.asin(clamp(sin_t, -1.0, 1.0))
    ci = math.cos(theta_i)
    ct = math.cos(theta_t)

    rs = ((n1 * ci - n2 * ct) / (n1 * ci + n2 * ct)) ** 2
    rp = ((n1 * ct - n2 * ci) / (n1 * ct + n2 * ci)) ** 2

    R = 0.5 * (rs + rp)
    T = 1.0 - R
    return R, T, rs, rp, False

def critical_angle(n_dense, n_rare):
    if n_dense <= n_rare:
        return None
    return math.degrees(math.asin(clamp(n_rare / n_dense, 0.0, 1.0)))

def ray_end(start, angle_from_normal_deg, length, direction_sign=1):
    """
    Surface is horizontal. Positive x is to the right, positive y upward.
    For a ray travelling downwards, y contribution is negative.
    angle is measured from the vertical normal.
    """
    a = math.radians(angle_from_normal_deg)
    dx = direction_sign * length * math.sin(a)
    return start[0] + dx, start[1]

def add_arrow(fig, x0, y0, x1, y1, name, width=4):
    fig.add_trace(
        go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            name=name,
            line=dict(width=width),
            hoverinfo="name",
        )
    )
    # Plotly arrow annotation
    fig.add_annotation(
        x=x1,
        y=y1,
        ax=x0,
        ay=y0,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.2,
        arrowwidth=2,
        text="",
    )

# ------------------------------------------------------------
# Session defaults
# ------------------------------------------------------------
PRESETS = {
    "Small sample": {
        "thickness": 29.7,
        "diameter": 42.0,
        "incidence": 45.0,
        "n_si": 3.48,
        "n_air": 1.0003,
        "wavelength": 1550.0,
    },
    "Large sample": {
        "thickness": 180.0,
        "diameter": 450.0,
        "incidence": 45.0,
        "n_si": 3.48,
        "n_air": 1.0003,
        "wavelength": 1550.0,
    },
}

if "preset" not in st.session_state:
    st.session_state.preset = "Small sample"

if "loaded_preset" not in st.session_state:
    st.session_state.loaded_preset = None

PRESET_NAMES = ["Small sample", "Large sample", "Custom"]

# Initialise values from the small sample only once.
if "thickness" not in st.session_state:
    p0 = PRESETS["Small sample"]
    st.session_state.thickness = p0["thickness"]
    st.session_state.diameter = p0["diameter"]
    st.session_state.incidence = p0["incidence"]
    st.session_state.n_si = p0["n_si"]
    st.session_state.n_air = p0["n_air"]
    st.session_state.wavelength = p0["wavelength"]

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.title("Simulation")
    st.caption("Live silicon slab ray tracing")

    preset = st.radio(
        "Sample preset",
        PRESET_NAMES,
        index=PRESET_NAMES.index(st.session_state.preset),
        key="preset_radio",
    )

    # Selecting one of the two presets loads its recommended values.
    # Selecting Custom keeps the current values and allows the user
    # to edit them freely.
    if preset != st.session_state.preset:
        st.session_state.preset = preset

        if preset in PRESETS:
            p = PRESETS[preset]
            st.session_state.thickness = p["thickness"]
            st.session_state.diameter = p["diameter"]
            st.session_state.incidence = p["incidence"]
            st.session_state.n_si = p["n_si"]
            st.session_state.n_air = p["n_air"]
            st.session_state.wavelength = p["wavelength"]

    st.divider()
    st.subheader("Geometry")

    st.subheader("Geometry")

    if st.session_state.preset == "Custom":
        st.info("Custom mode: all parameters below are user adjustable.")

    st.slider(
        "Silicon thickness, t (mm)",
        min_value=1.0,
        max_value=200.0,
        value=float(st.session_state.thickness),
        step=0.1,
        key="thickness",
    )

    st.slider(
        "External incidence angle, i (°)",
        min_value=0.0,
        max_value=89.9,
        value=float(st.session_state.incidence),
        step=0.1,
        key="incidence",
    )

    st.number_input(
        "Sample diameter (mm)",
        min_value=1.0,
        max_value=1000.0,
        value=float(st.session_state.diameter),
        step=1.0,
        key="diameter",
    )

    st.divider()
    st.subheader("Optical properties")

    st.number_input(
        "Silicon refractive index, nSi",
        min_value=1.0001,
        max_value=10.0,
        value=float(st.session_state.n_si),
        step=0.0001,
        format="%.4f",
        key="n_si",
    )

    st.number_input(
        "Air refractive index, nair",
        min_value=1.0,
        max_value=2.0,
        value=float(st.session_state.n_air),
        step=0.0001,
        format="%.4f",
        key="n_air",
    )

    st.number_input(
        "Wavelength (nm)",
        min_value=100.0,
        max_value=10000.0,
        value=float(st.session_state.wavelength),
        step=1.0,
        key="wavelength",
    )

    st.divider()
    polarisation = st.selectbox(
        "Polarisation for Fresnel values",
        ["Unpolarised", "s polarisation", "p polarisation"],
        index=0,
    )

    show_normals = st.checkbox("Show surface normals", True)
    show_labels = st.checkbox("Show optical labels", True)
    show_dimensions = st.checkbox("Show dimensions", True)

# ------------------------------------------------------------
# Physics
# ------------------------------------------------------------
t = float(st.session_state.thickness)
i = float(st.session_state.incidence)
n_si = float(st.session_state.n_si)
n_air = float(st.session_state.n_air)
wavelength = float(st.session_state.wavelength)

# Snell: air -> silicon
sin_r = (n_air / n_si) * math.sin(math.radians(i))
sin_r = clamp(sin_r, -1.0, 1.0)
r = math.degrees(math.asin(sin_r))

theta_c = critical_angle(n_si, n_air)

# Back interface: silicon -> air
tir = theta_c is not None and r > theta_c + 1e-10
critical_condition = theta_c is not None and abs(r - theta_c) <= 1e-10

R_front, T_front, Rs_front, Rp_front, _ = fresnel_unpolarised(
    n_air, n_si, i
)

R_back, T_back, Rs_back, Rp_back, back_tir = fresnel_unpolarised(
    n_si, n_air, r
)

if polarisation == "Unpolarised":
    R_display = R_front
    T_display = T_front
elif polarisation == "s polarisation":
    R_display = Rs_front
    T_display = 1.0 - R_display
else:
    R_display = Rp_front
    T_display = 1.0 - R_display

# Internal displacement and perpendicular gap
dx = t * math.tan(math.radians(r))
horizontal_separation = 2.0 * dx
perpendicular_gap = horizontal_separation * math.cos(math.radians(i))

# Refraction at the back surface when not TIR
if not tir:
    # For silicon -> air, the transmitted angle is i by reversibility.
    back_transmitted_angle = i
else:
    back_transmitted_angle = None

# ------------------------------------------------------------
# Main page
# ------------------------------------------------------------
st.title("Silicon Ray Optics Simulator")
st.caption(
    "Live ray tracing of a plane parallel silicon slab. "
    "All geometry and optical quantities update immediately when a control changes."
)

# Status
if tir:
    status = "🔴 Total internal reflection at the back silicon → air surface"
    status_detail = (
        f"Internal incidence r = {r:.3f}° > critical angle θc = {theta_c:.3f}°."
    )
elif critical_condition:
    status = "🟠 Critical condition at the back silicon → air surface"
    status_detail = (
        f"Internal incidence r = {r:.3f}° = critical angle θc = {theta_c:.3f}°. "
        "The transmitted ray is tangent to the back surface."
    )
else:
    status = "🟢 Transmission through the back silicon → air surface"
    status_detail = (
        f"Internal incidence r = {r:.3f}° < critical angle θc = {theta_c:.3f}°."
    )

st.info(f"**{status}**  \n{status_detail}")

# Metric row
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("External angle, i", f"{i:.2f}°")
c2.metric("Internal angle, r", f"{r:.2f}°")
c3.metric("Critical angle, θc", f"{theta_c:.2f}°" if theta_c else "N/A")
c4.metric("Internal displacement, Δx", f"{dx:.2f} mm")
c5.metric("Perpendicular beam gap, G", f"{perpendicular_gap:.2f} mm")

# ------------------------------------------------------------
# Ray diagram
# ------------------------------------------------------------
st.subheader("Live optical geometry")

# Keep the slab visible without making the plot unreadably wide.
ray_height = max(20.0, 0.65 * t)
x_span = max(80.0, 2.6 * t * math.tan(math.radians(max(r, 8.0))) + 35.0)

fig = go.Figure()

# Silicon slab
fig.add_shape(
    type="rect",
    x0=-x_span / 2,
    x1=x_span / 2,
    y0=-t,
    y1=0,
    fillcolor="rgba(100,150,220,0.12)",
    line=dict(color="rgba(70,100,150,0.7)", width=2),
)

# Surfaces
fig.add_trace(
    go.Scatter(
        x=[-x_span / 2, x_span / 2],
        y=[0, 0],
        mode="lines",
        name="Front surface",
        line=dict(width=3),
    )
)
fig.add_trace(
    go.Scatter(
        x=[-x_span / 2, x_span / 2],
        y=[-t, -t],
        mode="lines",
        name="Back surface",
        line=dict(width=3),
    )
)

# Incident ray, ending at origin
inc_len = max(35.0, 0.9 * ray_height)
inc_start = (
    -inc_len * math.sin(math.radians(i)),
    inc_len * math.cos(math.radians(i)),
)
add_arrow(fig, inc_start[0], inc_start[1], 0, 0, "Incident ray")

# Front reflected ray
ref_end = (
    inc_len * math.sin(math.radians(i)),
    inc_len * math.cos(math.radians(i)),
)
add_arrow(fig, 0, 0, ref_end[0], ref_end[1], "Front reflected ray")

# Refracted ray to back surface
back_x = dx
add_arrow(fig, 0, 0, back_x, -t, "Refracted ray inside silicon")

# Back interaction
if tir:
    # Internal reflected ray back to front
    add_arrow(fig, back_x, -t, 0, 0, "Internal reflected ray")

    # Emerging reflected ray from front, parallel to front reflection
    out_end = (
        2 * dx + inc_len * math.sin(math.radians(i)),
        inc_len * math.cos(math.radians(i)),
    )
    add_arrow(fig, 0, 0, out_end[0], out_end[1], "Back reflected beam")
else:
    # Transmitted ray exits back surface, direction reverses symmetrically
    out_len = max(30.0, 0.75 * ray_height)
    trans_end = (
        back_x + out_len * math.sin(math.radians(i)),
        -t - out_len * math.cos(math.radians(i)),
    )
    add_arrow(fig, back_x, -t, trans_end[0], trans_end[1], "Back transmitted ray")

# Normals
if show_normals:
    normal_len = max(8.0, 0.25 * ray_height)
    fig.add_trace(
        go.Scatter(
            x=[0, 0],
            y=[-normal_len, normal_len],
            mode="lines",
            name="Front normal",
            line=dict(dash="dash", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[back_x, back_x],
            y=[-t - normal_len, -t + normal_len],
            mode="lines",
            name="Back normal",
            line=dict(dash="dash", width=2),
        )
    )

# Perpendicular gap dimension between the two emerging reflected beams.
# Draw a line normal to the beam direction at a convenient height.
if tir and show_dimensions:
    dim_y = min(0.72 * ray_height, max(5.0, 0.55 * ray_height))
    # x coordinate of front beam at dim_y
    x_front = dim_y * math.tan(math.radians(i))
    # x coordinate of back-reflected beam at same y
    x_back = 2 * dx + dim_y * math.tan(math.radians(i))

    # Perpendicular vector to beam direction: (cos i, -sin i)
    # Start at front beam and end at back beam.
    # The signed horizontal difference is 2dx.
    ux = math.cos(math.radians(i))
    uy = -math.sin(math.radians(i))
    # We need a segment of length G. The vector from front to back is horizontal,
    # projected onto the perpendicular direction. Use a construction segment.
    # For clarity, draw the horizontal separation and a perpendicular dimension.
    fig.add_trace(
        go.Scatter(
            x=[x_front, x_back],
            y=[dim_y, dim_y],
            mode="lines",
            name="Horizontal beam separation",
            line=dict(dash="dot", width=2),
        )
    )
    fig.add_annotation(
        x=(x_front + x_back) / 2,
        y=dim_y + 0.8,
        text=f"2Δx = {horizontal_separation:.2f} mm",
        showarrow=False,
    )

    # Perpendicular gap marker using the actual perpendicular distance.
    # Pick midpoint and construct +/- G/2 along the perpendicular direction.
    mx = (x_front + x_back) / 2
    my = dim_y
    gx = (perpendicular_gap / 2) * ux
    gy = (perpendicular_gap / 2) * uy
    fig.add_trace(
        go.Scatter(
            x=[mx - gx, mx + gx],
            y=[my - gy, my + gy],
            mode="lines",
            name="Perpendicular gap G",
            line=dict(width=4),
        )
    )
    fig.add_annotation(
        x=mx + gx,
        y=my + gy,
        ax=mx - gx,
        ay=my - gy,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1,
        arrowwidth=2,
        text="",
    )
    fig.add_annotation(
        x=mx,
        y=my - max(2.0, 0.04 * ray_height),
        text=f"G = {perpendicular_gap:.2f} mm",
        showarrow=False,
    )

if show_labels:
    fig.add_annotation(
        x=-0.38 * x_span,
        y=0.12 * ray_height,
        text="<b>AIR</b>",
        showarrow=False,
    )
    fig.add_annotation(
        x=-0.38 * x_span,
        y=-0.5 * t,
        text="<b>SILICON</b>",
        showarrow=False,
    )
    fig.add_annotation(
        x=0,
        y=0.08 * ray_height,
        text=f"i = {i:.2f}°",
        showarrow=False,
    )
    fig.add_annotation(
        x=0.55 * dx,
        y=-0.48 * t,
        text=f"r = {r:.2f}°",
        showarrow=False,
    )
    fig.add_annotation(
        x=-0.25 * x_span,
        y=0.96 * ray_height,
        text="Incident direction →",
        showarrow=False,
    )

fig.update_layout(
    height=650,
    margin=dict(l=20, r=20, t=20, b=20),
    xaxis=dict(
        title="Distance parallel to surface (mm)",
        zeroline=False,
        scaleanchor="y",
        scaleratio=1,
    ),
    yaxis=dict(
        title="Distance normal to surface (mm)",
        zeroline=False,
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    hovermode="closest",
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# Optical quantities
# ------------------------------------------------------------
st.subheader("Live optical quantities")

q1, q2, q3 = st.columns(3)

with q1:
    st.markdown("### Snell's law")
    st.latex(r"\sin r = \frac{n_{\mathrm{air}}}{n_{\mathrm{Si}}}\sin i")
    st.write(
        f"r = sin⁻¹(({n_air:.4f}/{n_si:.4f}) sin({i:.2f}°)) = **{r:.3f}°**"
    )

with q2:
    st.markdown("### Critical angle")
    st.latex(r"\theta_c=\sin^{-1}\left(\frac{n_{\mathrm{air}}}{n_{\mathrm{Si}}}\right)")
    st.write(
        f"θc = **{theta_c:.3f}°** for the silicon → air interface."
    )
    st.write(
        f"Internal incidence / critical angle = **{r/theta_c:.4f}**"
    )

with q3:
    st.markdown("### Beam separation")
    st.latex(r"\Delta x=t\tan r")
    st.latex(r"G=2t\tan r\cos i")
    st.write(f"Δx = **{dx:.3f} mm**")
    st.write(f"G = **{perpendicular_gap:.3f} mm**")

# ------------------------------------------------------------
# Fresnel section
# ------------------------------------------------------------
st.subheader("Interface optics")

fc1, fc2, fc3, fc4 = st.columns(4)

fc1.metric("Front surface R", f"{100 * R_display:.2f}%")
fc2.metric("Front surface T", f"{100 * T_display:.2f}%")

if tir:
    back_R_display = 1.0
    back_T_display = 0.0
elif polarisation == "Unpolarised":
    back_R_display = R_back
    back_T_display = T_back
elif polarisation == "s polarisation":
    back_R_display = Rs_back
    back_T_display = 1.0 - Rs_back
else:
    back_R_display = Rp_back
    back_T_display = 1.0 - Rp_back

fc3.metric("Back surface R", f"{100 * back_R_display:.2f}%")
fc4.metric("Back surface T", f"{100 * back_T_display:.2f}%")

st.caption(
    f"λ = {wavelength:.0f} nm | nSi = {n_si:.4f} | nair = {n_air:.4f} | "
    f"Fresnel model: {polarisation}. "
    "The current model assumes a lossless, planar, uncoated silicon slab."
)

# Detailed Fresnel values
with st.expander("Show s and p Fresnel components"):
    a, b, c, d = st.columns(4)
    a.metric("Front Rs", f"{100 * Rs_front:.2f}%")
    b.metric("Front Rp", f"{100 * Rp_front:.2f}%")
    if Rs_back is not None:
        c.metric("Back Rs", f"{100 * (1.0 if tir else Rs_back):.2f}%")
        d.metric("Back Rp", f"{100 * (1.0 if tir else Rp_back):.2f}%")

# ------------------------------------------------------------
# Physics notes
# ------------------------------------------------------------
with st.expander("What determines TIR?"):
    st.markdown(
        """
**The critical angle is an internal angle.**

For the silicon → air back surface:

\[
r < \theta_c \quad \Rightarrow \quad \text{transmission}
\]

\[
r = \theta_c \quad \Rightarrow \quad \text{critical condition}
\]

\[
r > \theta_c \quad \Rightarrow \quad \text{total internal reflection}
\]

The external angle \(i\) is first converted into the internal angle \(r\) using Snell's law.
"""
    )

with st.expander("Model assumptions"):
    st.markdown(
        """
- Plane parallel silicon slab.
- Air and silicon are treated as lossless, non absorbing media.
- Refractive indices are entered directly by the user.
- Fresnel values use the selected polarisation.
- No surface coating or oxide layer is included.
- The wavelength is displayed and can be used with a wavelength dependent refractive index in a future version.
"""
    )

st.divider()
st.caption("Silicon Ray Optics Simulator • Live geometry • Snell's law • Fresnel reflection • Critical angle • TIR")
