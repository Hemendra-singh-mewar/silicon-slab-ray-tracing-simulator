# Interactive Silicon Ray Optics Lab v2

A browser based simulator inspired by the supplied silicon ray geometry figure.

## Main modes

### 1. Reflected Beam Gap

The simulation shows:

- incident beam
- front surface reflected beam
- refracted beam inside silicon
- internal reflection from the back surface
- back reflected beam emerging from the front surface
- sample thickness
- incident and refracted angles
- horizontal internal shift
- perpendicular gap between the two reflected beams
- optical path length

For a parallel slab:

r = sin^-1[(n_air / n_silicon) sin(i)]

The horizontal displacement after the internal round trip is:

2t tan(r)

The perpendicular separation between the two emergent parallel beams is:

Gap = 2t tan(r) cos(i)

Example:

t = 29.7 mm
i = 45 degrees
n_air = 1.0003
n_silicon = 3.48

gives approximately:

r = 11.72 degrees
2t tan(r) = 12.33 mm
Gap = 8.72 mm

### 2. Critical Angle

The second mode switches to a silicon to air interface.

The ray starts inside silicon and its angle is increased towards:

theta_c = sin^-1(n_air / n_silicon)

For silicon n = 3.48 and air n = 1.0003, the critical angle is approximately 16.69 degrees.

The animation demonstrates:

1. refraction below the critical angle
2. the refracted ray becoming tangent to the interface at the critical angle
3. total internal reflection above the critical angle

## Run

Open index.html in a browser.

## GitHub Pages

Create a GitHub repository, upload the four files, then enable Settings -> Pages -> Deploy from branch -> main -> root.

No Python server is required.

## Future research features

- Fresnel Rs and Rp
- reflected beam intensity
- polarisation
- multiple internal reflections
- wavelength dependent silicon refractive index
- temperature dependent refractive index
- detector plane
- beam footprint
- finite beam diameter
- etalon interference
