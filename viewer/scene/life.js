// Vida viewer, natural scene: small moving things, all decoration.
//   - pollen and dust drifting in the sunlight near where you look;
//   - a few birds circling high over the forest;
//   - fireflies among the trees at dusk.

"use strict";

var GLOW_VERTEX = [
  "attribute float seed;",
  "uniform float time;",
  "uniform float size;",
  "uniform float kind;",
  "uniform vec3 centre;",
  "uniform float spread;",
  "varying float vBright;",
  "void main() {",
  "  vec3 place = position;",
  "  float t = time * (kind > 0.5 ? 0.35 : 0.12) + seed * 40.0;",
  // wander slowly round where it started, and wrap round a box that
  // follows the middle of the view
  "  place += vec3(sin(t * 1.3 + seed * 9.0), sin(t * 0.9 + seed * 5.0) * 0.4, cos(t * 1.1 + seed * 7.0)) * (kind > 0.5 ? 1.2 : 2.0);",
  "  place.xz = centre.xz + mod(place.xz - centre.xz + spread * 0.5, spread) - spread * 0.5;",
  "  vec4 mvPosition = modelViewMatrix * vec4(place, 1.0);",
  "  gl_Position = projectionMatrix * mvPosition;",
  "  gl_PointSize = size * (kind > 0.5 ? 1.0 : 0.6 + seed) / max(1.0, -mvPosition.z) * 60.0;",
  // fireflies blink; dust sparkles now and then
  "  if (kind > 0.5) {",
  "    vBright = pow(max(0.0, sin(time * (1.5 + seed) + seed * 30.0)), 6.0);",
  "  } else {",
  "    vBright = 0.35 + 0.65 * pow(max(0.0, sin(time * 0.7 + seed * 50.0)), 8.0);",
  "  }",
  "}"
].join("\n");

var GLOW_FRAGMENT = [
  "uniform vec3 colour;",
  "uniform float strength;",
  "varying float vBright;",
  "void main() {",
  "  float d = length(gl_PointCoord - 0.5) * 2.0;",
  "  float soft = pow(max(0.0, 1.0 - d), 2.0);",
  "  gl_FragColor = vec4(colour * strength * vBright * soft, soft * vBright);",
  "}"
].join("\n");

function makeGlowPoints(state, count, kind, colour) {
  var random = makeRandom(kind === 1 ? 71 : 53);
  var positions = new Float32Array(count * 3);
  var seeds = new Float32Array(count);
  for (var i = 0; i < count; i++) {
    positions[i * 3] = (random() - 0.5) * 40;
    positions[i * 3 + 1] = kind === 1 ? 0.3 + random() * 2.2 : 0.4 + random() * 9;
    positions[i * 3 + 2] = (random() - 0.5) * 40;
    seeds[i] = random();
  }
  var geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("seed", new THREE.Float32BufferAttribute(seeds, 1));
  var material = new THREE.ShaderMaterial({
    uniforms: {
      time: state.uniforms.time,
      size: { value: kind === 1 ? 5.0 : 1.6 },
      kind: { value: kind },
      centre: { value: new THREE.Vector3() },
      spread: { value: 40 },
      colour: { value: colour },
      strength: { value: 1 }
    },
    vertexShader: GLOW_VERTEX,
    fragmentShader: GLOW_FRAGMENT,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false
  });
  var points = new THREE.Points(geometry, material);
  points.frustumCulled = false;
  state.scene.add(points);
  return points;
}

function birdGeometry() {
  // a bird seen from above: a small body and two long wings, 1 m across
  var positions = [
    // left wing
    0, 0, -0.08, -0.5, 0, 0.05, 0, 0, 0.1,
    // right wing
    0, 0, -0.08, 0, 0, 0.1, 0.5, 0, 0.05,
    // body
    0, 0.02, -0.18, -0.04, 0, 0.12, 0.04, 0, 0.12
  ];
  var geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function makeBirds(state) {
  var count = 7;
  var material = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.02, 0.02, 0.025), side: THREE.DoubleSide });
  function onBeforeCompile(shader) {
    shader.uniforms.time = state.uniforms.time;
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nuniform float time;")
      .replace("#include <begin_vertex>", [
        "#include <begin_vertex>",
        // the wings flap: the further out along the wing, the more it moves
        "float flapPhase = time * 9.0 + instanceMatrix[3].x * 0.7 + instanceMatrix[3].z * 0.3;",
        "transformed.y += abs(position.x) * sin(flapPhase) * 0.7;"
      ].join("\n"));
  }
  material.onBeforeCompile = onBeforeCompile;
  var birds = new THREE.InstancedMesh(birdGeometry(), material, count);
  birds.frustumCulled = false;
  state.scene.add(birds);
  state.birds = { mesh: birds, count: count, random: makeRandom(5) };
}

function updateLife(state) {
  // move the birds round their circles, and keep the dust and fireflies
  // near what you are looking at
  var time = state.uniforms.time.value;
  var world = state.world || 100;
  var tallest = state.tallest || 20;
  var matrix = new THREE.Matrix4();
  var turn = new THREE.Quaternion();
  var up = new THREE.Vector3(0, 1, 0);
  var place = new THREE.Vector3();
  var scale = new THREE.Vector3();
  var birds = state.birds;
  var wingspan = Math.max(0.6, world * 0.012);
  for (var i = 0; i < birds.count; i++) {
    var radius = world * (0.25 + 0.05 * (i % 3));
    var speed = 0.07 + 0.012 * i;
    var angle = time * speed + i * 0.9;
    place.set(Math.cos(angle) * radius + Math.sin(i * 2.1) * 3, tallest * 1.5 + 4 + Math.sin(time * 0.3 + i) * 2 + i * 0.8,
      Math.sin(angle) * radius + Math.cos(i * 1.7) * 3);
    turn.setFromAxisAngle(up, -angle);
    scale.set(wingspan, wingspan, wingspan);
    matrix.compose(place, turn, scale);
    birds.mesh.setMatrixAt(i, matrix);
  }
  birds.mesh.instanceMatrix.needsUpdate = true;
  birds.mesh.visible = state.dusk < 0.85;

  var target = state.view ? state.view.target : new THREE.Vector3();
  var dust = state.dust.material.uniforms;
  dust.centre.value.set(target.x, 0, target.z);
  dust.spread.value = Math.max(20, Math.min(60, state.view ? state.view.distance * 0.8 : 40));
  state.dust.position.y = state.groundHeight(target.x, -target.z);
  dust.strength.value = 0.9 * (1 - state.dusk) * state.uniforms.sunColour.value.g;
  var flies = state.fireflies.material.uniforms;
  flies.centre.value.set(target.x, 0, target.z);
  flies.spread.value = dust.spread.value;
  state.fireflies.position.y = state.dust.position.y;
  flies.strength.value = 3.0 * Math.max(0, (state.dusk - 0.5) * 2);
  state.fireflies.visible = state.dusk > 0.5;
}

function makeLife(state) {
  state.dust = makeGlowPoints(state, 700, 0, new THREE.Color(1.0, 0.95, 0.8));
  state.fireflies = makeGlowPoints(state, 260, 1, new THREE.Color(0.75, 1.0, 0.3));
  makeBirds(state);
}
