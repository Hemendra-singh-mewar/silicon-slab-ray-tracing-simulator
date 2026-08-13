const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const el = id => document.getElementById(id);
const controls = {
  thickness: el("thickness"),
  angle: el("angle"),
  nSi: el("nSi"),
  nAir: el("nAir"),
  showNormals: el("showNormals"),
  showLabels: el("showLabels"),
  showFormula: el("showFormula")
};

let mode = "gap";
let playing = false;
let animationId = null;
let lastTime = 0;
let animationDirection = 1;

function deg(x) { return x * Math.PI / 180; }
function rad(x) { return x * 180 / Math.PI; }
function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }

function resize() {
  const dpr = window.devicePixelRatio || 1;
  const r = canvas.getBoundingClientRect();
  canvas.width = Math.floor(r.width * dpr);
  canvas.height = Math.floor(r.height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

function getValues() {
  const t = Number(controls.thickness.value);
  const i = Number(controls.angle.value);
  const nSi = Number(controls.nSi.value);
  const nAir = Number(controls.nAir.value);
  const r = Math.asin(clamp(nAir / nSi * Math.sin(deg(i)), -1, 1));
  const critical = nSi > nAir ? rad(Math.asin(nAir / nSi)) : NaN;

  // This is the geometry shown in the supplied reference figure:
  // horizontal displacement = 2t tan(r)
  // perpendicular beam gap = horizontal displacement * cos(i)
  const shift = 2 * t * Math.tan(r);
  const gap = Math.abs(shift * Math.cos(deg(i)));
  const internalPath = 2 * t / Math.cos(r);
  const opl = nSi * internalPath;

  return { t, i, nSi, nAir, r: rad(r), critical, shift, gap, internalPath, opl };
}

function updateResults() {
  const v = getValues();

  el("thicknessValue").textContent = `${v.t.toFixed(1)} mm`;
  el("angleValue").textContent = `${v.i.toFixed(1)}°`;
  el("nSiValue").textContent = v.nSi.toFixed(3);
  el("nAirValue").textContent = v.nAir.toFixed(4);

  el("outI").textContent = `${v.i.toFixed(2)}°`;
  el("outR").textContent = `${v.r.toFixed(2)}°`;
  el("outCritical").textContent = Number.isFinite(v.critical) ? `${v.critical.toFixed(2)}°` : "N/A";
  el("outShift").textContent = `${v.shift.toFixed(2)} mm`;
  el("outGap").textContent = `${v.gap.toFixed(2)} mm`;
  el("outOPL").textContent = `${v.opl.toFixed(2)} mm`;

  const status = el("criticalStatus");
  if (v.i >= 89.9) {
    status.textContent = "Grazing incidence limit";
  } else {
    status.textContent = "Air → silicon → air: two reflected beams emerge parallel";
  }
  status.classList.remove("tir");
}

function drawText(s, x, y, size=13, align="left", colour="#26343b") {
  ctx.save();
  ctx.font = `${size}px Georgia, "Times New Roman", serif`;
  ctx.textAlign = align;
  ctx.fillStyle = colour;
  ctx.fillText(s, x, y);
  ctx.restore();
}

function drawLine(a, b, colour="#222", width=2, dash=[]) {
  ctx.save();
  ctx.strokeStyle = colour;
  ctx.lineWidth = width;
  ctx.setLineDash(dash);
  ctx.beginPath();
  ctx.moveTo(a.x, a.y);
  ctx.lineTo(b.x, b.y);
  ctx.stroke();
  ctx.restore();
}

function arrow(a, b, colour, width=2) {
  drawLine(a, b, colour, width);
  const angle = Math.atan2(b.y-a.y, b.x-a.x);
  const s = 8;
  ctx.save();
  ctx.fillStyle = colour;
  ctx.beginPath();
  ctx.moveTo(b.x, b.y);
  ctx.lineTo(b.x-s*Math.cos(angle-Math.PI/6), b.y-s*Math.sin(angle-Math.PI/6));
  ctx.lineTo(b.x-s*Math.cos(angle+Math.PI/6), b.y-s*Math.sin(angle+Math.PI/6));
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawGapMode() {
  const v = getValues();
  const W = canvas.clientWidth;
  const H = canvas.clientHeight;

  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, W, H);

  // Plot region similar to supplied figure
  const x0 = W * 0.10;
  const x1 = W * 0.68;
  const y0 = H * 0.46;
  const slabPx = clamp(H * 0.50, 230, 390);
  const scale = slabPx / v.t;
  const bottom = y0 + slabPx;

  // light grid
  ctx.strokeStyle = "#e3e8eb";
  ctx.lineWidth = 1;
  for (let x=x0; x<x1; x+=70) drawLine({x,y:30},{x,y:H-45},"#e5e9eb",1);
  for (let y=90; y<H-45; y+=70) drawLine({x:x0,y},{x:x1,y},"#e5e9eb",1);

  // slab surfaces
  drawLine({x:x0,y:y0},{x:x1,y:y0},"#111",2);
  drawLine({x:x0,y:bottom},{x:x1,y:bottom},"#111",2);
  drawText("Silicon", x0+20, y0+slabPx*0.54, 13, "left", "#555");

  // Scale display is intentionally geometric rather than exact physical width.
  const hitX = x0 + (x1-x0)*0.40;
  const thetaI = deg(v.i);
  const thetaT = deg(v.r);

  const incidentLength = Math.min(220, (x1-x0)*0.32);
  const frontLength = incidentLength;
  const insideDx = slabPx * Math.tan(thetaT);

  const incidentStart = {
    x: hitX - incidentLength*Math.cos(thetaI),
    y: y0 - incidentLength*Math.sin(thetaI)
  };
  const frontEnd = {
    x: hitX + frontLength*Math.cos(thetaI),
    y: y0 - frontLength*Math.sin(thetaI)
  };

  const backHit = { x: hitX + insideDx, y: bottom };
  const returnFront = { x: hitX + 2*insideDx, y: y0 };
  const backEnd = {
    x: returnFront.x + frontLength*Math.cos(thetaI),
    y: y0 - frontLength*Math.sin(thetaI)
  };

  // Normals
  if (controls.showNormals.checked) {
    drawLine({x:hitX,y:y0-80},{x:hitX,y:bottom+80},"#777",1,[6,5]);
    drawLine({x:returnFront.x,y:y0-80},{x:returnFront.x,y:bottom+80},"#777",1,[6,5]);
  }

  // Rays
  arrow(incidentStart, {x:hitX,y:y0}, "#111dff", 2.5);
  arrow({x:hitX,y:y0}, frontEnd, "#ff1515", 2.5);
  arrow({x:hitX,y:y0}, backHit, "#12df25", 2.5);
  arrow(backHit, returnFront, "#12df25", 2.5);
  arrow(returnFront, backEnd, "#f000ff", 2.5);

  // Gap indicator perpendicular to reflected beams
  const q1 = {
    x: hitX + 70*Math.cos(thetaI),
    y: y0 - 70*Math.sin(thetaI)
  };
  const q2 = {
    x: returnFront.x + 70*Math.cos(thetaI),
    y: y0 - 70*Math.sin(thetaI)
  };
  drawLine(q1,q2,"#777",1,[5,4]);

  if (controls.showLabels.checked) {
    drawText(`i = ${v.i.toFixed(1)}°`, hitX+12, y0-45, 13);
    drawText(`r = ${v.r.toFixed(2)}°`, hitX+18, y0+65, 13);
    drawText("Front reflected beam", frontEnd.x-95, frontEnd.y+42, 13, "left", "#e11");
    drawText("Back reflected beam", backEnd.x-95, backEnd.y+80, 13, "left", "#d000d8");
    drawText("Internal reflection", backHit.x-55, backHit.y-55, 12, "left", "#13b824");
    drawText(`Gap = ${v.gap.toFixed(2)} mm`, (q1.x+q2.x)/2, (q1.y+q2.y)/2-10, 13, "center", "#222");
    drawText(`2t tan(r) = ${v.shift.toFixed(2)} mm`, hitX+10, bottom-20, 12, "left", "#333");

    // thickness bracket
    drawLine({x:hitX-20,y:y0},{x:hitX-20,y:bottom},"#777",1,[5,4]);
    drawText(`t = ${v.t.toFixed(1)} mm`, hitX-34, (y0+bottom)/2, 12, "right", "#555");
  }

  // Right hand equation panel
  const px = W*0.72;
  const py = H*0.24;
  drawText("Gap = 2t tan(r) cos(i)", px, py, 24, "left", "#111");
  drawText("r = sin⁻¹[(n_air / n_silicon) sin(i)]", px, py+42, 17, "left", "#222");
  drawText("Where,", px, py+105, 17, "left", "#111");
  drawText("t = sample thickness", px, py+140, 16, "left", "#222");
  drawText("i = angle of incidence", px, py+172, 16, "left", "#222");
  drawText(`n_air = ${v.nAir.toFixed(4)}`, px, py+204, 16, "left", "#222");
  drawText(`n_silicon = ${v.nSi.toFixed(3)} @ 1550 nm`, px, py+236, 16, "left", "#222");

  if (controls.showLabels.checked) {
    drawText(`Critical angle in silicon = ${v.critical.toFixed(2)}°`, px, py+290, 15, "left", "#0d5f7c");
  }
}

function drawCriticalMode() {
  const v = getValues();
  const W = canvas.clientWidth;
  const H = canvas.clientHeight;
  ctx.fillStyle = "#fff";
  ctx.fillRect(0,0,W,H);

  const interfaceY = H*0.42;
  const cx = W*0.43;
  const left = W*0.12;
  const right = W*0.69;
  const bottom = H*0.86;

  // Regions
  ctx.fillStyle = "#e9f3f7";
  ctx.fillRect(left, interfaceY, right-left, bottom-interfaceY);
  drawLine({x:left,y:interfaceY},{x:right,y:interfaceY},"#111",2);

  drawText("AIR", (left+right)/2, interfaceY-20, 15, "center", "#555");
  drawText("SILICON", (left+right)/2, interfaceY+45, 15, "center", "#47616c");
  drawText(`n₁ = ${v.nSi.toFixed(3)}`, (left+right)/2, interfaceY+67, 13, "center", "#47616c");
  drawText(`n₂ = ${v.nAir.toFixed(4)}`, (left+right)/2, interfaceY-2, 13, "center", "#47616c");

  // Animated angle inside silicon. User slider controls the base angle in critical mode.
  const maxAngle = Math.min(89, v.critical + 18);
  const theta = Math.min(maxAngle, v.i);
  const thetaRad = deg(theta);

  // Normal
  drawLine({x:cx,y:interfaceY-90},{x:cx,y:bottom+10},"#777",1,[6,5]);

  const L = 230;
  const start = {
    x: cx - L*Math.sin(thetaRad),
    y: interfaceY + L*Math.cos(thetaRad)
  };
  const hit = {x:cx,y:interfaceY};

  // Incident ray in silicon
  arrow(start, hit, "#12c92a", 3);

  const thetaC = v.critical;
  const beyond = theta > thetaC + 0.03;

  if (!beyond) {
    // Refracted angle in air
    const s = v.nSi/v.nAir*Math.sin(thetaRad);
    const refracted = Math.asin(clamp(s,-1,1));
    const refrLength = 180;
    const end = {
      x: cx + refrLength*Math.sin(refracted),
      y: interfaceY - refrLength*Math.cos(refracted)
    };
    arrow(hit,end,"#e21b1b",3);

    if (Math.abs(theta-thetaC) < 0.15) {
      drawText("Critical condition: refracted ray grazes the interface", W*0.05, H*0.08, 16, "left", "#9b1515");
    }
  } else {
    // Total internal reflection
    const reflEnd = {
      x: cx + L*Math.sin(thetaRad),
      y: interfaceY + L*Math.cos(thetaRad)
    };
    arrow(hit,reflEnd,"#f000ff",3);
    drawText("TOTAL INTERNAL REFLECTION", W*0.05, H*0.08, 18, "left", "#9b1515");
  }

  if (controls.showLabels.checked) {
    drawText(`θ = ${theta.toFixed(2)}°`, cx+15, interfaceY+95, 14);
    drawText(`θc = ${v.critical.toFixed(2)}°`, cx+15, interfaceY-105, 14, "left", "#0d5f7c");
    drawText(`nSi = ${v.nSi.toFixed(3)}`, right-20, bottom-28, 13, "right");
    drawText(`nAir = ${v.nAir.toFixed(4)}`, right-20, bottom-48, 13, "right");
  }

  // Critical angle scale
  const sx = W*0.76;
  const sy = H*0.30;
  drawText("Critical angle", sx, sy, 20, "left", "#111");
  drawText(`θc = sin⁻¹(nAir / nSi) = ${v.critical.toFixed(2)}°`, sx, sy+35, 14);
  drawText("Move the angle slider or press Animate.", sx, sy+72, 12, "left", "#59666d");

  const barY = sy+115;
  const barW = W*0.19;
  drawLine({x:sx,y:barY},{x:sx+barW,y:barY},"#888",4);
  const marker = sx + barW*clamp(theta/90,0,1);
  ctx.fillStyle = theta >= v.critical ? "#d31b1b" : "#0d6b96";
  ctx.beginPath(); ctx.arc(marker,barY,7,0,Math.PI*2); ctx.fill();
  drawText("0°",sx,barY+25,11);
  drawText(`${v.critical.toFixed(1)}°`,sx+barW*(v.critical/90),barY+25,11,"center","#0d5f7c");
  drawText("90°",sx+barW,barY+25,11,"right");

  const status = el("criticalStatus");
  if (theta < v.critical - 0.15) {
    status.textContent = "Refraction: transmitted ray exits into air";
    status.classList.remove("tir");
  } else if (Math.abs(theta-v.critical) <= 0.15) {
    status.textContent = "At the critical angle: refracted ray grazes the interface";
    status.classList.remove("tir");
  } else {
    status.textContent = "Total internal reflection";
    status.classList.add("tir");
  }
}

function draw() {
  if (mode === "gap") drawGapMode();
  else drawCriticalMode();
}

function updateMode() {
  const gap = mode === "gap";
  document.querySelectorAll(".tab").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
  el("controlTitle").textContent = gap ? "Silicon slab" : "Silicon → air interface";
  el("modeDescription").textContent = gap
    ? "The incident beam enters silicon, reflects from the back surface and exits through the front surface. The front and back reflected beams remain parallel."
    : "The ray now starts inside silicon. Increase the internal incidence angle towards the critical angle and observe the refracted ray become tangent to the surface, followed by total internal reflection.";
  el("formulaPanel").classList.toggle("hidden", !gap || !controls.showFormula.checked);
  el("criticalPanel").classList.toggle("hidden", gap);
  updateResults();
}

function animate(timestamp) {
  if (!playing) return;
  if (!lastTime) lastTime = timestamp;
  const dt = (timestamp-lastTime)/1000;
  lastTime = timestamp;

  const min = 0;
  const max = 89;
  let a = Number(controls.angle.value);
  a += animationDirection * dt * 18;
  if (a >= max) { a=max; animationDirection=-1; }
  if (a <= min) { a=min; animationDirection=1; }
  controls.angle.value = a;
  updateResults();
  animationId = requestAnimationFrame(animate);
}

el("playBtn").addEventListener("click", () => {
  playing = !playing;
  el("playBtn").textContent = playing ? "❚❚ Pause" : "▶ Animate";
  if (playing) {
    lastTime = 0;
    animationId = requestAnimationFrame(animate);
  } else {
    cancelAnimationFrame(animationId);
  }
});

el("resetBtn").addEventListener("click", () => {
  controls.thickness.value = 29.7;
  controls.angle.value = 45;
  controls.nSi.value = 3.480;
  controls.nAir.value = 1.0003;
  playing = false;
  el("playBtn").textContent = "▶ Animate";
  cancelAnimationFrame(animationId);
  updateResults();
});

document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    mode = tab.dataset.mode;
    updateMode();
  });
});

Object.values(controls).forEach(c => {
  c.addEventListener("input", () => {
    if (c === controls.showFormula) return;
    updateResults();
  });
});
controls.showFormula.addEventListener("change", updateMode);

window.addEventListener("resize", resize);
resize();
updateMode();
