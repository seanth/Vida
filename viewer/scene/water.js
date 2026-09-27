// Vida viewer, natural scene: water.
//
// The water is one flat sheet at the simulation's water level (to scale).
// How it looks is decoration, following the usual recipe for water in
// games (see for example Alexander Ameye's "Stylized Water Shader" notes):
//   - it reflects the world, like a mirror, bent by the ripples: the scene
//     is drawn a second time from a camera below the water (the reflection
//     maths is from three.js's examples/jsm/objects/Reflector.js, MIT);
//   - how much it reflects depends on the angle you look at it (Fresnel);
//   - the bottom shows through where it is shallow, and it is dark green
//     where deep, using how far the ground is below the surface (from the
//     height map);
//   - ripples drift across it, the sun glints off them, and foam lines the
//     shore.

"use strict";

var WATER_VERTEX = [
  "uniform mat4 textureMatrix;",
  "varying vec4 vReflectPlace;",
  "varying vec3 vWaterPlace;",
  "#include <fog_pars_vertex>",
  "void main() {",
  "  vReflectPlace = textureMatrix * vec4(position, 1.0);",
  "  vec4 worldPlace = modelMatrix * vec4(position, 1.0);",
  "  vWaterPlace = worldPlace.xyz;",
  "  vec4 mvPosition = viewMatrix * worldPlace;",
  "  gl_Position = projectionMatrix * mvPosition;",
  "  #include <fog_vertex>",
  "}"
].join("\n");

var WATER_FRAGMENT = [
  "uniform sampler2D reflection;",
  "uniform float useReflection;",
  "uniform sampler2D ripples;",
  "uniform sampler2D heightMap;",
  "uniform float heightMapSize;",
  "uniform float waterLevel;",
  "uniform float time;",
  "uniform float windStrength;",
  "uniform vec3 sunDirection;",
  "uniform vec3 sunColour;",
  "uniform vec3 skyColour;",
  "varying vec4 vReflectPlace;",
  "varying vec3 vWaterPlace;",
  "#include <fog_pars_fragment>",
  SCENE_NOISE_GLSL,
  "void main() {",
  "  vec3 place = vWaterPlace;",
  "  vec2 heightUv = place.xz / heightMapSize + 0.5;",
  // no water beyond the land the height map covers
  "  if (heightUv.x < 0.0 || heightUv.x > 1.0 || heightUv.y < 0.0 || heightUv.y > 1.0) discard;",
  "  float ground = texture2D(heightMap, heightUv).r;",
  "  float depth = waterLevel - ground;",
  "  if (depth <= 0.0) discard;",
  // ripples: two layers drifting different ways
  "  vec2 drift = vec2(time * 0.035, time * 0.021) * (0.4 + windStrength);",
  "  vec3 ripple1 = texture2D(ripples, place.xz * 0.09 + drift).rgb * 2.0 - 1.0;",
  "  vec3 ripple2 = texture2D(ripples, place.xz * 0.21 - drift * 1.4 + 0.37).rgb * 2.0 - 1.0;",
  "  vec2 tilt = (ripple1.xy + ripple2.xy * 0.6) * (0.08 + 0.08 * windStrength);",
  "  vec3 normal = normalize(vec3(tilt.x, 1.0, -tilt.y));",
  "  vec3 view = normalize(cameraPosition - place);",
  "  float facing = max(dot(normal, view), 0.0);",
  // how much it reflects depends on the angle you look at it (Schlick's
  // formula for Fresnel, for water)
  "  float fresnel = 0.02 + 0.98 * pow(1.0 - facing, 5.0);",
  // what it reflects
  "  vec3 reflected = skyColour * 1.6;",
  "  if (useReflection > 0.5) {",
  "    vec2 mirror = vReflectPlace.xy / vReflectPlace.w + tilt * 0.3;",
  "    reflected = texture2D(reflection, mirror).rgb;",
  "  }",
  "  reflected *= vec3(0.88, 0.93, 0.95);",
  // how much of the bottom shows through: less where it is deep, and less
  // at a slant, where the light goes further through the water
  "  float through = exp(-depth * 2.4 / max(facing, 0.25));",
  "  float daylight = clamp(sunDirection.y * 1.5 + 0.2, 0.08, 1.0);",
  "  vec3 body = vec3(0.02, 0.065, 0.055) * daylight + sunColour * 0.01;",
  // light from the water itself (its colour), then what it reflects on top;
  // the alpha lets the bottom show through by the same amount
  "  float alpha = 1.0 - through * (1.0 - fresnel);",
  "  vec3 colour = (body * (1.0 - through) * (1.0 - fresnel) + reflected * fresnel) / max(alpha, 0.001);",
  // the sun glinting off the ripples
  "  vec3 halfway = normalize(sunDirection + view);",
  "  float glint = pow(max(dot(normal, halfway), 0.0), 900.0) * 12.0 + pow(max(dot(normal, halfway), 0.0), 250.0) * 0.06;",
  "  colour += sunColour * glint / max(alpha, 0.05);",
  // foam: a thin broken line along the shore
  "  float shore = 1.0 - smoothstep(0.0, 0.06, depth);",
  "  float bubbles = 1.0 - sceneCells(place.xz * 3.2 + vec2(time * 0.12, time * 0.05), time * 0.9);",
  "  float foam = smoothstep(0.55, 0.9, bubbles * 0.7 + shore * 0.6) * shore;",
  "  colour = mix(colour, vec3(0.7) * (sunColour * 0.6 + vec3(0.25) * daylight), foam * 0.7);",
  "  alpha = clamp(max(alpha, foam * 0.7), 0.0, 1.0);",
  "  gl_FragColor = vec4(colour, alpha);",
  "  #include <fog_fragment>",
  "}"
].join("\n");

function makeWater(state, textures) {
  var reflectionTarget = new THREE.WebGLRenderTarget(16, 16, { type: THREE.HalfFloatType });
  var uniforms = THREE.UniformsUtils.merge([THREE.UniformsLib.fog]);
  uniforms.reflection = { value: reflectionTarget.texture };
  uniforms.useReflection = { value: 1 };
  uniforms.textureMatrix = { value: new THREE.Matrix4() };
  uniforms.ripples = { value: textures.ripples };
  uniforms.heightMap = state.uniforms.heightMap;
  uniforms.heightMapSize = state.uniforms.heightMapSize;
  uniforms.waterLevel = state.uniforms.waterLevel;
  uniforms.time = state.uniforms.time;
  uniforms.windStrength = state.uniforms.windStrength;
  uniforms.sunDirection = state.uniforms.sunDirection;
  uniforms.sunColour = state.uniforms.sunColour;
  uniforms.skyColour = state.uniforms.fogColour;
  var material = new THREE.ShaderMaterial({
    name: "Water",
    uniforms: uniforms,
    vertexShader: WATER_VERTEX,
    fragmentShader: WATER_FRAGMENT,
    transparent: true,
    fog: true,
    depthWrite: false,
    toneMapped: false
  });
  var world = state.world || 100;
  var water = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), material);
  water.rotation.x = -Math.PI / 2;
  water.visible = false;
  water.renderOrder = 1;
  state.scene.add(water);
  state.water = water;
  state.reflection = {
    target: reflectionTarget,
    camera: new THREE.PerspectiveCamera(),
    scale: 0.5
  };
  return water;
}

function sizeWater(state, world) {
  state.water.scale.set(world * 1.6, world * 1.6, 1);
}

function renderReflection(state) {
  // Draw the world as seen in the water, into a texture the water uses.
  var water = state.water;
  var reflection = state.reflection;
  var uniforms = water.material.uniforms;
  if (!water.visible || reflection.scale <= 0) {
    uniforms.useReflection.value = 0;
    return;
  }
  uniforms.useReflection.value = 1;
  var camera = state.camera;
  var renderer = state.renderer;
  var size = renderer.getDrawingBufferSize(new THREE.Vector2());
  var width = Math.max(16, Math.round(size.x * reflection.scale));
  var height = Math.max(16, Math.round(size.y * reflection.scale));
  if (reflection.target.width !== width || reflection.target.height !== height) {
    reflection.target.setSize(width, height);
  }
  water.updateMatrixWorld();
  camera.updateMatrixWorld();
  var waterPlace = new THREE.Vector3().setFromMatrixPosition(water.matrixWorld);
  var cameraPlace = new THREE.Vector3().setFromMatrixPosition(camera.matrixWorld);
  var normal = new THREE.Vector3(0, 1, 0);
  var view = new THREE.Vector3().subVectors(waterPlace, cameraPlace);
  if (view.dot(normal) > 0) {
    // looking at the water from below: nothing to reflect
    uniforms.useReflection.value = 0;
    return;
  }
  view.reflect(normal).negate().add(waterPlace);
  var turn = new THREE.Matrix4().extractRotation(camera.matrixWorld);
  var lookAt = new THREE.Vector3(0, 0, -1).applyMatrix4(turn).add(cameraPlace);
  var target = new THREE.Vector3().subVectors(waterPlace, lookAt).reflect(normal).negate().add(waterPlace);
  var mirror = reflection.camera;
  mirror.position.copy(view);
  mirror.up.set(0, 1, 0).applyMatrix4(turn).reflect(normal);
  mirror.lookAt(target);
  mirror.far = camera.far;
  mirror.updateMatrixWorld();
  mirror.projectionMatrix.copy(camera.projectionMatrix);
  var textureMatrix = uniforms.textureMatrix.value;
  textureMatrix.set(0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0, 0.5, 0.5, 0, 0, 0, 1);
  textureMatrix.multiply(mirror.projectionMatrix);
  textureMatrix.multiply(mirror.matrixWorldInverse);
  textureMatrix.multiply(water.matrixWorld);
  // cut away everything below the water, so only what is above is reflected
  // (an oblique near plane: http://www.terathon.com/code/oblique.html)
  var plane = new THREE.Plane().setFromNormalAndCoplanarPoint(normal, waterPlace);
  plane.applyMatrix4(mirror.matrixWorldInverse);
  var clip = new THREE.Vector4(plane.normal.x, plane.normal.y, plane.normal.z, plane.constant);
  var projection = mirror.projectionMatrix;
  var q = new THREE.Vector4(
    (Math.sign(clip.x) + projection.elements[8]) / projection.elements[0],
    (Math.sign(clip.y) + projection.elements[9]) / projection.elements[5],
    -1.0,
    (1.0 + projection.elements[10]) / projection.elements[14]);
  clip.multiplyScalar(2.0 / clip.dot(q));
  projection.elements[2] = clip.x;
  projection.elements[6] = clip.y;
  projection.elements[10] = clip.z + 1.0 - 0.003;
  projection.elements[14] = clip.w;
  // draw it, without the water itself and without the grass (too small to see)
  water.visible = false;
  var grassWasVisible = state.grass ? state.grass.visible : false;
  if (state.grass) {
    state.grass.visible = false;
  }
  var shadowUpdate = renderer.shadowMap.autoUpdate;
  renderer.shadowMap.autoUpdate = false;
  state.sky.position.copy(mirror.position);
  renderer.setRenderTarget(reflection.target);
  renderer.clear();
  renderer.render(state.scene, mirror);
  renderer.setRenderTarget(null);
  renderer.shadowMap.autoUpdate = shadowUpdate;
  state.sky.position.copy(camera.position);
  if (state.grass) {
    state.grass.visible = grassWasVisible;
  }
  water.visible = true;
}
