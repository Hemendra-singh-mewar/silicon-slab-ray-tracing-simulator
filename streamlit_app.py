import math
import streamlit as st
import plotly.graph_objects as go


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Silicon Ray Optics Simulator",
    page_icon="🔬",
    layout="wide",
)


# ============================================================
# PRESETS
# ============================================================

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
        "thickness": 100.0,
        "diameter": 100.0,
        "incidence": 45.0,
        "n_si": 3.48,
        "n_air": 1.0003,
        "wavelength": 1550.0,
    },
}


# ============================================================
# SESSION STATE
# ============================================================

if "preset" not in st.session_state:
    st.session_state.preset = "Small sample"

if "initialised" not in st.session_state:
    p = PRESETS["Small sample"]

    st.session_state.thickness = p["thickness"]
    st.session_state.diameter = p["diameter"]
    st.session_state.incidence = p["incidence"]
    st.session_state.n_si = p["n_si"]
    st.session_state.n_air = p["n_air"]
    st.session_state.wavelength = p["wavelength"]

    st.session_state.initialised = True


# ============================================================
# FUNCTIONS
# ============================================================

def snell_angle(i_deg, n1, n2):
    """
    Calculate refracted angle using Snell's law.
    Returns None if total internal reflection occurs.
    """
    i_rad = math.radians(i_deg)

    value = (n1 / n2) * math.sin(i_rad)

    if abs(value) > 1:
        return None

    return math.degrees(math.asin(value))


def critical_angle(n_dense, n_rare):
    """
    Critical angle for propagation from dense to rare medium.
    """
    if n_dense <= n_rare:
        return None

    return math.degrees(math.asin(n_rare / n_dense))


def fresnel_coefficients(n1, n2, angle_deg):
    """
    Fresnel power reflection/transmission coefficients.

    Returns:
        Rs, Rp, Ts, Tp
    """

    theta_i = math.radians(angle_deg)

    sin_t = (n1 / n2) * math.sin(theta_i)

    if abs(sin_t) > 1:
        return 1.0, 1.0, 0.0, 0.0

    theta_t = math.asin(sin_t)

    cos_i = math.cos(theta_i)
    cos_t = math.cos(theta_t)

    rs = (
        (n1 * cos_i - n2 * cos_t)
        / (n1 * cos_i + n2 * cos_t)
    )

    rp = (
        (n2 * cos_i - n1 * cos_t)
        / (n2 * cos_i + n1 * cos_t)
    )

    Rs = rs ** 2
    Rp = rp ** 2

    Ts = 1 - Rs
    Tp = 1 - Rp

    return Rs, Rp, Ts, Tp


def add_arrow(fig, x0, y0, x1, y1, colour, label=None):
    """
    Add a ray with an arrow indicating propagation direction.
    """

    fig.add_trace(
        go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line=dict(
                color=colour,
                width=3,
            ),
            name=label if label else "",
            showlegend=bool(label),
        )
    )

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
        arrowcolor=colour,
        text="",
    )


def add_normal(fig, x, y, length, label):
    """
    Add a surface normal.
    """

    fig.add_trace(
        go.Scatter(
            x=[x, x],
            y=[y - length, y + length],
            mode="lines",
            line=dict(
                color="orange",
                width=2,
                dash="dash",
            ),
            name=label,
            showlegend=True,
        )
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("Simulation")
    st.caption("Live silicon slab ray tracing")

    st.subheader("Sample preset")

    preset = st.radio(
        "Choose sample",
        ["Small sample", "Large sample", "Custom"],
        index=["Small sample", "Large sample", "Custom"].index(
            st.session_state.preset
        ),
    )

    # Load preset only when the user actually selects it
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

    # ========================================================
    # GEOMETRY
    # ========================================================

    st.subheader("Geometry")

    st.session_state.thickness = st.slider(
        "Silicon thickness, t (mm)",
        min_value=1.0,
        max_value=250.0,
        value=float(st.session_state.thickness),
        step=0.1,
    )

    st.session_state.incidence = st.slider(
        "External incidence angle, i (°)",
        min_value=0.0,
        max_value=89.9,
        value=float(st.session_state.incidence),
        step=0.1,
    )

    st.session_state.diameter = st.number_input(
        "Sample diameter (mm)",
        min_value=1.0,
        max_value=1000.0,
        value=float(st.session_state.diameter),
        step=1.0,
    )

    st.divider()

    # ========================================================
    # OPTICAL PROPERTIES
    # ========================================================

    st.subheader("Optical properties")

    st.session_state.n_si = st.number_input(
        "Silicon refractive index, nSi",
        min_value=1.0001,
        max_value=10.0,
        value=float(st.session_state.n_si),
        step=0.0001,
        format="%.4f",
    )

    st.session_state.n_air = st.number_input(
        "Air refractive index, nair",
        min_value=1.0,
        max_value=2.0,
        value=float(st.session_state.n_air),
        step=0.0001,
        format="%.4f",
    )

    st.session_state.wavelength = st.number_input(
        "Wavelength (nm)",
        min_value=100.0,
        max_value=10000.0,
        value=float(st.session_state.wavelength),
        step=1.0,
    )

    st.divider()

    st.subheader("Display")

    show_normals = st.checkbox(
        "Show surface normals",
        value=True,
    )

    show_dimensions = st.checkbox(
        "Show dimensions",
        value=True,
    )


# ============================================================
# CALCULATIONS
# ============================================================

t = st.session_state.thickness
i = st.session_state.incidence
n_si = st.session_state.n_si
n_air = st.session_state.n_air
wavelength = st.session_state.wavelength

# Air -> silicon
r = snell_angle(
    i,
    n_air,
    n_si,
)

# Silicon -> air critical angle
theta_c = critical_angle(
    n_si,
    n_air,
)


# ============================================================
# MAIN OPTICAL LOGIC
# ============================================================

if r is None:

    # This should not occur for normal air -> silicon incidence,
    # but is kept for completeness.
    tir = True
    r = 90.0

else:

    tir = (
        theta_c is not None
        and r >= theta_c
    )


# Internal lateral displacement to the back surface
internal_shift = t * math.tan(math.radians(r))


# Horizontal separation between the two emerging reflected beams
horizontal_separation = 2 * internal_shift


# Perpendicular separation between reflected beams
perpendicular_gap = (
    horizontal_separation
    * math.cos(math.radians(i))
)


# ============================================================
# FRESNEL COEFFICIENTS
# ============================================================

Rs_front, Rp_front, Ts_front, Tp_front = (
    fresnel_coefficients(
        n_air,
        n_si,
        i,
    )
)

R_front = (Rs_front + Rp_front) / 2
T_front = (Ts_front + Tp_front) / 2


if tir:

    R_back = 1.0
    T_back = 0.0

else:

    Rs_back, Rp_back, Ts_back, Tp_back = (
        fresnel_coefficients(
            n_si,
            n_air,
            r,
        )
    )

    R_back = (Rs_back + Rp_back) / 2
    T_back = (Ts_back + Tp_back) / 2


# ============================================================
# PAGE HEADER
# ============================================================

st.title("Silicon Ray Optics Simulator")

st.caption(
    "Live ray tracing of a plane parallel silicon slab. "
    "All geometry and optical quantities update immediately "
    "when a control changes."
)


# ============================================================
# STATUS
# ============================================================

if tir:

    st.error(
        f"Total internal reflection at the silicon → air back surface. "
        f"Internal incidence angle r = {r:.3f}° "
        f"> critical angle θc = {theta_c:.3f}°."
    )

else:

    st.success(
        f"Transmission through the back silicon → air surface. "
        f"Internal incidence angle r = {r:.3f}° "
        f"< critical angle θc = {theta_c:.3f}°."
    )


# ============================================================
# TOP METRICS
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "External angle, i",
    f"{i:.2f}°",
)

c2.metric(
    "Internal angle, r",
    f"{r:.2f}°",
)

c3.metric(
    "Critical angle, θc",
    f"{theta_c:.2f}°",
)

c4.metric(
    "Internal displacement, Δx",
    f"{internal_shift:.2f} mm",
)

c5.metric(
    "Perpendicular reflected beam gap, G",
    f"{perpendicular_gap:.2f} mm",
)


# ============================================================
# OPTICAL DIAGRAM
# ============================================================

st.subheader("Live optical geometry")


fig = go.Figure()


# ------------------------------------------------------------
# Determine drawing scale
# ------------------------------------------------------------

# Rays need enough space to be clearly visible.
ray_length = max(
    25,
    0.65 * t,
    0.35 * st.session_state.diameter,
)


# ------------------------------------------------------------
# Silicon slab
# ------------------------------------------------------------

sample_half_width = st.session_state.diameter / 2

# Front surface
fig.add_trace(
    go.Scatter(
        x=[
            -sample_half_width,
            sample_half_width,
        ],
        y=[0, 0],
        mode="lines",
        line=dict(
            color="#1f77b4",
            width=4,
        ),
        name="Front surface",
    )
)

# Back surface
fig.add_trace(
    go.Scatter(
        x=[
            -sample_half_width,
            sample_half_width,
        ],
        y=[-t, -t],
        mode="lines",
        line=dict(
            color="#1f77b4",
            width=4,
        ),
        name="Back surface",
    )
)


# ------------------------------------------------------------
# Silicon shaded region
# ------------------------------------------------------------

fig.add_shape(
    type="rect",
    x0=-sample_half_width,
    x1=sample_half_width,
    y0=-t,
    y1=0,
    fillcolor="rgba(100,150,220,0.12)",
    line=dict(width=0),
)


# ------------------------------------------------------------
# Incident ray
# ------------------------------------------------------------

i_rad = math.radians(i)

incident_start_x = (
    -ray_length * math.sin(i_rad)
)

incident_start_y = (
    ray_length * math.cos(i_rad)
)

add_arrow(
    fig,
    incident_start_x,
    incident_start_y,
    0,
    0,
    "#d62728",
    "Incident ray",
)


# ------------------------------------------------------------
# Front reflected beam
# ------------------------------------------------------------

front_reflected_end_x = (
    ray_length * math.sin(i_rad)
)

front_reflected_end_y = (
    ray_length * math.cos(i_rad)
)

add_arrow(
    fig,
    0,
    0,
    front_reflected_end_x,
    front_reflected_end_y,
    "#ff7f0e",
    "Front reflected beam",
)


# ------------------------------------------------------------
# Refracted ray inside silicon
# ------------------------------------------------------------

r_rad = math.radians(r)

back_x = t * math.tan(r_rad)

add_arrow(
    fig,
    0,
    0,
    back_x,
    -t,
    "#00a878",
    "Refracted ray inside silicon",
)


# ------------------------------------------------------------
# INTERNAL REFLECTED RAY
# ------------------------------------------------------------

if not tir:

    # Reflection at the back surface.
    # x component remains in the same direction.
    # y component changes sign.

    front_return_x = 2 * back_x

else:

    # Same geometric reflection occurs during TIR.
    front_return_x = 2 * back_x


# Internal reflected ray from back to front

add_arrow(
    fig,
    back_x,
    -t,
    front_return_x,
    0,
    "#9467bd",
    "Internal reflection from back surface",
)


# ------------------------------------------------------------
# SECOND REFLECTED BEAM
# ------------------------------------------------------------

# The ray emerges from the front surface at x = 2 t tan(r)
#
# Its external angle is again i because the slab is plane parallel.

second_reflected_end_x = (
    front_return_x
    + ray_length * math.sin(i_rad)
)

second_reflected_end_y = (
    ray_length * math.cos(i_rad)
)

add_arrow(
    fig,
    front_return_x,
    0,
    second_reflected_end_x,
    second_reflected_end_y,
    "#e377c2",
    "Back reflected beam",
)


# ------------------------------------------------------------
# TRANSMITTED BEAM THROUGH BACK SURFACE
# ------------------------------------------------------------

if not tir:

    transmission_length = ray_length * 0.75

    transmitted_end_x = (
        back_x
        + transmission_length * math.sin(r_rad)
    )

    transmitted_end_y = (
        -t
        - transmission_length * math.cos(r_rad)
    )

    add_arrow(
        fig,
        back_x,
        -t,
        transmitted_end_x,
        transmitted_end_y,
        "#2ca02c",
        "Back transmitted beam",
    )


# ============================================================
# NORMALS
# ============================================================

if show_normals:

    normal_length = max(
        5,
        min(12, t * 0.25),
    )

    add_normal(
        fig,
        0,
        0,
        normal_length,
        "Front normal",
    )

    add_normal(
        fig,
        back_x,
        -t,
        normal_length,
        "Back normal",
    )


# ============================================================
# GAP INDICATOR
# ============================================================

if show_dimensions:

    # Draw perpendicular distance between the two reflected beams.
    #
    # The two beams are parallel and separated horizontally by:
    #
    #     2 t tan(r)
    #
    # Their perpendicular separation is:
    #
    #     G = 2 t tan(r) cos(i)

    gap_x1 = front_reflected_end_x * 0.55
    gap_y1 = front_reflected_end_y * 0.55

    gap_x2 = (
        front_return_x
        + ray_length * math.sin(i_rad) * 0.55
    )

    gap_y2 = (
        ray_length * math.cos(i_rad) * 0.55
    )

    # Short perpendicular connector.
    #
    # This is drawn between equivalent positions on the two
    # parallel reflected beams.

    fig.add_trace(
        go.Scatter(
            x=[gap_x1, gap_x2],
            y=[gap_y1, gap_y2],
            mode="lines",
            line=dict(
                color="#444444",
                width=2,
                dash="dot",
            ),
            name="Perpendicular beam gap",
        )
    )

    fig.add_annotation(
        x=(gap_x1 + gap_x2) / 2,
        y=(gap_y1 + gap_y2) / 2,
        text=f"G = {perpendicular_gap:.2f} mm",
        showarrow=False,
        font=dict(size=14),
        bgcolor="white",
    )


# ============================================================
# ANGLE LABELS
# ============================================================

fig.add_annotation(
    x=0,
    y=3,
    text=f"i = {i:.2f}°",
    showarrow=False,
)

fig.add_annotation(
    x=back_x * 0.45,
    y=-t * 0.45,
    text=f"r = {r:.2f}°",
    showarrow=False,
)


# ============================================================
# SURFACE LABELS
# ============================================================

fig.add_annotation(
    x=-sample_half_width * 0.75,
    y=2.5,
    text="AIR",
    showarrow=False,
    font=dict(size=13),
)

fig.add_annotation(
    x=-sample_half_width * 0.75,
    y=-t / 2,
    text="SILICON",
    showarrow=False,
    font=dict(size=13),
)


# ============================================================
# LAYOUT
# ============================================================

x_margin = max(
    40,
    0.8 * st.session_state.diameter,
    1.5 * horizontal_separation,
)

y_top = ray_length * 1.15
y_bottom = -t - ray_length * 0.9

fig.update_layout(
    height=720,
    margin=dict(
        l=40,
        r=40,
        t=50,
        b=50,
    ),
    xaxis=dict(
        title="Distance parallel to surface (mm)",
        range=[
            -x_margin,
            x_margin,
        ],
        zeroline=False,
    ),
    yaxis=dict(
        title="Distance normal to surface (mm)",
        range=[
            y_bottom,
            y_top,
        ],
        scaleanchor="x",
        scaleratio=1,
        zeroline=False,
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),
    hovermode=False,
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# ============================================================
# LIVE OPTICAL QUANTITIES
# ============================================================

st.subheader("Live optical quantities")

col1, col2, col3 = st.columns(3)


# ------------------------------------------------------------
# Snell's law
# ------------------------------------------------------------

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
        f"""
        r = {r:.4f}°
        """
    )

    st.write(
        f"""
        {n_air:.4f} sin({i:.2f}°)
        =
        {n_si:.4f} sin({r:.2f}°)
        """
    )


# ------------------------------------------------------------
# Critical angle
# ------------------------------------------------------------

with col2:

    st.markdown("### Critical angle")

    st.latex(
        r"""
        \theta_c
        =
        \sin^{-1}
        \left(
        \frac{n_{\mathrm{air}}}
        {n_{\mathrm{Si}}}
        \right)
        """
    )

    st.metric(
        "Critical angle",
        f"{theta_c:.4f}°",
    )

    st.write(
        f"Internal angle r = {r:.4f}°"
    )

    if r < theta_c:

        st.success(
            "r < θc: transmission occurs at the back surface."
        )

    elif math.isclose(r, theta_c, abs_tol=1e-6):

        st.warning(
            "r = θc: critical condition."
        )

    else:

        st.error(
            "r > θc: total internal reflection occurs."
        )


# ------------------------------------------------------------
# Beam separation
# ------------------------------------------------------------

with col3:

    st.markdown("### Beam separation")

    st.latex(
        r"""
        \Delta x
        =
        t\tan r
        """
    )

    st.write(
        f"Internal displacement: Δx = {internal_shift:.4f} mm"
    )

    st.latex(
        r"""
        G
        =
        2t\tan r\cos i
        """
    )

    st.metric(
        "Perpendicular gap",
        f"{perpendicular_gap:.4f} mm",
    )


# ============================================================
# INTERFACE OPTICS
# ============================================================

st.subheader("Interface optics")

a, b, c, d = st.columns(4)

with a:
    st.metric(
        "Front surface reflection",
        f"{R_front * 100:.2f}%",
    )

with b:
    st.metric(
        "Front surface transmission",
        f"{T_front * 100:.2f}%",
    )

with c:
    st.metric(
        "Back surface reflection",
        f"{R_back * 100:.2f}%",
    )

with d:
    st.metric(
        "Back surface transmission",
        f"{T_back * 100:.2f}%",
    )


st.caption(
    f"λ = {wavelength:.1f} nm  |  "
    f"nSi = {n_si:.4f}  |  "
    f"nair = {n_air:.4f}  |  "
    f"Sample: {st.session_state.preset}"
)
