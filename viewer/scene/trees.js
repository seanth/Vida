// Vida viewer, natural scene: the trees.
//
// Drawn to scale from the simulation (see the top of scene.js): each stem is
// a cylinder of the stem's height and width, and each crown is as wide as
// the canopy radius with its top at the top of the stem. The crown is filled
// with clumps of leaves, layer by layer. Leaves are darker when the plant
// got less light.
//
// The crown's outline can be drawn two ways (the Crowns control):
//   - as Vida draws it in its 3D (.dxf) files: the top half of a sphere, as
//     deep as it is wide or, for crownShape PARA, reaching from boleHeight
//     percent of the way down the tree to the top;
//   - shaped by genus (the first word of the species name): decoration, so
//     the kinds of tree can be told apart. A pine grows a long bare trunk
//     with its crown near the top, an oak a broad rounded crown, a dogwood a
//     low flat-topped one, a sweetgum a pointed one, and so on (CROWN_FORMS
//     below). Young trees of every kind have fuller, more pointed crowns.
//     The height and the canopy radius are still the plant's own.
//
// The wind sways the clumps a few centimetres and flutters the leaves, and
// leaves glow when the sun shines through them from behind: decoration.

"use strict";

// Leaves by genus (the first word of the species name): their colour in
// summer, and which kind of leaf (see LEAF_KINDS). Pines have long needles
// in tufts; spruces, firs and the like short needles; the broadleaved trees
// their own leaf shapes. Anything not listed is a broadleaved tree.
var FOLIAGE = {
  Pinus: { colour: "#4e6b2e", leaf: "pine" },
  Picea: { colour: "#2f5238", leaf: "fir" },
  Abies: { colour: "#2c5236", leaf: "fir" },
  Tsuga: { colour: "#355a36", leaf: "fir" },
  Juniperus: { colour: "#4d6344", leaf: "fir" },
  Taxodium: { colour: "#5b7a34", leaf: "fir" },
  Gymnosperm: { colour: "#3f6035", leaf: "fir" },
  Acer: { colour: "#4f7f2f", leaf: "maple" },
  Quercus: { colour: "#46672a", leaf: "oak" },
  Carya: { colour: "#5d7f2d", leaf: "hickory" },
  Cornus: { colour: "#5b8537", leaf: "oval" },
  Liquidambar: { colour: "#4d7c2b", leaf: "sweetgum" },
  Liriodendron: { colour: "#5a8a31", leaf: "maple" },
  Magnolia: { colour: "#3c5f2c", leaf: "magnolia" },
  Nyssa: { colour: "#46702d", leaf: "oval" },
  Prunus: { colour: "#4b6f2a", leaf: "oval" },
  Fagus: { colour: "#5a7f33", leaf: "oval" },
  Betula: { colour: "#6a8c35", leaf: "oval" },
  Castanea: { colour: "#4f732c", leaf: "oval" },
  Angiosperm: { colour: "#52792f", leaf: "oval" }
};
var DEFAULT_FOLIAGE = { colour: "#52792f", leaf: "oval" };

// The kinds of leaf, each drawn as its own set of clumps: [kind, how many
// cards of leaves a clump has, how big each card is]. The pictures on the
// cards are in textures.js.
var LEAF_KINDS = [
  ["pine", 46, 0.9],
  ["fir", 46, 0.82],
  ["oval", 44, 0.8],
  ["magnolia", 42, 0.85],
  ["oak", 44, 0.82],
  ["maple", 44, 0.82],
  ["sweetgum", 44, 0.82],
  ["hickory", 42, 0.9]
];

function hasNeedles(leaf) {
  return leaf === "pine" || leaf === "fir";
}

function foliageFor(speciesName) {
  var words = String(speciesName || "").split(/[_\s]+/);
  for (var i = 0; i < words.length; i++) {
    if (FOLIAGE[words[i]]) {
      return FOLIAGE[words[i]];
    }
  }
  return DEFAULT_FOLIAGE;
}

// Crown outlines by genus, for grown trees (decoration; see the top of this
// file). The crown is as wide as the canopy radius where it is widest.
//   depth:  how much of the tree's height the crown takes up
//   widest: how far down the crown it is widest (0 at the top, 1 at the bottom)
//   top:    the shape above the widest point: 1 pointed, 2 round, 4 flat-topped
//   bottom: the shape below the widest point, the same way
//   base:   how wide the bottom of the crown is, as a part of the widest
//   gaps:   how many clumps of leaves are left out, for an open, tufted crown
var CROWN_FORMS = {
  Pinus: { depth: 0.36, widest: 0.45, top: 2.2, bottom: 1.6, base: 0.3, gaps: 0.3 },
  Picea: { depth: 0.85, widest: 0.95, top: 1, bottom: 3, base: 0.85, gaps: 0 },
  Abies: { depth: 0.85, widest: 0.95, top: 1, bottom: 3, base: 0.85, gaps: 0 },
  Tsuga: { depth: 0.8, widest: 0.85, top: 1.2, bottom: 2, base: 0.7, gaps: 0.05 },
  Juniperus: { depth: 0.85, widest: 0.7, top: 1.2, bottom: 2, base: 0.6, gaps: 0 },
  Taxodium: { depth: 0.7, widest: 0.8, top: 1.1, bottom: 2, base: 0.6, gaps: 0.1 },
  Gymnosperm: { depth: 0.8, widest: 0.9, top: 1.1, bottom: 2, base: 0.7, gaps: 0.05 },
  Acer: { depth: 0.66, widest: 0.5, top: 2, bottom: 2, base: 0.3, gaps: 0.05 },
  Quercus: { depth: 0.6, widest: 0.5, top: 2.6, bottom: 1.8, base: 0.35, gaps: 0.12 },
  Carya: { depth: 0.55, widest: 0.45, top: 1.8, bottom: 2, base: 0.35, gaps: 0.1 },
  Cornus: { depth: 0.72, widest: 0.3, top: 4, bottom: 1.5, base: 0.35, gaps: 0.1 },
  Liquidambar: { depth: 0.62, widest: 0.8, top: 1.25, bottom: 2, base: 0.5, gaps: 0.05 },
  Liriodendron: { depth: 0.55, widest: 0.6, top: 1.5, bottom: 2, base: 0.4, gaps: 0.05 },
  Magnolia: { depth: 0.7, widest: 0.5, top: 2, bottom: 2.5, base: 0.4, gaps: 0 },
  Nyssa: { depth: 0.6, widest: 0.75, top: 1.35, bottom: 2, base: 0.5, gaps: 0.08 },
  Prunus: { depth: 0.55, widest: 0.5, top: 2, bottom: 2, base: 0.3, gaps: 0.12 },
  Fagus: { depth: 0.75, widest: 0.6, top: 2.2, bottom: 2, base: 0.4, gaps: 0.02 },
  Betula: { depth: 0.6, widest: 0.5, top: 1.6, bottom: 2, base: 0.35, gaps: 0.1 },
  Castanea: { depth: 0.6, widest: 0.5, top: 2.5, bottom: 1.8, base: 0.35, gaps: 0.08 },
  Angiosperm: { depth: 0.62, widest: 0.5, top: 2, bottom: 2, base: 0.3, gaps: 0.05 }
};
var DEFAULT_BROADLEAF_FORM = CROWN_FORMS.Angiosperm;
var DEFAULT_CONIFER_FORM = CROWN_FORMS.Gymnosperm;
// a young tree of any kind: a fuller crown, reaching low, pointed at the top
var YOUNG_FORM = { depth: 0.85, widest: 0.8, top: 1.4, bottom: 2, base: 0.6, gaps: 0 };
// Vida's own crown: the top half of a sphere (or of an ellipse, for PARA)
var VIDA_FORM = { depth: null, widest: 1, top: 2, bottom: 2, base: 1, gaps: 0 };

function crownFormFor(speciesName, needles) {
  var words = String(speciesName || "").split(/[_\s]+/);
  for (var i = 0; i < words.length; i++) {
    if (CROWN_FORMS[words[i]]) {
      return CROWN_FORMS[words[i]];
    }
  }
  return needles ? DEFAULT_CONIFER_FORM : DEFAULT_BROADLEAF_FORM;
}

function grownFormAt(form, height) {
  // A tree's crown form at its height: like a young tree's when small,
  // becoming its genus's form as it grows from 3 m to 12 m tall.
  var youth = 1 - smoothStep(3, 12, height);
  var blended = {};
  var keys = ["depth", "widest", "top", "bottom", "base", "gaps"];
  for (var k = 0; k < keys.length; k++) {
    blended[keys[k]] = form[keys[k]] + (YOUNG_FORM[keys[k]] - form[keys[k]]) * youth;
  }
  return blended;
}

function colourFromHsv(hsv) {
  // Vida stores colours as [hue in degrees, saturation 0-1, brightness 0-1]
  var hue = ((hsv[0] % 360) + 360) % 360 / 60;
  var s = hsv[1];
  var v = hsv[2];
  var c = v * s;
  var x = c * (1 - Math.abs((hue % 2) - 1));
  var r = 0;
  var g = 0;
  var b = 0;
  if (hue < 1) { r = c; g = x; } else if (hue < 2) { r = x; g = c; } else if (hue < 3) { g = c; b = x; }
  else if (hue < 4) { g = x; b = c; } else if (hue < 5) { r = x; b = c; } else { r = c; b = x; }
  var m = v - c;
  var colour = new THREE.Color();
  colour.setRGB(r + m, g + m, b + m);
  colour.convertSRGBToLinear();
  return colour;
}

// ---------------------------------------------------------------------------
// Shapes
// ---------------------------------------------------------------------------

function clumpCoreGeometry() {
  // the inside of a clump of leaves: a lumpy ball, darker than the leaves,
  // so there are no holes to see through
  var geometry = new THREE.IcosahedronGeometry(0.56, 1);
  var position = geometry.attributes.position;
  var point = new THREE.Vector3();
  for (var i = 0; i < position.count; i++) {
    point.fromBufferAttribute(position, i);
    // a smooth bump that depends only on where the point is, so the copies
    // of a corner shared by two triangles move together
    var bump = 1 + 0.12 * Math.sin(3.1 * point.x + 1.3) * Math.sin(3.7 * point.y + 0.4) * Math.sin(2.9 * point.z + 2.1);
    point.multiplyScalar(bump);
    position.setXYZ(i, point.x, point.y, point.z);
  }
  geometry.computeVertexNormals();
  return geometry;
}

function clumpLeavesGeometry(cards, cardSize, start) {
  // Many small squares ("cards") with leaves drawn on them, scattered over a
  // ball of radius 1, facing roughly outwards. They are lit as if facing
  // outwards and a little up, so a crown looks like one soft mass of leaves.
  var random = makeRandom(start);
  var positions = [];
  var normals = [];
  var uvs = [];
  var indices = [];
  var outward = new THREE.Vector3();
  var facing = new THREE.Vector3();
  var across = new THREE.Vector3();
  var up = new THREE.Vector3();
  var centre = new THREE.Vector3();
  var helper = new THREE.Vector3();
  var lit = new THREE.Vector3();
  var skyward = new THREE.Vector3(0, 0.55, 0);
  for (var i = 0; i < cards; i++) {
    var z = random() * 2 - 1;
    var angle = random() * Math.PI * 2;
    var ring = Math.sqrt(1 - z * z);
    outward.set(ring * Math.cos(angle), z, ring * Math.sin(angle));
    centre.copy(outward).multiplyScalar(0.5 + random() * 0.45);
    lit.copy(outward).multiplyScalar(0.7).add(skyward).normalize();
    facing.set(random() - 0.5, random() - 0.5, random() - 0.5).multiplyScalar(0.9).add(outward).normalize();
    if (Math.abs(facing.y) > 0.95) {
      helper.set(1, 0, 0);
    } else {
      helper.set(0, 1, 0);
    }
    across.crossVectors(helper, facing).normalize();
    up.crossVectors(facing, across).normalize();
    var spin = random() * Math.PI * 2;
    var cosine = Math.cos(spin) * cardSize / 2;
    var sine = Math.sin(spin) * cardSize / 2;
    var corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
    var start = positions.length / 3;
    for (var c = 0; c < 4; c++) {
      var a = corners[c][0];
      var b = corners[c][1];
      positions.push(
        centre.x + across.x * (a * cosine - b * sine) + up.x * (a * sine + b * cosine),
        centre.y + across.y * (a * cosine - b * sine) + up.y * (a * sine + b * cosine),
        centre.z + across.z * (a * cosine - b * sine) + up.z * (a * sine + b * cosine));
      normals.push(lit.x, lit.y, lit.z);
      uvs.push((a + 1) / 2, (b + 1) / 2);
    }
    indices.push(start, start + 1, start + 2, start, start + 2, start + 3);
  }
  var geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  return geometry;
}

function vidaCrownDepth(species, stemHeight, canopyRadius) {
  // how far down from the top of the stem Vida's crown reaches (see the top of this file)
  if (species && species.crownShape === "PARA" && species.boleHeight !== null && species.boleHeight !== undefined) {
    return stemHeight * species.boleHeight / 100;
  }
  return canopyRadius;
}

function crownFor(state, speciesNumber, species, stemHeight, canopyRadius) {
  // The outline of one plant's crown: { form, depth } (see the top of this file)
  if (state.crownForms === "vida") {
    return { form: VIDA_FORM, depth: vidaCrownDepth(species, stemHeight, canopyRadius) };
  }
  var form = grownFormAt(state.crownFormsBySpecies[speciesNumber] || DEFAULT_BROADLEAF_FORM, stemHeight);
  return { form: form, depth: stemHeight * form.depth };
}

function widthAt(form, radius, depth, above) {
  // The radius of the crown at a height `above` its bottom: a curve from
  // the top down to the widest point, and another from there to the bottom.
  // (Vida's form is widest at the bottom, so it is all the first curve: the
  // top half of an ellipse.)
  var down = 1 - Math.max(0, Math.min(1, above / depth));
  if (down <= form.widest) {
    var fromWidest = form.widest > 0 ? (form.widest - down) / form.widest : 0;
    return radius * Math.pow(1 - Math.pow(fromWidest, form.top), 1 / form.top);
  }
  var towardsBottom = (down - form.widest) / (1 - form.widest);
  var curve = Math.pow(1 - Math.pow(towardsBottom, form.bottom), 1 / form.bottom);
  return radius * (form.base + (1 - form.base) * curve);
}

function layerCount(width, size) {
  if (width <= size * 1.15) {
    return 1;
  }
  var ring = Math.max(3, Math.round(2 * Math.PI * (width - size) / (size * 1.3)));
  if (width > size * 2.6) {
    return ring + 1;
  }
  return ring;
}

function estimateClumps(form, radius, depth, size) {
  var total = 1;
  var step = size * 0.9;
  for (var above = Math.min(depth * 0.5, size * 0.75); above < depth - size * 0.9; above += step) {
    total += layerCount(widthAt(form, radius, depth, above), size);
  }
  return total;
}

function addLayer(clumps, random, x, z, height, width, size, fraction, gaps) {
  // one layer of clumps: a ring round the edge of the crown at this height,
  // and one in the middle if the crown is wide there. The last number of
  // each clump is how far up the crown it is (0 bottom, 1 top). In an open
  // crown (gaps) some of the ring is left out.
  var count = layerCount(width, size);
  if (count === 1) {
    var small = Math.max(0.03, Math.min(size, width));
    clumps.push([x + (random() - 0.5) * 0.2 * small, height, z + (random() - 0.5) * 0.2 * small, small, fraction]);
    return;
  }
  var ring = count;
  if (width > size * 2.6) {
    ring = count - 1;
    clumps.push([x, height + (random() - 0.5) * size * 0.3, z, size, fraction * 0.7]);
  }
  var reach = width - size;
  var phase = random() * Math.PI * 2;
  for (var i = 0; i < ring; i++) {
    var angle = phase + (i + (random() - 0.5) * 0.4) / ring * Math.PI * 2;
    var along = reach * (0.9 + random() * 0.1);
    var leaveOut = random() < gaps && ring > 4;
    if (!leaveOut) {
      clumps.push([x + Math.cos(angle) * along, height + (random() - 0.5) * size * 0.6,
        z + Math.sin(angle) * along, size * (0.8 + random() * 0.2), fraction]);
    }
  }
}

function crownClumps(x, top, z, radius, crown, clumpBudget) {
  // Where to put the clumps of leaves that make up a crown, as
  // [x, y, z, clump radius, height in the crown], filling the crown's
  // outline (crown.form), `radius` wide at its widest and crown.depth deep,
  // with its top at `top`. The same plant always gets the same clumps.
  var random = makeRandom(randomStartFor(x, z));
  var depth = crown.depth;
  var size = Math.max(0.04, Math.min(1.6, Math.min(radius, depth) * 0.6));
  var needed = estimateClumps(crown.form, radius, depth, size);
  if (needed > clumpBudget) {
    size = size * Math.sqrt(needed / clumpBudget);
    size = Math.min(size, Math.min(radius, depth));
  }
  var base = top - depth;
  var clumps = [];
  var step = size * 0.9;
  var height = base + Math.min(depth * 0.5, size * 0.75);
  while (height < top - size * 0.9) {
    addLayer(clumps, random, x, z, height, widthAt(crown.form, radius, depth, height - base), size, (height - base) / depth, crown.form.gaps);
    height += step * (0.85 + random() * 0.3);
  }
  clumps.push([x, top - size, z, size, 1]);
  return clumps;
}

// ---------------------------------------------------------------------------
// Materials: wind and light through the leaves
// ---------------------------------------------------------------------------

var WIND_VERTEX = [
  "vec3 clumpOrigin = vec3(instanceMatrix[3]);",
  "float swayPhase = time * 1.1 + clumpOrigin.x * 0.31 + clumpOrigin.z * 0.23;",
  "float sway = (sin(swayPhase) * 0.6 + sin(swayPhase * 2.27 + 1.7) * 0.3) * windStrength;",
  "transformed.x += sway * 0.06 * (position.y + 1.2);",
  "transformed.z += sway * 0.035 * (position.y + 1.2);",
  "transformed += normal * sin(time * 6.5 + position.x * 13.0 + position.z * 11.0 + clumpOrigin.x) * 0.02 * windStrength;"
].join("\n");

function addWind(state, material, withGlow) {
  function onBeforeCompile(shader) {
    shader.uniforms.time = state.uniforms.time;
    shader.uniforms.windStrength = state.uniforms.windStrength;
    shader.uniforms.sunColour = state.uniforms.sunColour;
    shader.uniforms.sunDirectionView = state.uniforms.sunDirectionView;
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nuniform float time;\nuniform float windStrength;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\n" + WIND_VERTEX);
    if (withGlow) {
      shader.fragmentShader = shader.fragmentShader
        .replace("#include <common>", "#include <common>\nuniform vec3 sunColour;\nuniform vec3 sunDirectionView;")
        // both sides of a leaf card are lit as facing out of the clump
        .replace("#include <normal_fragment_begin>", "#include <normal_fragment_begin>\nnormal = normalize(vNormal);")
        .replace("#include <output_fragment>", [
          "float throughLeaves = pow(clamp(dot(normalize(-vViewPosition), sunDirectionView), 0.0, 1.0), 5.0);",
          "outgoingLight += diffuseColor.rgb * sunColour * throughLeaves * 1.6;",
          "#include <output_fragment>"
        ].join("\n"));
    }
  }
  material.onBeforeCompile = onBeforeCompile;
  // a different key for each kind, so three.js keeps their shaders apart
  material.customProgramCacheKey = function cacheKey() {
    return withGlow ? "vida-leaves-glow" : "vida-leaves";
  };
  return material;
}

function makeTreeMeshes(state, textures) {
  var stemGeometry = new THREE.CylinderGeometry(1, 1, 1, 12, 1, false);
  stemGeometry.translate(0, 0.5, 0);
  state.materials.stem = new THREE.MeshStandardMaterial({ map: textures.bark.colour, normalMap: textures.bark.normal,
    normalScale: new THREE.Vector2(2.2, 2.2), roughness: 0.95, metalness: 0, envMapIntensity: 0.45 });
  makeInstanced(state, "stems", stemGeometry, state.materials.stem, true);

  // for each kind of leaf, the cards of leaves, and a dark core inside each
  // clump so there are no holes to see through
  var core = clumpCoreGeometry();
  var coreMaterial = addWind(state, new THREE.MeshStandardMaterial({ roughness: 1.0, metalness: 0, envMapIntensity: 0.25 }), false);
  var coreDepth = addWind(state, new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking }), false);
  for (var i = 0; i < LEAF_KINDS.length; i++) {
    var key = LEAF_KINDS[i][0];
    var texture = textures.leaves[key];
    var cardMaterial = addWind(state, new THREE.MeshStandardMaterial({ map: texture, alphaTest: 0.5, side: THREE.DoubleSide,
      roughness: key === "magnolia" ? 0.6 : 0.88, metalness: 0, envMapIntensity: 0.32 }), true);
    var cards = makeInstanced(state, key + "Leaves", clumpLeavesGeometry(LEAF_KINDS[i][1], LEAF_KINDS[i][2], 101 + i), cardMaterial, true);
    var depthMaterial = addWind(state, new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: texture, alphaTest: 0.5 }), false);
    cards.customDepthMaterial = depthMaterial;
    var coreMesh = makeInstanced(state, key + "Core", core, coreMaterial, true);
    coreMesh.customDepthMaterial = coreDepth;
  }
}

function makeInstanced(state, key, geometry, material, castShadow) {
  var mesh = new THREE.InstancedMesh(geometry, material, 64);
  mesh.userData.capacity = 64;
  // give it colours now: three.js makes its shaders the first time it draws,
  // and only uses the colours if there were some then
  mesh.setColorAt(0, new THREE.Color(1, 1, 1));
  mesh.count = 0;
  mesh.castShadow = castShadow;
  mesh.receiveShadow = true;
  mesh.frustumCulled = false;
  state.scene.add(mesh);
  state.meshes[key] = mesh;
  return mesh;
}

function ensureCapacity(state, key, needed) {
  // an InstancedMesh has a fixed size; make a bigger one when there are more trees
  var mesh = state.meshes[key];
  if (mesh.userData.capacity >= needed) {
    return mesh;
  }
  var capacity = Math.max(needed, Math.ceil(mesh.userData.capacity * 1.6));
  var bigger = new THREE.InstancedMesh(mesh.geometry, mesh.material, capacity);
  bigger.userData.capacity = capacity;
  bigger.setColorAt(0, new THREE.Color(1, 1, 1));
  bigger.castShadow = mesh.castShadow;
  bigger.receiveShadow = mesh.receiveShadow;
  bigger.customDepthMaterial = mesh.customDepthMaterial;
  bigger.frustumCulled = false;
  state.scene.remove(mesh);
  mesh.dispose();
  state.scene.add(bigger);
  state.meshes[key] = bigger;
  return bigger;
}

// ---------------------------------------------------------------------------
// One cycle's trees
// ---------------------------------------------------------------------------

function setTreeSpecies(state, theRun) {
  // each species' leaf colour and crown form (from its genus) and bark colour
  state.foliage = [];
  state.bark = [];
  state.crownFormsBySpecies = [];
  for (var s = 0; s < theRun.species.length; s++) {
    var species = theRun.species[s];
    var foliage = foliageFor(species ? species.name : "");
    var colour = new THREE.Color(foliage.colour);
    // each species a little different, so neighbours can be told apart
    var random = makeRandom(s * 7919 + 17);
    var hsl = {};
    colour.getHSL(hsl);
    colour.setHSL(hsl.h + (random() - 0.5) * 0.035, hsl.s * (0.9 + random() * 0.2), hsl.l * (0.92 + random() * 0.16));
    state.foliage.push({ colour: colour, leaf: foliage.leaf });
    state.crownFormsBySpecies.push(crownFormFor(species ? species.name : "", hasNeedles(foliage.leaf)));
    var bark = species && species.stemColour ? colourFromHsv(species.stemColour) : new THREE.Color("#5b4636");
    bark.lerp(new THREE.Color("#6b635a"), 0.85);
    state.bark.push(bark);
  }
}

function placeTrees(state, theRun, cycle, options, clumpTotal) {
  // Put every plant of one cycle in the scene.
  var index = theRun.fieldIndex;
  var plants = cycle.plants;
  var matrix = new THREE.Matrix4();
  var rotation = new THREE.Quaternion();
  var noTurn = new THREE.Quaternion();
  var scale = new THREE.Vector3();
  var place = new THREE.Vector3();
  var colour = new THREE.Color();
  var clumpColour = new THREE.Color();
  var inner = new THREE.Color();
  var dim = new THREE.Color("#5f6358");
  var turnAxis = new THREE.Vector3();

  var stems = ensureCapacity(state, "stems", plants.length);
  // share the clumps out: a crown may have a little more than its share,
  // since most crowns need fewer
  var clumpBudget = Math.max(3, 1.3 * clumpTotal / Math.max(1, plants.length));
  var crowns = [];
  var needed = {};
  var counts = {};
  for (var kind = 0; kind < LEAF_KINDS.length; kind++) {
    needed[LEAF_KINDS[kind][0]] = 0;
    counts[LEAF_KINDS[kind][0] + "Leaves"] = 0;
    counts[LEAF_KINDS[kind][0] + "Core"] = 0;
  }
  for (var q = 0; q < plants.length; q++) {
    var p0 = plants[q];
    var h0 = Math.max(p0[index.stemHeight], 0.001);
    var r0 = Math.max(p0[index.canopyRadius], 0.01);
    var top0 = (p0[index.elevation] || 0) + h0;
    var crown = crownFor(state, p0[index.species], theRun.species[p0[index.species]], h0, r0);
    crown.depth = Math.max(crown.depth, 0.01);
    var list = crownClumps(p0[index.x], top0, -p0[index.y], r0, crown, clumpBudget);
    crowns.push(list);
    var leaf0 = (state.foliage[p0[index.species]] || DEFAULT_FOLIAGE).leaf;
    needed[leaf0] += list.length;
  }
  var meshes = {};
  for (var m = 0; m < LEAF_KINDS.length; m++) {
    var leafKind = LEAF_KINDS[m][0];
    meshes[leafKind + "Leaves"] = ensureCapacity(state, leafKind + "Leaves", needed[leafKind] + 1);
    meshes[leafKind + "Core"] = ensureCapacity(state, leafKind + "Core", needed[leafKind] + 1);
  }

  for (var p = 0; p < plants.length; p++) {
    var plant = plants[p];
    var x = plant[index.x];
    var y = plant[index.y];
    var base = plant[index.elevation] || 0;
    var stemRadius = Math.max(plant[index.stemRadius], 0.002);
    var stemHeight = Math.max(plant[index.stemHeight], 0.001);
    var speciesNumber = plant[index.species];
    var light = plant[index.light];
    if (light === null || light === undefined) {
      light = 1;
    }
    var faded = options.highlight >= 0 && speciesNumber !== options.highlight;

    // the stem, from a little below the ground (so it never floats) to its top
    var sink = Math.min(0.4, stemHeight * 0.2);
    place.set(x, base - sink, -y);
    scale.set(stemRadius, stemHeight + sink, stemRadius);
    matrix.compose(place, noTurn, scale);
    stems.setMatrixAt(p, matrix);
    colour.copy(state.bark[speciesNumber] || dim);
    if (faded) {
      colour.lerp(dim, 0.6);
    }
    stems.setColorAt(p, colour);

    // the crown
    var foliage = state.foliage[speciesNumber] || { colour: new THREE.Color(DEFAULT_FOLIAGE.colour), leaf: DEFAULT_FOLIAGE.leaf };
    if (options.colourBy === "light" && options.lightColour) {
      colour.set(options.lightColour(light));
    } else {
      colour.copy(foliage.colour);
      // leaves in the shade are darker, as Vida's own pictures show them
      colour.multiplyScalar(0.5 + 0.5 * Math.max(0, Math.min(1, light)));
    }
    if (faded) {
      colour.lerp(dim, 0.75);
    }
    var style = foliage.leaf;
    var leavesMesh = meshes[style + "Leaves"];
    var coreMesh = meshes[style + "Core"];
    var clumps = crowns[p];
    var turnRandom = makeRandom(randomStartFor(x, y) + 3);
    for (var c = 0; c < clumps.length; c++) {
      var clump = clumps[c];
      place.set(clump[0], clump[1], clump[2]);
      turnAxis.set(turnRandom() - 0.5, 1.5, turnRandom() - 0.5).normalize();
      rotation.setFromAxisAngle(turnAxis, turnRandom() * Math.PI * 2);
      scale.set(clump[3], clump[3], clump[3]);
      matrix.compose(place, rotation, scale);
      // lower in the crown is darker (the leaves above shade it), and each
      // clump a little different
      clumpColour.copy(colour).multiplyScalar((0.72 + 0.28 * clump[4]) * (0.9 + turnRandom() * 0.2));
      leavesMesh.setMatrixAt(counts[style + "Leaves"], matrix);
      leavesMesh.setColorAt(counts[style + "Leaves"], clumpColour);
      counts[style + "Leaves"] += 1;
      coreMesh.setMatrixAt(counts[style + "Core"], matrix);
      inner.copy(clumpColour).multiplyScalar(0.34);
      coreMesh.setColorAt(counts[style + "Core"], inner);
      counts[style + "Core"] += 1;
    }
  }
  stems.count = plants.length;
  for (var key in meshes) {
    meshes[key].count = counts[key];
    meshes[key].instanceMatrix.needsUpdate = true;
    meshes[key].instanceColor.needsUpdate = true;
  }
  stems.instanceMatrix.needsUpdate = true;
  stems.instanceColor.needsUpdate = true;
}
