// Vida viewer, natural scene: the land.
//
// Inside the simulated world the height of the ground comes from the
// terrain file (to scale). Outside it, where Vida doesn't simulate
// anything, the land eases into low rolling hills, high enough to hold the
// water in.
//
// The ground is also darker, and the grass thinner, where the simulation's
// canopies shade it: the "shade map" is the light that would reach the
// ground straight down through every canopy above it (each canopy lets
// through its species' canopyTransmittance).

"use strict";

var SHADE_MAP_CELLS = 256;
var HEIGHT_MAP_CELLS = 256;

function smoothStep(from, to, value) {
  var t = Math.max(0, Math.min(1, (value - from) / (to - from)));
  return t * t * (3 - 2 * t);
}

function terrainHeightFunction(header) {
  // The height of the ground from the terrain grid (see Vida_Data/vjson.py),
  // smoothly in between the points of the grid, and level beyond the edges.
  // x and y are Vida's (east and north).
  var terrain = header.terrain;
  var world = header.worldSize;
  if (!terrain) {
    return function flat() { return 0; };
  }
  var cells = terrain.cells;
  var size = terrain.cellSize;
  function at(row, column) {
    row = Math.max(0, Math.min(cells - 1, row));
    column = Math.max(0, Math.min(cells - 1, column));
    return terrain.elevation[row][column] || 0;
  }
  function height(x, y) {
    var column = Math.max(0, Math.min(cells - 1, (x + world / 2) / size));
    var row = Math.max(0, Math.min(cells - 1, (y + world / 2) / size));
    var c0 = Math.floor(column);
    var r0 = Math.floor(row);
    var fc = column - c0;
    var fr = row - r0;
    var low = at(r0, c0) * (1 - fc) + at(r0, c0 + 1) * fc;
    var high = at(r0 + 1, c0) * (1 - fc) + at(r0 + 1, c0 + 1) * fc;
    return low * (1 - fr) + high * fr;
  }
  return height;
}

function groundHeightFunction(header, highestWater) {
  // The height of the ground anywhere: the terrain inside the world, and
  // hills outside it.
  var world = header.worldSize;
  var inside = terrainHeightFunction(header);
  var edgeTotal = 0;
  for (var i = 0; i < 40; i++) {
    var along = -world / 2 + (i + 0.5) / 40 * world;
    edgeTotal += inside(along, -world / 2) + inside(along, world / 2) + inside(-world / 2, along) + inside(world / 2, along);
  }
  var surroundings = Math.max(edgeTotal / 160, highestWater + 0.6);
  function height(x, y) {
    var h = inside(x, y);
    var outside = Math.max(Math.abs(x), Math.abs(y)) - world / 2;
    if (outside <= 0) {
      return h;
    }
    var hills = (Math.sin(x * 0.045 + Math.sin(y * 0.03) * 2.1) + Math.sin(y * 0.052 + Math.sin(x * 0.027) * 1.7)) * world * 0.014;
    var eased = h + (surroundings - h) * smoothStep(0, world * 0.28, outside);
    return eased + Math.max(0, hills + world * 0.01) * smoothStep(world * 0.08, world * 0.6, outside);
  }
  return height;
}

function makeGroundMaterial(state, textures) {
  // The ground's colour is worked out in the shader, point by point: grass
  // in patches, drier grass here and there, soil on slopes, layered rock on
  // steep ones, dark wet soil at the water's edge, sand and mud under the
  // water with the flickering light patterns (caustics) that ripples
  // focus on the bottom, and darker ground under the trees.
  var material = new THREE.MeshStandardMaterial({
    map: textures.colour,
    normalMap: textures.normal,
    normalScale: new THREE.Vector2(0.7, 0.7),
    roughness: 0.95,
    metalness: 0,
    envMapIntensity: 0.4
  });
  function onBeforeCompile(shader) {
    shader.uniforms.time = state.uniforms.time;
    shader.uniforms.waterLevel = state.uniforms.waterLevel;
    shader.uniforms.worldSize = state.uniforms.worldSize;
    shader.uniforms.shadeMap = state.uniforms.shadeMap;
    shader.uniforms.sunColour = state.uniforms.sunColour;
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vGroundPlace;\nvarying vec3 vGroundNormal;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\nvGroundPlace = (modelMatrix * vec4(transformed, 1.0)).xyz;\nvGroundNormal = normalize(mat3(modelMatrix) * objectNormal);");
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", [
        "#include <common>",
        "varying vec3 vGroundPlace;",
        "varying vec3 vGroundNormal;",
        "uniform float time;",
        "uniform float waterLevel;",
        "uniform float worldSize;",
        "uniform sampler2D shadeMap;",
        "uniform vec3 sunColour;",
        "float groundWetness = 0.0;",
        SCENE_NOISE_GLSL,
        SHADE_LOOKUP_GLSL
      ].join("\n"))
      .replace("#include <map_fragment>", [
        "vec3 place = vGroundPlace;",
        "float slope = 1.0 - clamp(vGroundNormal.y, 0.0, 1.0);",
        "float broad = sceneFbm(place.xz * 0.017 + 3.7);",
        "float patches = sceneFbm(place.xz * 0.07);",
        "float grain = sceneFbm(place.xz * 0.9);",
        // meadow: greens in patches, deeper in some wide stretches and
        // fresher in others, with drier straw-coloured patches (more of
        // them outside the world)
        "vec3 colour = mix(vec3(0.075, 0.16, 0.03), vec3(0.18, 0.29, 0.06), smoothstep(0.3, 0.72, patches));",
        "colour *= mix(vec3(0.78, 0.92, 0.85), vec3(1.12, 1.05, 0.9), smoothstep(0.35, 0.68, broad));",
        "float outside = max(abs(place.x), abs(place.z)) - worldSize * 0.5;",
        "float dry = smoothstep(0.6, 0.84, patches + smoothstep(0.0, worldSize * 0.5, outside) * 0.12 + (broad - 0.5) * 0.3);",
        "colour = mix(colour, vec3(0.3, 0.27, 0.12), dry * 0.5);",
        // bare soil on slopes, and rock, in layers, on steep ones
        "colour = mix(colour, vec3(0.19, 0.12, 0.065) * (0.8 + 0.4 * grain), smoothstep(0.16, 0.34, slope + (grain - 0.5) * 0.2));",
        "float layers = sceneNoise(vec2(place.y * 3.1, (place.x + place.z) * 0.15)) * 0.6 + grain * 0.4;",
        "vec3 rock = mix(vec3(0.14, 0.1, 0.07), vec3(0.3, 0.25, 0.19), layers);",
        "colour = mix(colour, rock, smoothstep(0.36, 0.55, slope + (grain - 0.5) * 0.15));",
        "vec4 detail = texture2D(map, vUv);",
        "colour *= 0.55 + 0.8 * detail.r;",
        // shade of the canopies above, from the simulation
        "float light = shadeLightAt(place.xz);",
        "colour *= 0.42 + 0.58 * pow(light, 0.3);",
        // the water's edge and the bottom
        "float above = place.y - waterLevel;",
        "if (waterLevel > -500.0) {",
        "  groundWetness = 1.0 - smoothstep(0.0, 0.4, above + (grain - 0.5) * 0.12);",
        "  colour = mix(colour, colour * 0.42, groundWetness * 0.85);",
        "  if (above < 0.0) {",
        "    float depth = -above;",
        "    colour = mix(vec3(0.065, 0.06, 0.032), vec3(0.02, 0.032, 0.02), smoothstep(0.0, 1.0, depth)) * (0.75 + 0.5 * grain);",
        // the net of light that the ripples focus on the bottom (caustics)
        "    float c1 = sceneCellEdges(place.xz * 1.1, time * 1.1);",
        "    float c2 = sceneCellEdges(place.xz * 1.7 + 7.0, time * 1.4);",
        "    float caustic = (1.0 - smoothstep(0.0, 0.09, c1)) + (1.0 - smoothstep(0.0, 0.07, c2)) * 0.7;",
        "    float closeBy = 1.0 - smoothstep(8.0, 25.0, distance(cameraPosition, place));",
        "    colour += sunColour * caustic * 0.04 * exp(-depth * 1.2) * smoothstep(0.0, 0.08, depth) * closeBy;",
        "  }",
        "}",
        "diffuseColor.rgb = colour;"
      ].join("\n"))
      .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.28, groundWetness);");
  }
  material.onBeforeCompile = onBeforeCompile;
  return material;
}

// The light reaching the ground at a point (three.js x and z), from the
// shade map, which covers the simulated world; outside it there is full light.
var SHADE_LOOKUP_GLSL = [
  "float shadeLightAt(vec2 xz) {",
  "  vec2 uv = vec2(xz.x / worldSize + 0.5, -xz.y / worldSize + 0.5);",
  "  if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {",
  "    return 1.0;",
  "  }",
  "  return texture2D(shadeMap, uv).r;",
  "}"
].join("\n");

function makeShadeMap() {
  var data = new Uint8Array(SHADE_MAP_CELLS * SHADE_MAP_CELLS * 4);
  data.fill(255);
  var texture = new THREE.DataTexture(data, SHADE_MAP_CELLS, SHADE_MAP_CELLS, THREE.RGBAFormat);
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

function updateShadeMap(state, theRun, cycle) {
  // The light that reaches the ground straight down through the canopies
  // of this cycle (each lets through its species' canopyTransmittance),
  // softened a little at the edges.
  var cells = SHADE_MAP_CELLS;
  var world = theRun.header.worldSize;
  var size = world / cells;
  var light = new Float32Array(cells * cells);
  light.fill(1);
  var index = theRun.fieldIndex;
  var plants = cycle.plants;
  for (var p = 0; p < plants.length; p++) {
    var plant = plants[p];
    var radius = plant[index.canopyRadius];
    if (!(radius > 0)) {
      continue;
    }
    var species = theRun.species[plant[index.species]];
    var through = species && species.canopyTransmittance !== null && species.canopyTransmittance !== undefined ? species.canopyTransmittance : 0.05;
    var x = plant[index.x];
    var y = plant[index.y];
    var firstColumn = Math.max(0, Math.floor((x - radius + world / 2) / size));
    var lastColumn = Math.min(cells - 1, Math.floor((x + radius + world / 2) / size));
    var firstRow = Math.max(0, Math.floor((y - radius + world / 2) / size));
    var lastRow = Math.min(cells - 1, Math.floor((y + radius + world / 2) / size));
    for (var row = firstRow; row <= lastRow; row++) {
      var cy = -world / 2 + (row + 0.5) * size - y;
      for (var column = firstColumn; column <= lastColumn; column++) {
        var cx = -world / 2 + (column + 0.5) * size - x;
        if (cx * cx + cy * cy <= radius * radius) {
          light[row * cells + column] *= through;
        }
      }
    }
  }
  var data = state.uniforms.shadeMap.value.image.data;
  for (var r = 0; r < cells; r++) {
    for (var c = 0; c < cells; c++) {
      // a small blur, so the edge of the shade is soft
      var total = 0;
      var count = 0;
      for (var dr = -1; dr <= 1; dr++) {
        for (var dc = -1; dc <= 1; dc++) {
          var rr = r + dr;
          var cc = c + dc;
          if (rr >= 0 && rr < cells && cc >= 0 && cc < cells) {
            total += light[rr * cells + cc];
            count += 1;
          }
        }
      }
      var value = Math.round(total / count * 255);
      var at = (r * cells + c) * 4;
      data[at] = value;
      data[at + 1] = value;
      data[at + 2] = value;
      data[at + 3] = 255;
    }
  }
  state.uniforms.shadeMap.value.needsUpdate = true;
  state.shadeLight = light;
  state.shadeCells = cells;
}

function shadeLightAtPoint(state, x, y) {
  // the same light, read in JavaScript (Vida's x and y)
  if (!state.shadeLight) {
    return 1;
  }
  var world = state.world;
  var cells = state.shadeCells;
  var column = Math.floor((x + world / 2) / world * cells);
  var row = Math.floor((y + world / 2) / world * cells);
  if (column < 0 || row < 0 || column >= cells || row >= cells) {
    return 1;
  }
  return state.shadeLight[row * cells + column];
}

function buildGround(state, header, highestWater) {
  // the land as one big mesh, the height map the water reads, and the edge
  // line of the simulated world
  var world = header.worldSize;
  var margin = world * 0.9;
  var size = world + 2 * margin;
  var step = world / 150;
  if (header.terrain) {
    step = Math.max(header.terrain.cellSize / 2, size / 420);
  }
  var across = Math.min(460, Math.ceil(size / step));
  var height = groundHeightFunction(header, highestWater);
  state.groundHeight = height;
  state.groundSize = size;
  var positions = [];
  var uvs = [];
  var indices = [];
  for (var j = 0; j <= across; j++) {
    for (var i = 0; i <= across; i++) {
      var x = -size / 2 + i / across * size;
      var y = -size / 2 + j / across * size;
      positions.push(x, height(x, y), -y);
      uvs.push(x / 2.5, y / 2.5);
    }
  }
  for (var row = 0; row < across; row++) {
    for (var column = 0; column < across; column++) {
      var a = row * (across + 1) + column;
      var b = a + 1;
      var c = a + across + 1;
      var d = c + 1;
      // counter-clockwise seen from above, so the ground faces up
      indices.push(a, b, c, b, d, c);
    }
  }
  var geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  if (state.ground) {
    state.scene.remove(state.ground);
    state.ground.geometry.dispose();
  }
  var ground = new THREE.Mesh(geometry, state.materials.ground);
  ground.receiveShadow = true;
  state.scene.add(ground);
  state.ground = ground;

  // the height of the ground as a texture, for the water to know how deep it is
  var cells = HEIGHT_MAP_CELLS;
  var data = new Uint16Array(cells * cells * 4);
  for (var r = 0; r < cells; r++) {
    for (var q = 0; q < cells; q++) {
      var hx = -size / 2 + (q + 0.5) / cells * size;
      var hy = size / 2 - (r + 0.5) / cells * size;
      var half = THREE.DataUtils.toHalfFloat(height(hx, hy));
      var at = (r * cells + q) * 4;
      data[at] = half;
      data[at + 1] = half;
      data[at + 2] = half;
      data[at + 3] = THREE.DataUtils.toHalfFloat(1);
    }
  }
  var heightMap = new THREE.DataTexture(data, cells, cells, THREE.RGBAFormat, THREE.HalfFloatType);
  heightMap.magFilter = THREE.LinearFilter;
  heightMap.minFilter = THREE.LinearFilter;
  heightMap.needsUpdate = true;
  if (state.uniforms.heightMap.value) {
    state.uniforms.heightMap.value.dispose();
  }
  state.uniforms.heightMap.value = heightMap;
  state.uniforms.heightMapSize.value = size;

  // hills, woods and mountains far away all round
  buildFarLand(state, world, size, height(size / 2, 0));

  // a faint line round the edge of the simulated world
  if (state.edge) {
    state.scene.remove(state.edge);
    state.edge.geometry.dispose();
  }
  var edgePoints = [];
  var corners = [[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]];
  for (var k = 0; k < 4; k++) {
    for (var s = 0; s < 60; s++) {
      var t = s / 60;
      var ex = (corners[k][0] + (corners[k + 1][0] - corners[k][0]) * t) * world / 2;
      var ey = (corners[k][1] + (corners[k + 1][1] - corners[k][1]) * t) * world / 2;
      edgePoints.push(new THREE.Vector3(ex, height(ex, ey) + 0.06, -ey));
    }
  }
  edgePoints.push(edgePoints[0].clone());
  var edge = new THREE.Line(new THREE.BufferGeometry().setFromPoints(edgePoints), state.materials.edge);
  state.scene.add(edge);
  state.edge = edge;
}

function farHillRise(world, angle, fraction) {
  // How high the far hills are, at an angle round the world and a fraction
  // of the way out to the furthest hills.
  var bumps = 0.55 + 0.3 * Math.sin(angle * 5 + 1.3) + 0.2 * Math.sin(angle * 13 + 0.4) + 0.12 * Math.sin(angle * 29 + 2.2);
  return world * 0.2 * Math.pow(fraction, 1.3) * bumps;
}

function ringMesh(radii, heights, colours, segments, material) {
  // A band all the way round, made of rings of points: radii[r] and
  // colours[r] for each ring, heights(r, angle) for how high each point is.
  var positions = [];
  var pointColours = [];
  var indices = [];
  for (var r = 0; r < radii.length; r++) {
    for (var segment = 0; segment <= segments; segment++) {
      var angle = segment / segments * Math.PI * 2;
      positions.push(Math.cos(angle) * radii[r], heights(r, angle), Math.sin(angle) * radii[r]);
      pointColours.push(colours[r].r, colours[r].g, colours[r].b);
    }
  }
  for (var ring = 0; ring < radii.length - 1; ring++) {
    for (var s = 0; s < segments; s++) {
      var p0 = ring * (segments + 1) + s;
      var p1 = p0 + 1;
      var p2 = p0 + segments + 1;
      var p3 = p2 + 1;
      indices.push(p0, p2, p1, p1, p2, p3);
    }
  }
  var geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(pointColours, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return new THREE.Mesh(geometry, material);
}

function makeFarWoodsMaterial() {
  // The far woods' trees are plain shapes; darker low down, where they
  // shade each other, and dappled, so from far off they look like a
  // canopy of leaves rather than smooth balls and cones.
  var material = new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, envMapIntensity: 0.6 });
  function onBeforeCompile(shader) {
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vWoodPlace;\nvarying float vWoodHeight;")
      .replace("#include <project_vertex>", "#include <project_vertex>\nvWoodHeight = position.y;\nvWoodPlace = (modelMatrix * instanceMatrix * vec4(transformed, 1.0)).xyz;");
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vWoodPlace;\nvarying float vWoodHeight;\n" + SCENE_NOISE_GLSL)
      .replace("#include <color_fragment>", [
        "#include <color_fragment>",
        "float dapple = sceneNoise(vWoodPlace.xz * 0.9 + vWoodPlace.y * 1.3) * 0.6 + sceneNoise(vWoodPlace.zy * 2.1 + vWoodPlace.x * 0.7) * 0.4;",
        "diffuseColor.rgb *= (0.45 + 0.9 * dapple) * mix(0.35, 1.0, smoothstep(0.05, 0.9, vWoodHeight));"
      ].join("\n"));
  }
  material.onBeforeCompile = onBeforeCompile;
  return material;
}

function joinGeometries(parts) {
  // One geometry from several (their points and normals, without indices).
  var positions = [];
  var normals = [];
  for (var p = 0; p < parts.length; p++) {
    var part = parts[p].index ? parts[p].toNonIndexed() : parts[p];
    positions.push.apply(positions, part.attributes.position.array);
    normals.push.apply(normals, part.attributes.normal.array);
  }
  var geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  return geometry;
}

function farConiferGeometry() {
  // a distant conifer: three cones stacked, 1 high and 0.5 across at the base
  var tiers = [];
  for (var t = 0; t < 3; t++) {
    var tier = new THREE.ConeGeometry(0.5 - t * 0.12, 0.5, 7, 1, true);
    tier.translate(0, 0.25 + t * 0.25, 0);
    tiers.push(tier);
  }
  return joinGeometries(tiers);
}

function farCrownGeometry() {
  // a distant broadleaved tree: a lumpy ball, 1 across, on the ground
  // (the normals stay those of a smooth ball, so it is shaded softly)
  var ball = new THREE.IcosahedronGeometry(0.5, 2);
  var place = ball.attributes.position;
  var normal = ball.attributes.normal;
  var point = new THREE.Vector3();
  for (var i = 0; i < place.count; i++) {
    point.fromBufferAttribute(place, i);
    normal.setXYZ(i, point.x * 2, point.y * 2, point.z * 2);
    var lumps = 1 + 0.14 * Math.sin(point.x * 17 + 1.3) * Math.sin(point.y * 19 + 0.7) * Math.sin(point.z * 23 + 2.1);
    point.multiplyScalar(lumps);
    place.setXYZ(i, point.x, point.y * 0.9 + 0.5, point.z);
  }
  return ball;
}

function buildFarLand(state, world, size, baseHeight) {
  // Decoration beyond the ground, all round: low hills with woods on them,
  // and a line of mountains further off. None of it is simulated. The hills
  // and woods fade in the fog, like the rest of the land; the mountains
  // fade into the haze by their own colours (not the fog), so they stay a
  // little darker than the sky behind them.
  var old = [state.farHills, state.farWoods, state.farMountains];
  function disposeGeometry(part) {
    if (part.geometry) {
      part.geometry.dispose();
    }
  }
  for (var o = 0; o < old.length; o++) {
    if (old[o]) {
      state.scene.remove(old[o]);
      old[o].traverse(disposeGeometry);
    }
  }
  var near = new THREE.Color(0.1, 0.18, 0.045);
  var far = new THREE.Color(0.15, 0.21, 0.28);
  // the hills start under the edge of the ground, so there is no gap
  var inner = size * 0.46;
  var reach = world * 5;

  // the hills
  var rings = 12;
  var radii = [];
  var colours = [];
  for (var ringNumber = 0; ringNumber <= rings; ringNumber++) {
    var out = ringNumber / rings;
    radii.push(inner + out * reach);
    colours.push(near.clone().lerp(far, Math.max(0, out - 0.25) / 0.75 * 0.7));
  }
  function hillHeight(ring, angle) {
    return baseHeight - 1 + farHillRise(world, angle, ring / rings);
  }
  state.farHills = ringMesh(radii, hillHeight, colours, 180, state.materials.farHills);
  state.scene.add(state.farHills);

  // woods on the hills, well away from the simulated world: simple cones
  // (conifers) and rounded crowns (broadleaved trees) crowded together in
  // patches, too far away to need more
  var random = makeRandom(211);
  var count = 4000;
  var cone = farConiferGeometry();
  var round = farCrownGeometry();
  var coneWoods = new THREE.InstancedMesh(cone, state.materials.farWoods, count);
  var roundWoods = new THREE.InstancedMesh(round, state.materials.farWoods, count);
  var matrix = new THREE.Matrix4();
  var turn = new THREE.Quaternion();
  var place = new THREE.Vector3();
  var scale = new THREE.Vector3();
  var colour = new THREE.Color();
  var cones = 0;
  var rounds = 0;
  for (var tries = 0; tries < count * 8 && cones + rounds < count; tries++) {
    var angle = random() * Math.PI * 2;
    var fraction = 0.22 + Math.pow(random(), 1.2) * 0.55;
    var woods = 0.5 + 0.5 * Math.sin(angle * 6 + 2 + Math.sin(fraction * 9) * 1.5) * Math.sin(fraction * 13 + angle * 3);
    if (random() > woods * 1.8 - 0.6) {
      continue;
    }
    var radius = inner + fraction * reach;
    place.set(Math.cos(angle) * radius, baseHeight - 1.6 + farHillRise(world, angle, fraction), Math.sin(angle) * radius);
    var tall = 7 + random() * 7;
    var conifer = random() < 0.4;
    var wide = tall * (conifer ? 0.4 : 0.8) * (0.8 + random() * 0.4);
    scale.set(wide, conifer ? tall : tall * 0.85, wide);
    turn.setFromAxisAngle(new THREE.Vector3(0, 1, 0), random() * 6.3);
    matrix.compose(place, turn, scale);
    if (conifer) {
      colour.setRGB(0.022, 0.048, 0.03);
    } else {
      colour.setRGB(0.04, 0.07, 0.024);
    }
    colour.multiplyScalar(0.7 + random() * 0.6);
    if (conifer) {
      coneWoods.setMatrixAt(cones, matrix);
      coneWoods.setColorAt(cones, colour);
      cones += 1;
    } else {
      roundWoods.setMatrixAt(rounds, matrix);
      roundWoods.setColorAt(rounds, colour);
      rounds += 1;
    }
  }
  coneWoods.count = cones;
  roundWoods.count = rounds;
  var woodsGroup = new THREE.Group();
  woodsGroup.add(coneWoods);
  woodsGroup.add(roundWoods);
  state.farWoods = woodsGroup;
  state.scene.add(woodsGroup);

  // mountains on the skyline, blue with distance
  // (only the side that faces the world: from high up, you see the sky
  // over the top of them, not their far side)
  var mountainRadii = [world * 7.5, world * 9];
  var foot = new THREE.Color(0.08, 0.12, 0.16);
  var ridge = new THREE.Color(0.13, 0.18, 0.26);
  function mountainHeight(ring, angle) {
    if (ring === 0) {
      return baseHeight - 12;
    }
    var peaks = 0;
    var sizes = [3, 7, 11, 19, 31];
    for (var k = 0; k < sizes.length; k++) {
      var crest = 1 - Math.abs(Math.sin(angle * sizes[k] * 0.5 + k * 1.7));
      peaks += crest * crest / (1 + k * 0.6);
    }
    return baseHeight + world * (0.2 + 0.8 * peaks / 2.4);
  }
  state.farMountains = ringMesh(mountainRadii, mountainHeight, [foot, ridge], 360, state.materials.farMountains);
  state.scene.add(state.farMountains);
}
