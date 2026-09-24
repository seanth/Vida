// Vida viewer, natural scene: grass.
//
// Many thousands of single blades, all drawn at once (one "instance" of the
// same blade shape each), bent and swayed by the wind in the graphics card.
// Grass is decoration (Vida doesn't simulate it), but it follows the
// simulation: it thins out and darkens where the simulated canopies shade
// the ground (the shade map, see ground.js), and doesn't grow under water.
//
// The technique follows well-known open-source grass in three.js (al-ro's
// instanced grass, James Smyth's Breath of the Wild style grass): a tapered
// blade, a curve, wind as rolling gusts plus a flutter, a darker base and a
// glow when the sun shines through from behind. A few of the blades are
// wildflowers instead.

"use strict";

function bladeGeometry() {
  // one blade: four pairs of points up the blade and one at the tip, from
  // x = -0.5 to 0.5 across and y = 0 to 1 up (made thinner and taller later)
  var positions = [];
  var levels = 4;
  for (var level = 0; level < levels; level++) {
    var y = level / levels;
    positions.push(-0.5, y, 0, 0.5, y, 0);
  }
  positions.push(0, 1, 0);
  var indices = [];
  for (var l = 0; l < levels - 1; l++) {
    var a = l * 2;
    indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
  }
  var top = (levels - 1) * 2;
  indices.push(top, top + 1, levels * 2);
  var geometry = new THREE.InstancedBufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(new Array(positions.length).fill(0), 3));
  geometry.setIndex(indices);
  return geometry;
}

var GRASS_VERTEX_PARTS = [
  "attribute vec3 grassPlace;",
  "attribute vec4 grassShape;",
  "uniform float time;",
  "uniform float windStrength;",
  "uniform float waterLevel;",
  "uniform float worldSize;",
  "uniform float grassReach;",
  "uniform sampler2D shadeMap;",
  "uniform vec3 sunDirection;",
  "varying vec3 vGrassColour;",
  "varying float vGrassGlow;",
  SCENE_NOISE_GLSL,
  SHADE_LOOKUP_GLSL
].join("\n");

var GRASS_BEGIN_VERTEX = [
  "float along = position.y;",
  "float seed = grassShape.w;",
  "float light = shadeLightAt(grassPlace.xz);",
  // shorter and fewer in deep shade, none under water
  "float tall = grassShape.y * mix(0.35, 1.0, smoothstep(0.02, 0.5, light));",
  "float keep = step(seed, smoothstep(0.0, 0.3, light) * 0.8 + 0.2);",
  "keep *= step(waterLevel + 0.05, grassPlace.y);",
  // shorter towards the edge of where the grass grows, so it fades into the ground
  "float edge = max(abs(grassPlace.x), abs(grassPlace.z));",
  "tall *= 1.0 - smoothstep(grassReach * 0.55, grassReach, edge + seed * grassReach * 0.2);",
  "tall *= keep;",
  // a few wildflowers: one stem in forty, in the sun, a little taller than
  // the grass, with a head at the top
  "float flower = step(0.975, fract(seed * 29.3)) * step(0.6, light);",
  "tall *= 1.0 + flower * 0.25;",
  "float wide = grassShape.z * (1.0 - along * 0.85) * keep;",
  "wide = mix(wide, grassShape.z * (along > 0.7 ? 1.0 : 0.3) * keep, flower);",
  "vec3 blade = vec3(position.x * wide, along * tall, 0.0);",
  // a natural curve, each blade its own
  "blade.z += along * along * tall * (0.15 + seed * 0.45);",
  "float turnCos = cos(grassShape.x);",
  "float turnSin = sin(grassShape.x);",
  "blade = vec3(blade.x * turnCos - blade.z * turnSin, blade.y, blade.x * turnSin + blade.z * turnCos);",
  // wind: gusts rolling across the field, and each blade's own flutter
  "vec2 windWay = normalize(vec2(1.0, 0.35));",
  "float gust = sceneNoise(grassPlace.xz * 0.07 - windWay * time * 0.8);",
  "float flutter = sin(time * 2.3 + seed * 6.2831 + dot(grassPlace.xz, windWay) * 0.7) * 0.22;",
  "float bend = (gust * gust * 1.3 + flutter) * windStrength;",
  "blade.xz += windWay * bend * along * along * tall;",
  "blade.y -= abs(bend) * along * along * tall * 0.3;",
  "vec3 transformed = grassPlace + blade;",
  // colour: dark at the root, lighter at the tip, drier outside the world
  // and in the sun, darker in the shade
  "float outside = max(abs(grassPlace.x), abs(grassPlace.z)) - worldSize * 0.5;",
  "vec3 tipColour = mix(vec3(0.2, 0.36, 0.05), vec3(0.34, 0.42, 0.1), fract(seed * 7.31));",
  "tipColour = mix(tipColour, vec3(0.48, 0.4, 0.17), smoothstep(0.0, worldSize * 0.25, outside) * 0.35 + step(0.93, fract(seed * 13.7)) * 0.5);",
  "vGrassColour = mix(tipColour * vec3(0.35, 0.45, 0.3), tipColour, along) * mix(0.5, 1.0, smoothstep(0.0, 0.6, light));",
  // flower heads: white, yellow or violet
  "vec3 petals = mix(vec3(0.85, 0.82, 0.72), vec3(0.9, 0.62, 0.05), step(0.55, fract(seed * 5.1)));",
  "petals = mix(petals, vec3(0.42, 0.22, 0.7), step(0.82, fract(seed * 3.7)));",
  "vGrassColour = mix(vGrassColour, petals, flower * step(0.7, along));",
  // shining through the blade when the sun is behind it
  "vec3 towards = normalize(transformed - cameraPosition);",
  "vGrassGlow = pow(max(dot(towards, sunDirection), 0.0), 3.0) * along * light;"
].join("\n");

function makeGrassMaterial(state) {
  var material = new THREE.MeshLambertMaterial({ side: THREE.DoubleSide });
  function onBeforeCompile(shader) {
    shader.uniforms.time = state.uniforms.time;
    shader.uniforms.windStrength = state.uniforms.windStrength;
    shader.uniforms.waterLevel = state.uniforms.waterLevel;
    shader.uniforms.worldSize = state.uniforms.worldSize;
    shader.uniforms.grassReach = state.uniforms.grassReach;
    shader.uniforms.shadeMap = state.uniforms.shadeMap;
    shader.uniforms.sunDirection = state.uniforms.sunDirection;
    shader.uniforms.sunColour = state.uniforms.sunColour;
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\n" + GRASS_VERTEX_PARTS)
      .replace("#include <beginnormal_vertex>", "vec3 objectNormal = normalize(vec3(-sin(grassShape.x) * 0.35, 1.0, cos(grassShape.x) * 0.35));")
      .replace("#include <begin_vertex>", GRASS_BEGIN_VERTEX);
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vGrassColour;\nvarying float vGrassGlow;\nuniform vec3 sunColour;")
      .replace("#include <color_fragment>", "diffuseColor.rgb *= vGrassColour;")
      // both sides of a blade are lit the same way (three.js would turn the
      // back side's light to face the ground)
      .replace("#include <normal_fragment_begin>", "#include <normal_fragment_begin>\nnormal = normalize(vNormal);")
      .replace("#include <output_fragment>", "outgoingLight += vGrassColour * sunColour * vGrassGlow * 1.4;\n#include <output_fragment>");
  }
  material.onBeforeCompile = onBeforeCompile;
  return material;
}

function buildGrass(state, header, bladeCount) {
  // Scatter the blades over the world and a little way round it (grass
  // doesn't need to reach the far hills, where the texture does).
  if (state.grass) {
    state.scene.remove(state.grass);
    state.grass.geometry.dispose();
    state.grass = null;
  }
  if (bladeCount <= 0) {
    return;
  }
  var world = header.worldSize;
  var reach = world / 2 + world * 0.4;
  state.uniforms.grassReach.value = reach;
  var inner = world / 2 + world * 0.08;
  var density = bladeCount * 0.8 / (4 * inner * inner);
  // sparser grass gets wider blades, so it still covers the ground
  var width = Math.max(0.03, Math.min(0.14, 0.045 * Math.sqrt(70 / density)));
  var random = makeRandom(97);
  var places = new Float32Array(bladeCount * 3);
  var shapes = new Float32Array(bladeCount * 4);
  for (var i = 0; i < bladeCount; i++) {
    // four in five over the world, the rest anywhere out to the reach
    var spread = random() < 0.8 ? inner : reach;
    var x = (random() * 2 - 1) * spread;
    var y = (random() * 2 - 1) * spread;
    var ground = state.groundHeight(x, y);
    // none on steep slopes, where the ground is bare soil or rock
    var rise = Math.abs(state.groundHeight(x + 0.4, y) - ground) + Math.abs(state.groundHeight(x, y + 0.4) - ground);
    var steep = smoothStep(0.6, 1.0, rise / 0.4);
    places[i * 3] = x;
    places[i * 3 + 1] = ground - 0.02;
    places[i * 3 + 2] = -y;
    // meadow grass, taller in some patches
    var patch = 0.5 + 0.5 * Math.sin(x * 0.19 + Math.sin(y * 0.13) * 2.2) * Math.sin(y * 0.17 + Math.sin(x * 0.11) * 1.9);
    shapes[i * 4] = random() * Math.PI * 2;
    shapes[i * 4 + 1] = (0.22 + random() * 0.3) * (0.7 + patch * 0.8) * (1 - steep);
    shapes[i * 4 + 2] = width * (0.7 + random() * 0.6);
    shapes[i * 4 + 3] = random();
  }
  var geometry = bladeGeometry();
  geometry.setAttribute("grassPlace", new THREE.InstancedBufferAttribute(places, 3));
  geometry.setAttribute("grassShape", new THREE.InstancedBufferAttribute(shapes, 4));
  geometry.instanceCount = bladeCount;
  var grass = new THREE.Mesh(geometry, state.materials.grass);
  grass.frustumCulled = false;
  grass.receiveShadow = true;
  grass.castShadow = false;
  state.scene.add(grass);
  state.grass = grass;
}
