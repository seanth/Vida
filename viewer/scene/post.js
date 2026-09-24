// Vida viewer, natural scene: the finishing touches after the scene is drawn.
//
// The scene is drawn into a picture that can hold brighter-than-white
// light (so the sun on the water can be many times brighter than a leaf).
// Then:
//   - bloom: the brightest parts glow softly, as they do in a camera (the
//     bright parts are blurred at smaller and smaller sizes and added back);
//   - the light is squeezed into what a screen can show with the ACES filmic
//     curve, the usual one in films and games;
//   - a gentle colour grade (a touch warmer in the light, cooler in the
//     shade), a vignette darkening the corners, and a little noise so
//     smooth skies don't show bands.

"use strict";

var POST_VERTEX = [
  "varying vec2 vUv;",
  "void main() {",
  "  vUv = uv;",
  "  gl_Position = vec4(position.xy, 0.0, 1.0);",
  "}"
].join("\n");

var BRIGHT_FRAGMENT = [
  // the parts brighter than a threshold, with a soft knee, made half size
  "uniform sampler2D source;",
  "uniform vec2 texel;",
  "uniform float threshold;",
  "varying vec2 vUv;",
  "vec3 brightPart(vec3 c) {",
  "  float brightness = max(c.r, max(c.g, c.b));",
  "  float knee = threshold * 0.5;",
  "  float soft = clamp(brightness - threshold + knee, 0.0, 2.0 * knee);",
  "  soft = soft * soft / (4.0 * knee + 0.0001);",
  "  float contribution = max(soft, brightness - threshold) / max(brightness, 0.0001);",
  "  return c * contribution;",
  "}",
  "void main() {",
  "  vec3 sum = brightPart(texture2D(source, vUv + texel * vec2(-1.0, -1.0)).rgb);",
  "  sum += brightPart(texture2D(source, vUv + texel * vec2(1.0, -1.0)).rgb);",
  "  sum += brightPart(texture2D(source, vUv + texel * vec2(-1.0, 1.0)).rgb);",
  "  sum += brightPart(texture2D(source, vUv + texel * vec2(1.0, 1.0)).rgb);",
  "  gl_FragColor = vec4(min(sum * 0.25, vec3(60.0)), 1.0);",
  "}"
].join("\n");

var DOWN_FRAGMENT = [
  // half size again, blurring (the "dual filter" of Marius Bjorge's talk
  // "Bandwidth-efficient rendering", SIGGRAPH 2015)
  "uniform sampler2D source;",
  "uniform vec2 texel;",
  "varying vec2 vUv;",
  "void main() {",
  "  vec3 sum = texture2D(source, vUv).rgb * 4.0;",
  "  sum += texture2D(source, vUv + texel * vec2(-1.0, -1.0)).rgb;",
  "  sum += texture2D(source, vUv + texel * vec2(1.0, -1.0)).rgb;",
  "  sum += texture2D(source, vUv + texel * vec2(-1.0, 1.0)).rgb;",
  "  sum += texture2D(source, vUv + texel * vec2(1.0, 1.0)).rgb;",
  "  gl_FragColor = vec4(sum / 8.0, 1.0);",
  "}"
].join("\n");

var UP_FRAGMENT = [
  // double size, blurring, and add the level above
  "uniform sampler2D source;",
  "uniform sampler2D larger;",
  "uniform vec2 texel;",
  "varying vec2 vUv;",
  "void main() {",
  "  vec3 sum = texture2D(source, vUv + texel * vec2(-2.0, 0.0)).rgb;",
  "  sum += texture2D(source, vUv + texel * vec2(2.0, 0.0)).rgb;",
  "  sum += texture2D(source, vUv + texel * vec2(0.0, -2.0)).rgb;",
  "  sum += texture2D(source, vUv + texel * vec2(0.0, 2.0)).rgb;",
  "  sum += texture2D(source, vUv + texel * vec2(-1.0, -1.0)).rgb * 2.0;",
  "  sum += texture2D(source, vUv + texel * vec2(1.0, -1.0)).rgb * 2.0;",
  "  sum += texture2D(source, vUv + texel * vec2(-1.0, 1.0)).rgb * 2.0;",
  "  sum += texture2D(source, vUv + texel * vec2(1.0, 1.0)).rgb * 2.0;",
  "  gl_FragColor = vec4(sum / 12.0 + texture2D(larger, vUv).rgb, 1.0);",
  "}"
].join("\n");

var RAYS_SOURCE_FRAGMENT = [
  // where light shafts start: bright parts of the picture near the sun
  "uniform sampler2D source;",
  "uniform vec2 sunPlace;",
  "uniform float aspect;",
  "varying vec2 vUv;",
  "void main() {",
  "  vec3 c = texture2D(source, vUv).rgb;",
  "  float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));",
  "  vec2 away = (vUv - sunPlace) * vec2(aspect, 1.0);",
  "  float near = exp(-dot(away, away) * 3.0);",
  "  gl_FragColor = vec4(c * smoothstep(0.25, 0.9, luma) * near, 1.0);",
  "}"
].join("\n");

var RAYS_FRAGMENT = [
  // streak the bright parts away from the sun (a radial blur towards it)
  "uniform sampler2D source;",
  "uniform vec2 sunPlace;",
  "varying vec2 vUv;",
  "void main() {",
  "  vec2 step = (vUv - sunPlace) / 48.0 * 0.9;",
  "  vec2 place = vUv;",
  "  float fade = 1.0;",
  "  vec3 sum = vec3(0.0);",
  "  for (int i = 0; i < 48; i++) {",
  "    place -= step;",
  "    sum += texture2D(source, place).rgb * fade;",
  "    fade *= 0.955;",
  "  }",
  "  gl_FragColor = vec4(sum / 20.0, 1.0);",
  "}"
].join("\n");

var FINISH_FRAGMENT = [
  "uniform sampler2D scene;",
  "uniform sampler2D bloom;",
  "uniform float useBloom;",
  "uniform sampler2D rays;",
  "uniform float raysStrength;",
  "uniform float bloomStrength;",
  "uniform float exposure;",
  "uniform float time;",
  "varying vec2 vUv;",
  // the ACES filmic curve, as three.js has it (from Stephen Hill's fit)
  "vec3 rrtAndOdtFit(vec3 v) {",
  "  vec3 a = v * (v + 0.0245786) - 0.000090537;",
  "  vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;",
  "  return a / b;",
  "}",
  "vec3 acesFilmic(vec3 colour) {",
  "  const mat3 inputMatrix = mat3(vec3(0.59719, 0.07600, 0.02840), vec3(0.35458, 0.90834, 0.13383), vec3(0.04823, 0.01566, 0.83777));",
  "  const mat3 outputMatrix = mat3(vec3(1.60475, -0.10208, -0.00327), vec3(-0.53108, 1.10813, -0.07276), vec3(-0.07367, -0.00605, 1.07602));",
  "  colour *= exposure / 0.6;",
  "  colour = inputMatrix * colour;",
  "  colour = rrtAndOdtFit(colour);",
  "  colour = outputMatrix * colour;",
  "  return clamp(colour, 0.0, 1.0);",
  "}",
  "vec3 toSrgb(vec3 c) {",
  "  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c));",
  "}",
  "void main() {",
  "  vec3 colour = texture2D(scene, vUv).rgb;",
  "  if (useBloom > 0.5) {",
  "    colour += texture2D(bloom, vUv).rgb * bloomStrength;",
  "  }",
  "  if (raysStrength > 0.0) {",
  "    colour += texture2D(rays, vUv).rgb * raysStrength;",
  "  }",
  "  colour = acesFilmic(colour);",
  // grade: a touch warmer in the light, cooler in the shade, a bit richer
  "  float luma = dot(colour, vec3(0.2126, 0.7152, 0.0722));",
  "  colour = mix(colour * vec3(0.96, 0.99, 1.05), colour * vec3(1.04, 1.01, 0.95), smoothstep(0.1, 0.7, luma));",
  "  colour = mix(vec3(luma), colour, 1.08);",
  // vignette
  "  vec2 fromMiddle = vUv - 0.5;",
  "  colour *= 1.0 - dot(fromMiddle, fromMiddle) * 0.55;",
  "  colour = toSrgb(clamp(colour, 0.0, 1.0));",
  // a little noise, against bands in smooth skies
  "  float noise = fract(sin(dot(vUv * 1000.0 + time, vec2(12.9898, 78.233))) * 43758.5453);",
  "  colour += (noise - 0.5) / 255.0;",
  "  gl_FragColor = vec4(colour, 1.0);",
  "}"
].join("\n");

function postMaterial(fragment, uniforms) {
  return new THREE.ShaderMaterial({
    uniforms: uniforms,
    vertexShader: POST_VERTEX,
    fragmentShader: fragment,
    depthTest: false,
    depthWrite: false,
    toneMapped: false
  });
}

function makePost(state) {
  var renderer = state.renderer;
  var webgl2 = renderer.capabilities.isWebGL2;
  var post = {
    levels: 5,
    down: [],
    up: [],
    quadScene: new THREE.Scene(),
    quadCamera: new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1),
    samples: webgl2 ? 4 : 0
  };
  post.scene = new THREE.WebGLRenderTarget(16, 16, { type: THREE.HalfFloatType, samples: post.samples });
  for (var i = 0; i < post.levels; i++) {
    post.down.push(new THREE.WebGLRenderTarget(8, 8, { type: THREE.HalfFloatType }));
    post.up.push(new THREE.WebGLRenderTarget(8, 8, { type: THREE.HalfFloatType }));
  }
  post.raysA = new THREE.WebGLRenderTarget(8, 8, { type: THREE.HalfFloatType });
  post.raysB = new THREE.WebGLRenderTarget(8, 8, { type: THREE.HalfFloatType });
  post.raysSource = postMaterial(RAYS_SOURCE_FRAGMENT, { source: { value: null }, sunPlace: { value: new THREE.Vector2() }, aspect: { value: 1 } });
  post.raysBlur = postMaterial(RAYS_FRAGMENT, { source: { value: null }, sunPlace: { value: new THREE.Vector2() } });
  post.bright = postMaterial(BRIGHT_FRAGMENT, { source: { value: null }, texel: { value: new THREE.Vector2() }, threshold: { value: 1.2 } });
  post.downMaterial = postMaterial(DOWN_FRAGMENT, { source: { value: null }, texel: { value: new THREE.Vector2() } });
  post.upMaterial = postMaterial(UP_FRAGMENT, { source: { value: null }, larger: { value: null }, texel: { value: new THREE.Vector2() } });
  post.finish = postMaterial(FINISH_FRAGMENT, {
    scene: { value: post.scene.texture },
    bloom: { value: null },
    useBloom: { value: 1 },
    rays: { value: null },
    raysStrength: { value: 0 },
    bloomStrength: { value: 0.22 },
    exposure: { value: 0.6 },
    time: state.uniforms.time
  });
  post.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), post.finish);
  post.quad.frustumCulled = false;
  post.quadScene.add(post.quad);
  state.post = post;
}

function sizePost(state, width, height) {
  var post = state.post;
  post.scene.setSize(width, height);
  var w = width;
  var h = height;
  for (var i = 0; i < post.levels; i++) {
    w = Math.max(1, Math.round(w / 2));
    h = Math.max(1, Math.round(h / 2));
    post.down[i].setSize(w, h);
    post.up[i].setSize(w, h);
  }
  post.raysA.setSize(Math.max(1, Math.round(width / 4)), Math.max(1, Math.round(height / 4)));
  post.raysB.setSize(Math.max(1, Math.round(width / 4)), Math.max(1, Math.round(height / 4)));
}

function quadPass(state, material, target) {
  var post = state.post;
  post.quad.material = material;
  state.renderer.setRenderTarget(target);
  state.renderer.render(post.quadScene, post.quadCamera);
}

function renderWithPost(state) {
  var renderer = state.renderer;
  var post = state.post;
  renderer.setRenderTarget(post.scene);
  renderer.clear();
  renderer.render(state.scene, state.camera);
  var useBloom = state.quality.bloom;
  post.finish.uniforms.useBloom.value = useBloom ? 1 : 0;
  if (useBloom) {
    // bright parts, then smaller and smaller blurs
    post.bright.uniforms.source.value = post.scene.texture;
    post.bright.uniforms.texel.value.set(1 / post.scene.width, 1 / post.scene.height);
    quadPass(state, post.bright, post.down[0]);
    for (var i = 1; i < post.levels; i++) {
      post.downMaterial.uniforms.source.value = post.down[i - 1].texture;
      post.downMaterial.uniforms.texel.value.set(0.5 / post.down[i - 1].width, 0.5 / post.down[i - 1].height);
      quadPass(state, post.downMaterial, post.down[i]);
    }
    // back up, adding each size to the next larger one
    var smaller = post.down[post.levels - 1];
    for (var j = post.levels - 2; j >= 0; j--) {
      post.upMaterial.uniforms.source.value = smaller.texture;
      post.upMaterial.uniforms.larger.value = post.down[j].texture;
      post.upMaterial.uniforms.texel.value.set(0.5 / smaller.width, 0.5 / smaller.height);
      quadPass(state, post.upMaterial, post.up[j]);
      smaller = post.up[j];
    }
    post.finish.uniforms.bloom.value = post.up[0].texture;
  }
  // light shafts, when the sun is in front of the camera
  var sunPlace = state.camera.position.clone().add(state.uniforms.sunDirection.value.clone().multiplyScalar(1000)).project(state.camera);
  var ahead = new THREE.Vector3(0, 0, -1).applyQuaternion(state.camera.quaternion).dot(state.uniforms.sunDirection.value);
  var strength = state.quality.bloom ? Math.max(0, ahead) * (1 - state.dusk * 0.7) * 0.55 : 0;
  var onScreen = Math.max(Math.abs(sunPlace.x), Math.abs(sunPlace.y));
  strength *= 1 - smoothStep(1.2, 2.2, onScreen);
  post.finish.uniforms.raysStrength.value = strength;
  if (strength > 0.001) {
    var place = new THREE.Vector2(sunPlace.x * 0.5 + 0.5, sunPlace.y * 0.5 + 0.5);
    post.raysSource.uniforms.source.value = post.scene.texture;
    post.raysSource.uniforms.sunPlace.value.copy(place);
    post.raysSource.uniforms.aspect.value = state.camera.aspect;
    quadPass(state, post.raysSource, post.raysA);
    post.raysBlur.uniforms.source.value = post.raysA.texture;
    post.raysBlur.uniforms.sunPlace.value.copy(place);
    quadPass(state, post.raysBlur, post.raysB);
    post.finish.uniforms.rays.value = post.raysB.texture;
  }
  quadPass(state, post.finish, null);
}
