// Vida viewer: the natural scene, drawn in 3D with three.js (lib/three.min.js).
//
// What comes from the simulation is drawn to scale:
//   - where each plant stands, and the height of the ground under it;
//   - the height and width of its stem (a cylinder, as in Vida's 3D files);
//   - the size and shape of its crown (see trees.js);
//   - the shape of the ground (from a terrain file) and the water level;
//   - how much light each plant got, which darkens its leaves;
//   - the shade of the canopies on the ground, straight down, which darkens
//     the ground and thins the grass (see ground.js).
// Everything else is decoration, to make it look like a real place: the
// leaves, bark, grass, sky, clouds, water, birds and so on, and the sun,
// which can be set to any time of day. Vida's own light comes straight
// down, which is the "overhead" setting.
//
// The scene is split into files, loaded in this order by viewer.js:
//   textures.js   textures and shader noise shared by the others
//   sky.js        the sky, the sun and the light they give
//   ground.js     the land, and the shade of the canopies on it
//   grass.js      grass
//   trees.js      stems and crowns
//   water.js      water
//   life.js       dust, birds and fireflies
//   post.js       bloom, the filmic curve and the colour grade
//   scene.js      this file: setting up, camera, quality, and drawing
//
// Coordinates: Vida's x is east, y is north and height is up. In three.js,
// y is up, so a point (x, y, height) in Vida is (x, height, -y) here.

"use strict";

var scene3d = null;   // everything the scene needs, made by sceneStart

// How much to draw. The first one that suits the device is picked, and the
// Quality menu changes it.
var SCENE_QUALITY = {
  high: { grass: 240000, clumps: 8000, reflection: 0.5, shadowMap: 4096, bloom: true, samples: 4, pixelRatio: 2 },
  medium: { grass: 90000, clumps: 5000, reflection: 0.35, shadowMap: 2048, bloom: true, samples: 2, pixelRatio: 1.5 },
  low: { grass: 25000, clumps: 2500, reflection: 0, shadowMap: 1024, bloom: false, samples: 0, pixelRatio: 1 }
};

function onPhone() {
  return /Mobi|Android|iPhone|iPad/.test(navigator.userAgent);
}

// ---------------------------------------------------------------------------
// Camera: drag to turn, pinch or scroll to zoom, two fingers or right-drag to move
// ---------------------------------------------------------------------------

function placeCamera(state) {
  var view = state.view;
  var flat = Math.cos(view.elevation) * view.distance;
  state.camera.position.set(
    view.target.x + Math.sin(view.azimuth) * flat,
    view.target.y + Math.sin(view.elevation) * view.distance,
    view.target.z + Math.cos(view.azimuth) * flat);
  // don't go under the ground or the water
  var floor = state.groundHeight(state.camera.position.x, -state.camera.position.z);
  if (state.water && state.water.visible) {
    floor = Math.max(floor, state.uniforms.waterLevel.value);
  }
  if (state.camera.position.y < floor + 0.6) {
    state.camera.position.y = floor + 0.6;
  }
  state.camera.lookAt(view.target);
}

function resetView(state, header) {
  var world = header.worldSize;
  var middle = state.groundHeight(0, 0);
  // stand further back on a tall, narrow screen, so the whole world fits
  var narrow = Math.sqrt(Math.max(1, 1.2 / state.camera.aspect));
  state.view = {
    target: new THREE.Vector3(0, middle + 2, 0),
    distance: world * 1.25 * narrow,
    azimuth: 0.65,
    elevation: 0.36
  };
  placeCamera(state);
}

function attachControls(state, canvas) {
  var pointers = {};
  var lastPinch = 0;
  var lastMiddle = null;

  function count() {
    return Object.keys(pointers).length;
  }
  function middleOf() {
    var keys = Object.keys(pointers);
    var x = 0;
    var y = 0;
    for (var i = 0; i < keys.length; i++) {
      x += pointers[keys[i]].x;
      y += pointers[keys[i]].y;
    }
    return { x: x / keys.length, y: y / keys.length };
  }
  function pinchLength() {
    var keys = Object.keys(pointers);
    var a = pointers[keys[0]];
    var b = pointers[keys[1]];
    return Math.hypot(a.x - b.x, a.y - b.y);
  }
  function turn(dx, dy) {
    state.view.azimuth -= dx * 0.006;
    state.view.elevation = Math.max(0.02, Math.min(1.5, state.view.elevation + dy * 0.005));
  }
  function zoom(factor) {
    var world = state.world || 100;
    state.view.distance = Math.max(1.5, Math.min(world * 4, state.view.distance * factor));
  }
  function move(dx, dy) {
    // slide the point we look at across the ground
    var scale = state.view.distance * 0.0016;
    var sin = Math.sin(state.view.azimuth);
    var cos = Math.cos(state.view.azimuth);
    state.view.target.x -= (dx * cos + dy * sin) * scale;
    state.view.target.z -= (-dx * sin + dy * cos) * scale;
    var limit = (state.world || 100) * 0.9;
    state.view.target.x = Math.max(-limit, Math.min(limit, state.view.target.x));
    state.view.target.z = Math.max(-limit, Math.min(limit, state.view.target.z));
    state.view.target.y = state.groundHeight(state.view.target.x, -state.view.target.z) + 2;
  }
  function changed() {
    state.touring = false;
    updateTourButton(state);
    placeCamera(state);
    requestSceneDraw();
  }
  function onDown(event) {
    canvas.setPointerCapture(event.pointerId);
    pointers[event.pointerId] = { x: event.clientX, y: event.clientY, button: event.button, shift: event.shiftKey };
    if (count() === 2) {
      lastPinch = pinchLength();
      lastMiddle = middleOf();
    }
  }
  function onMove(event) {
    var pointer = pointers[event.pointerId];
    if (!pointer) {
      return;
    }
    var dx = event.clientX - pointer.x;
    var dy = event.clientY - pointer.y;
    if (count() === 1) {
      if (pointer.button === 2 || pointer.shift) {
        move(dx, dy);
      } else {
        turn(dx, dy);
      }
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      changed();
    } else if (count() === 2) {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      var length = pinchLength();
      var middle = middleOf();
      if (lastPinch > 0) {
        zoom(lastPinch / length);
      }
      if (lastMiddle) {
        move(middle.x - lastMiddle.x, middle.y - lastMiddle.y);
      }
      lastPinch = length;
      lastMiddle = middle;
      changed();
    }
  }
  function onUp(event) {
    delete pointers[event.pointerId];
    lastPinch = 0;
    lastMiddle = null;
  }
  function onWheel(event) {
    event.preventDefault();
    zoom(Math.exp(event.deltaY * 0.0012));
    changed();
  }
  function onContextMenu(event) {
    event.preventDefault();
  }
  function onDoubleClick() {
    if (state.header) {
      resetView(state, state.header);
      changed();
    }
  }
  canvas.addEventListener("pointerdown", onDown);
  canvas.addEventListener("pointermove", onMove);
  canvas.addEventListener("pointerup", onUp);
  canvas.addEventListener("pointercancel", onUp);
  canvas.addEventListener("wheel", onWheel, { passive: false });
  canvas.addEventListener("contextmenu", onContextMenu);
  canvas.addEventListener("dblclick", onDoubleClick);
}

// ---------------------------------------------------------------------------
// The scene's own controls: time of day, quality, motion and the tour
// ---------------------------------------------------------------------------

function hoursLabel(hours) {
  var whole = Math.floor(hours);
  var minutes = Math.round((hours - whole) * 60);
  return whole + ":" + (minutes < 10 ? "0" : "") + minutes;
}

function updateTourButton(state) {
  var button = document.getElementById("tour-button");
  if (button) {
    button.textContent = state.touring ? "Stop tour" : "Tour";
    button.setAttribute("aria-pressed", state.touring ? "true" : "false");
  }
}

function attachSceneControls(state) {
  var slider = document.getElementById("sun-slider");
  var label = document.getElementById("sun-label");
  var overhead = document.getElementById("sun-overhead");
  var quality = document.getElementById("quality-select");
  var motion = document.getElementById("motion-check");
  var tour = document.getElementById("tour-button");
  var crowns = document.getElementById("crown-select");
  function applySun() {
    var hours = Number(slider.value);
    label.textContent = overhead.checked ? "overhead" : hoursLabel(hours);
    slider.disabled = overhead.checked;
    setSceneSun(state, overhead.checked ? null : hours);
  }
  if (slider && overhead) {
    slider.addEventListener("input", applySun);
    overhead.addEventListener("change", applySun);
    applySun();
  }
  if (quality) {
    quality.value = state.qualityName;
    quality.addEventListener("change", onQuality);
  }
  function onQuality() {
    setSceneQuality(state, quality.value);
  }
  if (crowns) {
    crowns.value = state.crownForms;
    crowns.addEventListener("change", onCrowns);
  }
  function onCrowns() {
    state.crownForms = crowns.value;
    if (state.lastCycle) {
      sceneShowCycle(state.lastRun, state.lastCycle, state.lastOptions);
    }
  }
  if (motion) {
    motion.addEventListener("change", onMotion);
  }
  function onMotion() {
    state.moving = motion.checked;
    state.uniforms.windStrength.value = motion.checked ? 1 : 0;
    startLoop(state);
    requestSceneDraw();
  }
  if (tour) {
    tour.addEventListener("click", onTour);
  }
  function onTour() {
    state.touring = !state.touring;
    updateTourButton(state);
    startLoop(state);
  }
}

function setSceneQuality(state, name) {
  state.qualityName = name;
  state.quality = SCENE_QUALITY[name];
  var quality = state.quality;
  state.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, quality.pixelRatio));
  state.sun.shadow.mapSize.set(quality.shadowMap, quality.shadowMap);
  if (state.sun.shadow.map) {
    state.sun.shadow.map.dispose();
    state.sun.shadow.map = null;
  }
  state.reflection.scale = quality.reflection;
  if (state.post.samples !== quality.samples && state.renderer.capabilities.isWebGL2) {
    state.post.samples = quality.samples;
    state.post.scene.dispose();
    state.post.scene = new THREE.WebGLRenderTarget(16, 16, { type: THREE.HalfFloatType, samples: quality.samples });
    state.post.finish.uniforms.scene.value = state.post.scene.texture;
  }
  if (state.header) {
    buildGrass(state, state.header, quality.grass);
    if (state.lastCycle) {
      sceneShowCycle(state.lastRun, state.lastCycle, state.lastOptions);
    }
  }
  sceneResize();
}

// ---------------------------------------------------------------------------
// Setting up, and showing a run and a cycle
// ---------------------------------------------------------------------------

function sceneStart(box) {
  // Set up the scene inside box (an element). Returns false if this browser
  // can't draw in 3D.
  if (scene3d !== null) {
    return true;
  }
  if (typeof THREE === "undefined") {
    return false;
  }
  var renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: "high-performance" });
  } catch (error) {
    return false;
  }
  THREE.ColorManagement.legacyMode = false;
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  box.appendChild(renderer.domElement);
  renderer.domElement.style.touchAction = "none";
  renderer.domElement.style.display = "block";

  var state = {
    renderer: renderer,
    box: box,
    scene: new THREE.Scene(),
    camera: new THREE.PerspectiveCamera(42, 1, 0.1, 2000),
    meshes: {},
    materials: {},
    groundHeight: function flat() { return 0; },
    header: null,
    world: 100,
    tallest: 20,
    crownForms: "genus",
    crownFormsBySpecies: [],
    dusk: 0,
    moving: true,
    touring: false,
    looping: false,
    active: false,
    drawPending: false,
    clock: new THREE.Clock(),
    uniforms: {
      time: { value: 0 },
      windStrength: { value: 1 },
      waterLevel: { value: -1000 },
      worldSize: { value: 100 },
      grassReach: { value: 60 },
      shadeMap: { value: null },
      heightMap: { value: null },
      heightMapSize: { value: 100 },
      sunDirection: { value: new THREE.Vector3(0, 1, 0) },
      sunDirectionView: { value: new THREE.Vector3(0, 1, 0) },
      sunColour: { value: new THREE.Color(1, 1, 1) },
      fogColour: { value: new THREE.Color(0.6, 0.7, 0.8) }
    }
  };
  state.uniforms.shadeMap.value = makeShadeMap();
  state.scene.fog = new THREE.Fog(new THREE.Color(0.6, 0.7, 0.8), 160, 650);

  var sun = new THREE.DirectionalLight(0xffffff, 3);
  sun.castShadow = true;
  sun.shadow.bias = -0.0003;
  sun.shadow.normalBias = 0.04;
  state.scene.add(sun);
  state.scene.add(sun.target);
  state.sun = sun;
  state.skyLight = new THREE.HemisphereLight(new THREE.Color(0.55, 0.68, 0.9), new THREE.Color(0.25, 0.2, 0.12), 0.5);
  state.scene.add(state.skyLight);
  state.sky = makeSky(state);
  state.scene.add(state.sky);

  var textures = {
    leaves: leafTextures(),
    bark: barkTextures(),
    ground: groundDetail(),
    ripples: waterNormals()
  };
  state.materials.ground = makeGroundMaterial(state, textures.ground);
  state.materials.grass = makeGrassMaterial(state);
  // the far hills sit just behind the ground where they meet it (so the
  // ground wins, with no flicker); the mountains fade by their own colours,
  // not the fog, so they stay a little darker than the sky behind them
  state.materials.farHills = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, metalness: 0, envMapIntensity: 0.6, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 8 });
  state.materials.farMountains = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, metalness: 0, envMapIntensity: 0.6, side: THREE.DoubleSide, fog: false });
  state.materials.farWoods = makeFarWoodsMaterial();
  state.materials.edge = new THREE.LineBasicMaterial({ color: new THREE.Color(1, 0.97, 0.85), transparent: true, opacity: 0.14 });
  makeTreeMeshes(state, textures);
  makeWater(state, textures);
  makeLife(state);
  makePost(state);

  var qualityName = onPhone() ? "medium" : "high";
  state.qualityName = qualityName;
  state.quality = SCENE_QUALITY[qualityName];
  scene3d = state;
  setSceneQuality(state, qualityName);
  attachControls(state, renderer.domElement);
  attachSceneControls(state);
  document.addEventListener("visibilitychange", onVisibility);
  function onVisibility() {
    startLoop(state);
  }
  sceneResize();
  return true;
}

function sceneSetActive(active) {
  // the scene only draws while it is on show
  if (scene3d === null) {
    return;
  }
  scene3d.active = active;
  startLoop(scene3d);
  requestSceneDraw();
}

function sceneSetRun(theRun) {
  // a new file: the ground, water, grass and camera for its world
  if (scene3d === null) {
    return;
  }
  var state = scene3d;
  state.header = theRun.header;
  state.world = theRun.header.worldSize;
  state.uniforms.worldSize.value = state.world;
  var highestWater = 0;
  if (theRun.header.terrain) {
    for (var c = 0; c < theRun.cycles.length; c++) {
      if (theRun.cycles[c].waterLevel !== null && theRun.cycles[c].waterLevel > highestWater) {
        highestWater = theRun.cycles[c].waterLevel;
      }
    }
  }
  state.tallest = theRun.tallest || 20;
  buildGround(state, theRun.header, highestWater);
  sizeWater(state, state.world);
  buildGrass(state, theRun.header, state.quality.grass);
  setTreeSpecies(state, theRun);
  // sky, fog and the sun's shadow box, sized to the world
  var world = state.world;
  state.scene.fog.near = world * 1.5;
  state.scene.fog.far = world * 10;
  state.sky.scale.setScalar(world * 8);
  var shadowSize = world * 0.72;
  var shadowCamera = state.sun.shadow.camera;
  shadowCamera.left = -shadowSize;
  shadowCamera.right = shadowSize;
  shadowCamera.top = shadowSize;
  shadowCamera.bottom = -shadowSize;
  shadowCamera.near = 0.5;
  shadowCamera.far = world * 5;
  shadowCamera.updateProjectionMatrix();
  state.camera.far = world * 20;
  state.camera.updateProjectionMatrix();
  setSceneSun(state, state.sunHours === undefined ? 10.5 : state.sunHours);
  resetView(state, theRun.header);
}

function sceneShowCycle(theRun, cycle, options) {
  // Put every plant of one cycle in the scene.
  // options: { colourBy: "species" or "light", highlight: species number or -1,
  //            lightColour: function(light) giving a CSS colour }
  if (scene3d === null) {
    return;
  }
  var state = scene3d;
  state.lastRun = theRun;
  state.lastCycle = cycle;
  state.lastOptions = options;
  updateShadeMap(state, theRun, cycle);
  placeTrees(state, theRun, cycle, options, state.quality.clumps);
  var water = cycle.waterLevel;
  if (theRun.header.terrain && water !== null && water > 0) {
    state.water.visible = true;
    state.water.position.y = water;
    state.uniforms.waterLevel.value = water;
  } else {
    state.water.visible = false;
    state.uniforms.waterLevel.value = -1000;
  }
  requestSceneDraw();
}

function sceneResize() {
  if (scene3d === null) {
    return;
  }
  var box = scene3d.box.getBoundingClientRect();
  var width = Math.max(1, Math.round(box.width));
  var height = Math.max(1, Math.round(box.height));
  scene3d.renderer.setSize(width, height, false);
  scene3d.renderer.domElement.style.width = "100%";
  scene3d.renderer.domElement.style.height = "100%";
  scene3d.camera.aspect = width / height;
  scene3d.camera.updateProjectionMatrix();
  var size = scene3d.renderer.getDrawingBufferSize(new THREE.Vector2());
  sizePost(scene3d, size.x, size.y);
  requestSceneDraw();
}

// ---------------------------------------------------------------------------
// Drawing
// ---------------------------------------------------------------------------

function requestSceneDraw() {
  // draw once, the next time the browser is ready (several changes in a row
  // are drawn together); while things move, the loop draws anyway
  if (scene3d === null || scene3d.drawPending || scene3d.looping) {
    return;
  }
  scene3d.drawPending = true;
  window.requestAnimationFrame(drawOnce);
}

function drawOnce() {
  scene3d.drawPending = false;
  drawSceneNow(scene3d);
}

function startLoop(state) {
  // keep drawing while the wind blows or the tour turns, the scene is on
  // show and the page is visible
  var wanted = state.active && !document.hidden && (state.moving || state.touring);
  if (wanted && !state.looping) {
    state.looping = true;
    state.clock.getDelta();
    window.requestAnimationFrame(loop);
  }
  if (!wanted) {
    state.looping = false;
  }
  function loop() {
    if (!state.looping) {
      return;
    }
    drawSceneNow(state);
    window.requestAnimationFrame(loop);
  }
}

function drawSceneNow(state) {
  if (!state.header) {
    return;
  }
  var delta = Math.min(0.1, state.clock.getDelta());
  if (state.moving) {
    state.uniforms.time.value += delta;
  }
  if (state.touring) {
    state.view.azimuth += delta * 0.05;
    placeCamera(state);
  }
  state.sky.position.copy(state.camera.position);
  state.sun.target.position.set(state.view.target.x, 0, state.view.target.z);
  state.sun.position.copy(state.uniforms.sunDirection.value).multiplyScalar(state.world * 2).add(state.sun.target.position);
  state.camera.updateMatrixWorld();
  state.uniforms.sunDirectionView.value.copy(state.uniforms.sunDirection.value).transformDirection(state.camera.matrixWorldInverse);
  updateLife(state);
  updateEnvironment(state);
  renderReflection(state);
  renderWithPost(state);
}
