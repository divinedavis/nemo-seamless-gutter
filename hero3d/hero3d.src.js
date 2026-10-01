// NEMO hero — a 3D close-up of one eave, looping through a gutter job:
// tear off -> measure -> form -> hang -> protect -> flow.
//
// Decorative only: the hero copy carries the message, the CSS gradient behind
// the canvas is the fallback (no WebGL, reduced motion still gets one still
// frame of the finished gutter). Self-hosted because the CSP is script-src 'self'.
//
// Units: 1 = 10 inches. The eave runs along +x from 0 to L, the fascia face
// is the z=0 plane, y=0 is the gutter bottom.
import {
  WebGLRenderer, Scene, PerspectiveCamera, Color, Fog, Group, Mesh, Shape,
  ExtrudeGeometry, ShapeGeometry, BoxGeometry, PlaneGeometry, CylinderGeometry,
  MeshStandardMaterial, MeshBasicMaterial, PointsMaterial, LineBasicMaterial,
  HemisphereLight, DirectionalLight, PointLight, CanvasTexture, RepeatWrapping,
  SRGBColorSpace, ACESFilmicToneMapping, PMREMGenerator, BufferGeometry,
  BufferAttribute, Points, LineSegments, Vector3, CatmullRomCurve3, DoubleSide,
  AdditiveBlending, Sprite, SpriteMaterial, MathUtils,
} from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

const host = document.querySelector('.hero-3d');
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (host) start(host);

function start(host) {
  let renderer;
  try {
    renderer = new WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  } catch (e) { return; }           // no WebGL: the CSS hero stays as it is
  const small = Math.min(window.innerWidth, window.innerHeight) < 700;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, small ? 1.5 : 1.75));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.domElement.setAttribute('aria-hidden', 'true');
  host.appendChild(renderer.domElement);

  const L = 8;                       // eave length
  const OUT = 7.35;                  // downspout x
  const WALL = -0.75;                // wall face z (soffit depth)
  const GROUND = -10;

  const scene = new Scene();
  scene.fog = new Fog(new Color('#16245c'), 12, 36);
  const pmrem = new PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.55;

  const camera = new PerspectiveCamera(38, 1, 0.05, 80);

  // ---- light: dusk, warm key from the low sun, cool sky fill
  const hemi = new HemisphereLight(0x8aa0ea, 0x0b1230, 0.9);
  scene.add(hemi);
  const sun = new DirectionalLight(0xffc48a, 2.6);
  sun.position.set(-6, 5, 7);
  scene.add(sun);
  const rim = new DirectionalLight(0x8aa0ea, 1.2);
  rim.position.set(10, 2, -4);
  scene.add(rim);
  const spark = new PointLight(0xf16c27, 0, 3.5, 1.6);
  scene.add(spark);

  // ---- procedural textures (canvas, no image requests)
  function canvasTex(w, h, draw, rx, ry) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    draw(c.getContext('2d'), w, h);
    const t = new CanvasTexture(c);
    t.colorSpace = SRGBColorSpace;
    t.wrapS = t.wrapT = RepeatWrapping;
    t.repeat.set(rx, ry);
    t.anisotropy = 4;
    return t;
  }
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

  const shingles = canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = '#1b2029'; g.fillRect(0, 0, w, h);
    const rowH = 64, tabW = 128;
    for (let r = 0; r < h / rowH; r++) {
      const off = (r % 2) * tabW / 2;
      for (let x = -tabW; x < w + tabW; x += tabW) {
        const s = 34 + rnd() * 22;
        g.fillStyle = `rgb(${s},${s + 4},${s + 12})`;
        g.fillRect(x + off + 2, r * rowH + 2, tabW - 4, rowH - 3);
        for (let i = 0; i < 70; i++) {         // granules
          const q = s + (rnd() - .5) * 40;
          g.fillStyle = `rgb(${q},${q + 3},${q + 9})`;
          g.fillRect(x + off + rnd() * tabW, r * rowH + rnd() * rowH, 2, 2);
        }
      }
      g.fillStyle = 'rgba(0,0,0,.55)';
      g.fillRect(0, r * rowH + rowH - 5, w, 5);    // shadow line under each course
    }
  }, 8.4 / 1.6, 5 / 1.6);

  const siding = canvasTex(256, 256, (g, w, h) => {
    const bh = 32;
    for (let y = 0; y < h; y += bh) {
      const grd = g.createLinearGradient(0, y, 0, y + bh);
      grd.addColorStop(0, '#9aa3b4'); grd.addColorStop(.85, '#c3cad6'); grd.addColorStop(1, '#6e778a');
      g.fillStyle = grd; g.fillRect(0, y, w, bh);
    }
  }, 3, 3);

  const waterTex = canvasTex(256, 64, (g, w, h) => {
    g.fillStyle = '#4f7fd6'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 90; i++) {
      g.fillStyle = `rgba(220,235,255,${0.15 + rnd() * 0.45})`;
      g.fillRect(rnd() * w, rnd() * h, 14 + rnd() * 50, 1.5);
    }
  }, 6, 1);

  const guardTex = canvasTex(128, 128, (g, w, h) => {
    g.clearRect(0, 0, w, h);
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
    g.globalCompositeOperation = 'destination-out';
    for (let y = 8; y < h; y += 16) for (let x = (y / 16 % 2) * 8 + 8; x < w; x += 16) {
      g.beginPath(); g.ellipse(x, y, 5.5, 3, 0, 0, Math.PI * 2); g.fill();
    }
  }, 40, 2.5);

  // ---- house: roof, fascia, soffit, wall, ground
  const house = new Group();
  scene.add(house);
  const slope = Math.atan(6 / 12);
  const roofGeo = new PlaneGeometry(L + 1.4, 5).translate(0, 2.5, 0).rotateX(-(Math.PI / 2 - slope));
  const roof = new Mesh(roofGeo, new MeshStandardMaterial({ map: shingles, roughness: .95, metalness: 0 }));
  roof.position.set(L / 2, 0.58, 0.16);
  house.add(roof);
  const dripEdge = new Mesh(new BoxGeometry(L + 1.4, 0.07, 0.2),
    new MeshStandardMaterial({ color: 0x2a303b, roughness: .6, metalness: .4 }));
  dripEdge.position.set(L / 2, 0.55, 0.08);
  house.add(dripEdge);
  const trim = new MeshStandardMaterial({ color: 0xeeeeea, roughness: .55 });
  const fascia = new Mesh(new BoxGeometry(L + 1.4, 0.62, 0.08), trim);
  fascia.position.set(L / 2, 0.24, -0.04);
  house.add(fascia);
  const soffit = new Mesh(new PlaneGeometry(L + 1.4, -WALL).rotateX(Math.PI / 2), trim);
  soffit.position.set(L / 2, -0.07, WALL / 2);
  house.add(soffit);
  const wall = new Mesh(new PlaneGeometry(L + 1.4, -GROUND), new MeshStandardMaterial({ map: siding, roughness: .8 }));
  wall.position.set(L / 2, GROUND / 2 - 0.07, WALL);
  house.add(wall);
  const side = new Mesh(new PlaneGeometry(8, -GROUND).rotateY(Math.PI / 2), new MeshStandardMaterial({ map: siding.clone(), roughness: .8 }));
  side.position.set(L + .7, GROUND / 2 - .07, WALL - 4);
  house.add(side);
  const cornerBoard = new Mesh(new BoxGeometry(.22, -GROUND, .22), trim);
  cornerBoard.position.set(L + .62, GROUND / 2 - .07, WALL + .08);
  house.add(cornerBoard);
  const ground = new Mesh(new PlaneGeometry(40, 30).rotateX(-Math.PI / 2),
    new MeshStandardMaterial({ color: 0x1d2b22, roughness: 1 }));
  ground.position.set(L / 2, GROUND, 8);
  house.add(ground);

  // ---- K-style gutter profile: back, flat bottom, cove + ogee front, rolled lip
  const P = [[0, .46], [0, 0], [.3, 0], [.34, .02], [.37, .08], [.4, .1], [.44, .13], [.46, .2],
    [.47, .3], [.49, .38], [.52, .44], [.53, .47], [.48, .47]];
  function wallShape(pts, t) {
    // thin-walled cross-section: the path plus an inward offset copy
    const inner = pts.map((p, i) => {
      const a = pts[Math.max(i - 1, 0)], b = pts[Math.min(i + 1, pts.length - 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], n = Math.hypot(dx, dy) || 1;
      return [p[0] - dy / n * t, p[1] + dx / n * t];
    });
    const s = new Shape();
    pts.forEach((p, i) => (i ? s.lineTo(p[0], p[1]) : s.moveTo(p[0], p[1])));
    for (let i = inner.length - 1; i >= 0; i--) s.lineTo(inner[i][0], inner[i][1]);
    s.closePath();
    return s;
  }
  function gutterGeo(len, sag) {
    const g = new ExtrudeGeometry(wallShape(P, 0.018), { depth: len, bevelEnabled: false, steps: sag ? 24 : 1 });
    g.rotateY(-Math.PI / 2).translate(len, 0, 0);       // length along +x from 0
    if (sag) {
      const pos = g.attributes.position;
      for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i) / len;
        pos.setY(i, pos.getY(i) - sag * Math.sin(Math.PI * x) - .08 * x);
      }
      g.computeVertexNormals();
    }
    return g;
  }
  const capShape = new Shape();
  P.slice(0, 12).forEach((p, i) => (i ? capShape.lineTo(p[0], p[1]) : capShape.moveTo(p[0], p[1])));
  capShape.closePath();
  const capGeo = new ShapeGeometry(capShape).rotateY(-Math.PI / 2);

  const white = new MeshStandardMaterial({ color: 0xf5f5f1, roughness: .32, metalness: .3, side: DoubleSide });

  // Old gutter — sagging, stained, full of leaves
  const old = new Group();
  const oldMat = new MeshStandardMaterial({ color: 0x8c8a7e, roughness: .8, metalness: .2, side: DoubleSide, transparent: true });
  old.add(new Mesh(gutterGeo(L, .14), oldMat));
  const leafMat = new MeshStandardMaterial({ color: 0x8a5a24, roughness: 1, side: DoubleSide, transparent: true });
  for (let i = 0; i < 70; i++) {
    const x = rnd() * L;
    const leaf = new Mesh(new PlaneGeometry(.12, .07), leafMat);
    leaf.position.set(x, .36 - .14 * Math.sin(Math.PI * x / L) - .08 * x / L + rnd() * .06, .08 + rnd() * .34);
    leaf.rotation.set(rnd() * 3, rnd() * 3, rnd() * 3);
    old.add(leaf);
  }
  scene.add(old);

  // New gutter: one continuous run
  const gutter = new Group();
  const run = new Mesh(gutterGeo(L), white);
  gutter.add(run);
  const capA = new Mesh(capGeo, white);
  const capB = new Mesh(capGeo, white); capB.position.x = L;
  gutter.add(capA, capB);
  const hangerMat = new MeshStandardMaterial({ color: 0xc9ccd2, roughness: .35, metalness: .8 });
  const hangers = [];
  for (let x = .5; x < L; x += .9) {
    const h = new Mesh(new BoxGeometry(.06, .025, .5), hangerMat);
    h.position.set(x, .44, .25);
    gutter.add(h); hangers.push(h);
  }
  const water = new Mesh(new PlaneGeometry(OUT, .3).rotateX(-Math.PI / 2),
    new MeshStandardMaterial({ map: waterTex, color: 0x9fc0ff, roughness: .1, metalness: .2, transparent: true, opacity: 0, depthWrite: false }));
  water.position.set(OUT / 2, .07, .17);
  gutter.add(water);
  const guard = new Mesh(new PlaneGeometry(L, .5).rotateX(-Math.PI / 2),
    new MeshStandardMaterial({ color: 0xd8dbe0, alphaMap: guardTex, transparent: true, roughness: .3, metalness: .85, side: DoubleSide, opacity: 0 }));
  guard.position.set(L / 2, .47, .26);
  gutter.add(guard);
  scene.add(gutter);

  // Downspout — four segments that grow in sequence, top to bottom
  const spoutMat = new MeshStandardMaterial({ color: 0xf2f2ee, roughness: .35, metalness: .25 });
  function segment(a, b) {
    const d = b.clone().sub(a), len = d.length();
    const geo = new BoxGeometry(.3, len, .2).translate(0, -len / 2, 0);   // origin at the top end
    const m = new Mesh(geo, spoutMat);
    m.position.copy(a);
    m.rotation.x = Math.atan2(-d.z, -d.y);
    m.userData.len = len;
    return m;
  }
  const z0 = .17, zW = WALL + .12;
  const sp = [
    segment(new Vector3(OUT, .02, z0), new Vector3(OUT, -.35, z0)),
    segment(new Vector3(OUT, -.35, z0), new Vector3(OUT, -.95, zW)),
    segment(new Vector3(OUT, -.95, zW), new Vector3(OUT, GROUND + 1, zW)),
    segment(new Vector3(OUT, GROUND + 1, zW), new Vector3(OUT, GROUND + .55, zW + .55)),
  ];
  const strapMat = new MeshStandardMaterial({ color: 0xdedfe0, roughness: .4, metalness: .5 });
  const straps = [-3, -6.5].map((y) => {
    const s = new Mesh(new BoxGeometry(.36, .06, .26), strapMat);
    s.position.set(OUT, y, zW); scene.add(s); return s;
  });
  sp.forEach((m) => scene.add(m));
  const outlet = new Vector3(OUT, GROUND + .55, zW + .55);

  // Measuring tape line + ticks along the fascia
  const orange = new MeshBasicMaterial({ color: 0xf16c27, transparent: true });
  const tape = new Mesh(new BoxGeometry(1, .012, .01).translate(.5, 0, 0), orange);
  tape.position.set(0, .3, .006);
  scene.add(tape);
  const ticks = [];
  for (let x = .5; x < L; x += .5) {
    const t = new Mesh(new BoxGeometry(.012, x % 2 === 0 ? .09 : .05, .01), orange);
    t.position.set(x, .3, .006); scene.add(t); ticks.push(t);
  }
  const glowTex = canvasTex(64, 64, (g) => {
    const r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    r.addColorStop(0, 'rgba(255,240,220,1)'); r.addColorStop(.25, 'rgba(241,108,39,.9)'); r.addColorStop(1, 'rgba(241,108,39,0)');
    g.fillStyle = r; g.fillRect(0, 0, 64, 64);
  }, 1, 1);
  const glow = new Sprite(new SpriteMaterial({ map: glowTex, blending: AdditiveBlending, depthWrite: false, transparent: true }));
  glow.scale.set(.5, .5, .5);
  scene.add(glow);

  // Rain streaks
  const RAIN = small ? 1000 : 2400;
  const rainPos = new Float32Array(RAIN * 6), rainSeed = new Float32Array(RAIN * 3);
  for (let i = 0; i < RAIN; i++) {
    rainSeed[i * 3] = -4 + rnd() * (L + 12);
    rainSeed[i * 3 + 1] = rnd();
    rainSeed[i * 3 + 2] = -1 + rnd() * 13;
  }
  const rainGeo = new BufferGeometry();
  rainGeo.setAttribute('position', new BufferAttribute(rainPos, 3));
  const rainMat = new LineBasicMaterial({ color: 0xbcd0ff, transparent: true, opacity: 0, depthWrite: false });
  const rain = new LineSegments(rainGeo, rainMat);
  rain.frustumCulled = false;
  scene.add(rain);

  // Water out of the downspout kick-out
  const DROPS = 420;
  const dropPos = new Float32Array(DROPS * 3), dropLife = new Float32Array(DROPS), dropVel = new Float32Array(DROPS * 3);
  const dropGeo = new BufferGeometry();
  dropGeo.setAttribute('position', new BufferAttribute(dropPos, 3));
  const dropTex = canvasTex(32, 32, (g) => {
    const r = g.createRadialGradient(16, 16, 0, 16, 16, 16);
    r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(.5, 'rgba(255,255,255,.7)'); r.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = r; g.fillRect(0, 0, 32, 32);
  }, 1, 1);
  const dropMat = new PointsMaterial({ map: dropTex, color: 0xcfe0ff, size: .11, transparent: true, opacity: 0, depthWrite: false });
  const drops = new Points(dropGeo, dropMat);
  drops.frustumCulled = false;
  scene.add(drops);
  for (let i = 0; i < DROPS; i++) dropLife[i] = -rnd();

  // ---- timeline
  const STAGES = [
    { at: 0, word: 'to tear off', sub: 'Old, sagging gutters come down and get hauled away.' },
    { at: 4, word: 'to measure', sub: 'Every run measured to your roofline.' },
    { at: 8, word: 'to form', sub: 'One continuous piece, formed on-site. No seams.' },
    { at: 12, word: 'to hang', sub: 'Secure hangers, pitched so water actually moves.' },
    { at: 15.5, word: 'to protect', sub: 'Downspouts and guards that keep it all clear.' },
    { at: 19, word: 'to flow', sub: 'Rain goes where it should: away from your home.' },
  ];
  const LOOP = 27;
  const cam = [
    // [time, position, target]
    [0, [-1.2, 1.5, 3.6], [3.2, -0.2, 0]],
    [4, [-0.6, 1.25, 2.9], [3.6, 0.15, 0]],
    [8, [1.0, 1.7, 3.0], [4.4, 0.0, 0.4]],
    [12, [3.6, 1.9, 2.0], [6.0, 0.1, 0.2]],
    [14.8, [5.4, 1.7, 2.3], [7.0, 0.1, 0.2]],
    [16.8, [10.6, 0.4, 4.6], [6.6, -1.6, 0]],
    [19, [2.4, 1.7, 3.2], [6, -0.1, 0]],
    [22, [5.2, 1.35, 1.7], [7.4, 0.05, 0.2]],
    [25.2, [10.8, -6.4, 4.4], [7.2, -8.9, 0.6]],
    [27, [-1.2, 1.5, 3.6], [3.2, -0.2, 0]],
  ];
  const camPos = new CatmullRomCurve3(cam.map((k) => new Vector3(...k[1])));
  const camTgt = new CatmullRomCurve3(cam.map((k) => new Vector3(...k[2])));
  function along(t) {
    // map loop time to curve u so each keyframe lands on its point, eased in between
    for (let i = 0; i < cam.length - 1; i++) {
      if (t <= cam[i + 1][0]) {
        const f = (t - cam[i][0]) / (cam[i + 1][0] - cam[i][0]);
        return (i + MathUtils.smootherstep(f, 0, 1)) / (cam.length - 1);
      }
    }
    return 1;
  }
  const ramp = (t, a, b) => MathUtils.clamp((t - a) / (b - a), 0, 1);
  const ease = (x) => x * x * (3 - 2 * x);

  // ---- caption (lower right, like a film title card)
  const cap = document.createElement('div');
  cap.className = 'hero-3d-cap';
  cap.setAttribute('aria-hidden', 'true');
  cap.innerHTML = '<span class="w"></span><span class="s"></span><span class="bar"><i></i></span>';
  host.appendChild(cap);
  const capW = cap.querySelector('.w'), capS = cap.querySelector('.s'), capBar = cap.querySelector('.bar i');
  let shown = -1;

  const v = new Vector3(), tg = new Vector3();
  const pointer = { x: 0, y: 0, tx: 0, ty: 0 };
  window.addEventListener('pointermove', (e) => {
    pointer.tx = e.clientX / window.innerWidth - .5;
    pointer.ty = e.clientY / window.innerHeight - .5;
  }, { passive: true });

  function frame(t, dt) {
    // tear off: the old run tips forward and drops away
    const fall = ease(ramp(t, 1.2, 3.6));
    old.visible = t < 3.8;
    old.position.set(0, -fall * fall * 7, fall * 1.4);
    old.rotation.x = fall * 0.9;
    oldMat.opacity = leafMat.opacity = 1 - ramp(t, 2.8, 3.7);

    // measure
    const m = ramp(t, 4.3, 7.4);
    const tapeOn = t > 4 && t < 9.2;
    tape.visible = tapeOn;
    tape.scale.x = Math.max(m * L, .0001);
    orange.opacity = 1 - ramp(t, 8.2, 9.2);
    ticks.forEach((k) => { k.visible = tapeOn && k.position.x <= m * L; });

    // form: the run extrudes out of the machine end, held low, then lifted into place
    const f = ramp(t, 8.1, 11.6);
    const lift = ease(ramp(t, 12, 13.6));
    gutter.visible = t > 8.05;
    run.scale.x = Math.max(f, .0001);
    capA.visible = t > 12.6;
    capB.visible = t > 13.4;
    gutter.position.set(0, (1 - lift) * -.12, (1 - lift) * .62);
    hangers.forEach((h, i) => {
      const s = ease(ramp(t, 13.4 + i * .17, 13.7 + i * .17));
      h.visible = s > 0; h.scale.set(1, 1, Math.max(s, .0001));
    });

    // the glow rides the measuring tip, then the forming tip
    let gOn = 0;
    if (t > 4.2 && t < 7.6) { glow.position.set(m * L, .3, .05); gOn = 1 - ramp(t, 7.3, 7.6); }
    else if (t > 8.1 && t < 11.9) { glow.position.set(f * L, .1, .85); gOn = 1 - ramp(t, 11.5, 11.9); }
    glow.visible = gOn > 0;
    glow.material.opacity = gOn * (.8 + .2 * Math.sin(t * 30));
    spark.position.copy(glow.position);
    spark.intensity = gOn * 3;

    // protect: downspout segments, straps, then the guard settles on
    let acc = 15.6;
    sp.forEach((s, i) => {
      const dur = [.35, .45, 1.5, .4][i];
      const g = ease(ramp(t, acc, acc + dur)); acc += dur;
      s.visible = g > 0; s.scale.y = Math.max(g, .0001);
    });
    straps.forEach((s, i) => { s.visible = t > 16.9 + i * .5; });
    const gd = ease(ramp(t, 17.6, 18.8));
    guard.visible = gd > 0;
    guard.material.opacity = gd;
    guard.position.y = .47 + (1 - gd) * .6;

    // flow: rain in, water runs to the outlet and out the kick-out
    const wet = ramp(t, 19, 20.5) * (1 - ramp(t, 25.6, 26.6));
    rainMat.opacity = wet * .75;
    water.material.opacity = ramp(t, 20, 21.5) * (1 - ramp(t, 25.6, 26.6)) * .85;
    waterTex.offset.x -= dt * .9;
    sun.intensity = 2.6 - wet * 1.4;
    hemi.intensity = .9 - wet * .25;
    if (wet > 0) {
      for (let i = 0; i < RAIN; i++) {
        const x = rainSeed[i * 3], z = rainSeed[i * 3 + 2];
        const y = 8 - ((rainSeed[i * 3 + 1] * 19 + t * 14) % 19);
        const o = i * 6;
        rainPos[o] = x; rainPos[o + 1] = y; rainPos[o + 2] = z;
        rainPos[o + 3] = x - .03; rainPos[o + 4] = y - .38; rainPos[o + 5] = z;
      }
      rainGeo.attributes.position.needsUpdate = true;
    }
    rain.visible = wet > 0;
    const pour = ramp(t, 21.2, 22.4) * (1 - ramp(t, 25.4, 26.4));
    drops.visible = pour > 0;
    dropMat.opacity = pour * .9;
    if (pour > 0) {
      for (let i = 0; i < DROPS; i++) {
        dropLife[i] += dt;
        if (dropLife[i] > .9 || dropLife[i] < 0 && dropLife[i] + dt >= 0) {
          dropLife[i] = 0;
          dropPos[i * 3] = outlet.x + (rnd() - .5) * .16;
          dropPos[i * 3 + 1] = outlet.y;
          dropPos[i * 3 + 2] = outlet.z;
          dropVel[i * 3] = (rnd() - .5) * .4; dropVel[i * 3 + 1] = -.2; dropVel[i * 3 + 2] = 1.8 + rnd() * .8;
        }
        if (dropLife[i] < 0) continue;
        dropVel[i * 3 + 1] -= 9.8 * dt;
        for (let k = 0; k < 3; k++) dropPos[i * 3 + k] += dropVel[i * 3 + k] * dt;
        if (dropPos[i * 3 + 1] < GROUND) { dropPos[i * 3 + 1] = GROUND + .01; dropVel[i * 3 + 1] *= -.15; dropVel[i * 3 + 2] *= .5; }
      }
      dropGeo.attributes.position.needsUpdate = true;
    }

    // camera
    const u = along(t);
    camPos.getPoint(Math.min(u, 1), v);
    camTgt.getPoint(Math.min(u, 1), tg);
    pointer.x += (pointer.tx - pointer.x) * .04;
    pointer.y += (pointer.ty - pointer.y) * .04;
    v.x += pointer.x * .5; v.y -= pointer.y * .3;
    camera.position.copy(v);
    camera.lookAt(tg);

    // loop seam: dip to the background between passes
    renderer.domElement.style.opacity = String(Math.min(ramp(t, 0, .8), 1 - ramp(t, LOOP - .9, LOOP)));

    // caption
    let s = 0;
    for (let i = 0; i < STAGES.length; i++) if (t >= STAGES[i].at) s = i;
    if (s !== shown) {
      shown = s;
      cap.classList.remove('in');
      void cap.offsetWidth;
      capW.textContent = STAGES[s].word + (s === STAGES.length - 1 ? '.' : '…');
      capS.textContent = STAGES[s].sub;
      cap.classList.add('in');
    }
    capBar.style.transform = `scaleX(${(t / LOOP).toFixed(4)})`;
    cap.style.opacity = String(1 - ramp(t, LOOP - 1.2, LOOP - .4));

    renderer.render(scene, camera);
  }

  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.fov = w / h < 1 ? 52 : 38;
    // Desktop: the copy sits on the left, so slide the picture right of centre
    if (w / h > 1.1) camera.setViewOffset(w, h, -w * .17, 0, w, h);
    // Phone: the copy fills the middle, so lift the picture into the band under the header
    else camera.setViewOffset(w, h, 0, h * .2, w, h);
    camera.updateProjectionMatrix();
  }
  resize();
  window.addEventListener('resize', resize);

  if (reduce) {
    // one still of the finished, guarded gutter; no motion
    const still = () => { resize(); frame(18.95, 0); cap.style.display = 'none'; renderer.domElement.style.opacity = '1'; };
    still();
    window.addEventListener('resize', still);
    host.classList.add('ready');
    return;
  }

  let running = true, visible = true, frozen = false, last = performance.now(), t = 0;
  new IntersectionObserver((e) => { visible = e[0].isIntersecting; tick(); }).observe(host);
  document.addEventListener('visibilitychange', tick);
  function tick() {
    if (frozen) return;
    const want = visible && !document.hidden;
    if (want && !running) { running = true; last = performance.now(); requestAnimationFrame(loop); }
    if (!want) running = false;
  }
  function loop(now) {
    if (!running) return;
    const dt = Math.min((now - last) / 1000, .1);
    last = now;
    t = (t + dt) % LOOP;
    frame(t, dt);
    requestAnimationFrame(loop);
  }
  frame(0, 0);
  host.classList.add('ready');
  requestAnimationFrame(loop);

  // headless preview hook: ?hero3d=<seconds> freezes the loop at that time
  const q = /[?&]hero3d=([\d.]+)/.exec(location.search);
  if (q) { frozen = true; running = false; t = parseFloat(q[1]); for (let k = 60; k >= 0; k--) frame(Math.max(t - k / 30, 0), 1 / 30); renderer.domElement.style.opacity = '1'; }
}
