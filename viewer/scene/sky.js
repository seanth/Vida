// Vida viewer, natural scene: the sky, the sun and the light they give.
//
// The sky is the Preetham model of daylight, adapted from three.js's
// examples/jsm/objects/Sky.js (MIT licence; first implemented by Simon
// Wallner, improved by Martin Upitis, three.js version by zz85), with
// drifting clouds added.
//
// The sun can be put at any time of day, or straight overhead. Straight
// overhead is how Vida's own light works (it comes straight down), so the
// shadows then fall where the simulation's shade does.

"use strict";

var SCENE_LATITUDE = 35;       // degrees north, for where the sun is at each time of day
var SCENE_DECLINATION = 18;    // early summer

function sunDirectionAt(hours) {
  // The direction of the sun (a unit vector in three.js coordinates:
  // x east, y up, z south) at a time of day, in hours.
  // hours === null means straight overhead.
  if (hours === null) {
    return new THREE.Vector3(0.02, 1, 0.01).normalize();
  }
  var latitude = SCENE_LATITUDE * Math.PI / 180;
  var declination = SCENE_DECLINATION * Math.PI / 180;
  var hourAngle = (hours - 12) * 15 * Math.PI / 180;
  var east = -Math.cos(declination) * Math.sin(hourAngle);
  var north = Math.sin(declination) * Math.cos(latitude) - Math.cos(declination) * Math.cos(hourAngle) * Math.sin(latitude);
  var up = Math.sin(declination) * Math.sin(latitude) + Math.cos(declination) * Math.cos(hourAngle) * Math.cos(latitude);
  return new THREE.Vector3(east, up, -north).normalize();
}

function sunColourFor(direction) {
  // Warm and dim near the horizon, white and bright high up (linear colour
  // and brightness for the sunlight).
  var height = Math.max(0, direction.y);
  var warm = new THREE.Color(1.0, 0.42, 0.16);
  var white = new THREE.Color(1.0, 0.95, 0.88);
  var colour = warm.clone().lerp(white, Math.min(1, Math.pow(height / 0.45, 0.7)));
  var strength = Math.max(0, Math.min(1, (height + 0.02) / 0.18));
  return { colour: colour, strength: strength };
}

var SKY_VERTEX = [
  "uniform vec3 sunPosition;",
  "uniform float rayleigh;",
  "uniform float turbidity;",
  "uniform float mieCoefficient;",
  "uniform vec3 up;",
  "varying vec3 vWorldPosition;",
  "varying vec3 vSunDirection;",
  "varying float vSunfade;",
  "varying vec3 vBetaR;",
  "varying vec3 vBetaM;",
  "varying float vSunE;",
  "const float e = 2.71828182845904523536028747135266249775724709369995957;",
  "const float pi = 3.141592653589793238462643383279502884197169;",
  "const vec3 totalRayleigh = vec3(5.804542996261093E-6, 1.3562911419845635E-5, 3.0265902468824876E-5);",
  "const vec3 MieConst = vec3(1.8399918514433978E14, 2.7798023919660528E14, 4.0790479543861094E14);",
  "const float cutoffAngle = 1.6110731556870734;",
  "const float steepness = 1.5;",
  "const float EE = 1000.0;",
  "float sunIntensity(float zenithAngleCos) {",
  "  zenithAngleCos = clamp(zenithAngleCos, -1.0, 1.0);",
  "  return EE * max(0.0, 1.0 - pow(e, -((cutoffAngle - acos(zenithAngleCos)) / steepness)));",
  "}",
  "vec3 totalMie(float T) {",
  "  float c = (0.2 * T) * 10E-18;",
  "  return 0.434 * c * MieConst;",
  "}",
  "void main() {",
  "  vec4 worldPosition = modelMatrix * vec4(position, 1.0);",
  "  vWorldPosition = worldPosition.xyz - cameraPosition;",
  "  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);",
  "  gl_Position.z = gl_Position.w;",
  "  vSunDirection = normalize(sunPosition);",
  "  vSunE = sunIntensity(dot(vSunDirection, up));",
  "  vSunfade = 1.0 - clamp(1.0 - exp((sunPosition.y / 450000.0)), 0.0, 1.0);",
  "  float rayleighCoefficient = rayleigh - (1.0 * (1.0 - vSunfade));",
  "  vBetaR = totalRayleigh * rayleighCoefficient;",
  "  vBetaM = totalMie(turbidity) * mieCoefficient;",
  "}"
].join("\n");

var SKY_FRAGMENT = [
  "varying vec3 vWorldPosition;",
  "varying vec3 vSunDirection;",
  "varying float vSunfade;",
  "varying vec3 vBetaR;",
  "varying vec3 vBetaM;",
  "varying float vSunE;",
  "uniform float mieDirectionalG;",
  "uniform vec3 up;",
  "uniform float time;",
  "uniform float brightness;",
  "uniform float cloudCover;",
  "uniform vec3 sunColour;",
  "const float pi = 3.141592653589793238462643383279502884197169;",
  "const float rayleighZenithLength = 8.4E3;",
  "const float mieZenithLength = 1.25E3;",
  "const float sunAngularDiameterCos = 0.999956676946448443553574619906976478926848692873900859324;",
  "const float THREE_OVER_SIXTEENPI = 0.05968310365946075;",
  "const float ONE_OVER_FOURPI = 0.07957747154594767;",
  SCENE_NOISE_GLSL,
  "float rayleighPhase(float cosTheta) {",
  "  return THREE_OVER_SIXTEENPI * (1.0 + pow(cosTheta, 2.0));",
  "}",
  "float hgPhase(float cosTheta, float g) {",
  "  float g2 = pow(g, 2.0);",
  "  float inverse = 1.0 / pow(1.0 - 2.0 * g * cosTheta + g2, 1.5);",
  "  return ONE_OVER_FOURPI * ((1.0 - g2) * inverse);",
  "}",
  "void main() {",
  "  vec3 direction = normalize(vWorldPosition);",
  "  float zenithAngle = acos(max(0.0, dot(up, direction)));",
  "  float inverse = 1.0 / (cos(zenithAngle) + 0.15 * pow(93.885 - ((zenithAngle * 180.0) / pi), -1.253));",
  "  float sR = rayleighZenithLength * inverse;",
  "  float sM = mieZenithLength * inverse;",
  "  vec3 Fex = exp(-(vBetaR * sR + vBetaM * sM));",
  "  float cosTheta = dot(direction, vSunDirection);",
  "  float rPhase = rayleighPhase(cosTheta * 0.5 + 0.5);",
  "  vec3 betaRTheta = vBetaR * rPhase;",
  "  float mPhase = hgPhase(cosTheta, mieDirectionalG);",
  "  vec3 betaMTheta = vBetaM * mPhase;",
  "  vec3 Lin = pow(vSunE * ((betaRTheta + betaMTheta) / (vBetaR + vBetaM)) * (1.0 - Fex), vec3(1.5));",
  "  Lin *= mix(vec3(1.0), pow(vSunE * ((betaRTheta + betaMTheta) / (vBetaR + vBetaM)) * Fex, vec3(1.0 / 2.0)), clamp(pow(1.0 - dot(up, vSunDirection), 5.0), 0.0, 1.0));",
  "  vec3 L0 = vec3(0.1) * Fex;",
  "  float sundisk = smoothstep(sunAngularDiameterCos, sunAngularDiameterCos + 0.00002, cosTheta);",
  "  L0 += (vSunE * 19000.0 * Fex) * sundisk;",
  "  vec3 texColor = (Lin + L0) * 0.04 + vec3(0.0, 0.0003, 0.00075);",
  "  vec3 colour = pow(texColor, vec3(1.0 / (1.2 + (1.2 * vSunfade))));",
  // a little richer than the model gives, as on a clear, dry day
  "  float skyLuma = dot(colour, vec3(0.2126, 0.7152, 0.0722));",
  "  colour = max(mix(vec3(skyLuma), colour, 1.45), 0.0);",
  // by day, the haze low in the sky is a pale blue away from the sun (the
  // model makes it grey, and the tone mapping greyer)
  "  float lowSky = 1.0 - smoothstep(-0.05, 0.4, direction.y);",
  "  float awayFromSun = 1.0 - pow(max(cosTheta, 0.0), 3.0);",
  "  float byDay = smoothstep(0.05, 0.35, vSunDirection.y);",
  "  colour *= mix(vec3(1.0), vec3(0.92, 1.08, 1.38), lowSky * awayFromSun * byDay);",
  // clouds: soft patches on a flat layer above, drifting, lit from the sun's side
  "  if (direction.y > 0.0 && cloudCover > 0.0) {",
  "    vec2 cloudPlace = direction.xz / (direction.y + 0.08) * 1.6 + vec2(time * 0.012, time * 0.004);",
  "    float shape = sceneFbm(cloudPlace * 0.7);",
  "    float detail = sceneFbm(cloudPlace * 2.3 + 5.0);",
  "    float puff = shape * 0.85 + detail * 0.3;",
  "    float cloud = smoothstep(0.66 - cloudCover * 0.22, 0.8 - cloudCover * 0.15, puff);",
  "    cloud *= smoothstep(0.02, 0.3, direction.y);",
  "    float sunSide = pow(max(cosTheta, 0.0), 4.0);",
  "    float daylight = clamp(vSunE / 600.0, 0.04, 1.0);",
  // lit on top and towards the sun, greyer underneath where they are thick
  "    float thick = smoothstep(0.7, 1.0, puff);",
  "    vec3 cloudColour = mix(vec3(1.25, 1.25, 1.28), vec3(0.72, 0.75, 0.82), thick) * daylight * 2.6;",
  "    cloudColour += sunColour * sunSide * 1.2 * daylight;",
  "    colour = mix(colour, cloudColour, cloud * 0.92);",
  "  }",
  "  gl_FragColor = vec4(colour * brightness, 1.0);",
  "}"
].join("\n");

function makeSky(state) {
  var material = new THREE.ShaderMaterial({
    name: "Sky",
    uniforms: {
      turbidity: { value: 1.8 },
      rayleigh: { value: 3.0 },
      mieCoefficient: { value: 0.0025 },
      mieDirectionalG: { value: 0.82 },
      sunPosition: { value: new THREE.Vector3(0, 1, 0) },
      up: { value: new THREE.Vector3(0, 1, 0) },
      time: state.uniforms.time,
      brightness: { value: 0.3 },
      cloudCover: { value: 0.6 },
      sunColour: state.uniforms.sunColour
    },
    vertexShader: SKY_VERTEX,
    fragmentShader: SKY_FRAGMENT,
    side: THREE.BackSide,
    depthWrite: false,
    toneMapped: false
  });
  var sky = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), material);
  sky.frustumCulled = false;
  sky.renderOrder = -1;
  return sky;
}

function setSceneSun(state, hours) {
  // Put the sun at a time of day (hours), or straight overhead (null), and
  // light everything to match.
  state.sunHours = hours;
  var direction = sunDirectionAt(hours);
  state.uniforms.sunDirection.value.copy(direction);
  var sun = sunColourFor(direction);
  state.uniforms.sunColour.value.copy(sun.colour).multiplyScalar(sun.strength);
  state.sky.material.uniforms.sunPosition.value.copy(direction);
  state.sun.color.copy(sun.colour);
  state.sun.intensity = 2.8 * sun.strength;
  state.sun.visible = sun.strength > 0.001;
  var world = state.world || 100;
  state.sun.position.copy(direction).multiplyScalar(world * 2).add(state.sun.target.position);
  // the light from the whole sky, dimmer at dusk
  var daylight = Math.max(0.22, Math.min(1, direction.y / 0.35 + 0.15));
  state.skyLight.intensity = 0.55 * daylight;
  state.skyLight.color.setRGB(0.55, 0.68, 0.9).lerp(new THREE.Color(0.9, 0.6, 0.45), (1 - daylight) * 0.5);
  state.materials.edge.color.setRGB(1, 0.97, 0.85).multiplyScalar(0.25 + 0.5 * daylight);
  state.dusk = 1 - Math.max(0, Math.min(1, (direction.y - 0.02) / 0.2));
  // fog: the colour of the sky near the horizon, away from the sun
  var horizon = new THREE.Color(0.62, 0.72, 0.84).lerp(new THREE.Color(0.85, 0.6, 0.45), state.dusk * 0.6);
  horizon.multiplyScalar((0.35 + 0.65 * daylight) * 0.72);
  state.scene.fog.color.copy(horizon);
  state.uniforms.fogColour.value.copy(horizon);
  if (state.post) {
    // like eyes getting used to the dark, the picture brightens at dusk
    state.post.finish.uniforms.exposure.value = 0.6 * (1 + state.dusk * 1.8);
  }
  state.environmentStale = true;
  requestSceneDraw();
}

function updateEnvironment(state) {
  // Light from the whole sky, for everything that reflects it (the leaves,
  // the ground and the bark): the sky is rendered into a special map that
  // three.js blurs for rough surfaces.
  if (!state.environmentStale) {
    return;
  }
  state.environmentStale = false;
  if (!state.pmrem) {
    state.pmrem = new THREE.PMREMGenerator(state.renderer);
  }
  var skyOnly = new THREE.Scene();
  var skyCopy = new THREE.Mesh(state.sky.geometry, state.sky.material);
  skyCopy.scale.setScalar(100);
  skyOnly.add(skyCopy);
  var target = state.pmrem.fromScene(skyOnly, 0, 0.1, 1000);
  if (state.environment) {
    state.environment.dispose();
  }
  state.environment = target;
  state.scene.environment = target.texture;
}
