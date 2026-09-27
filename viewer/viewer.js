// Vida viewer: shows a simulation saved with Vida's -j option (viewer.jsonl).
//
// Plain JavaScript with no libraries, so it runs by opening index.html.
// The file format is described in Vida_Data/vjson.py: the first line is the
// world (size, fields, terrain), and every other line is one cycle.
//
// The main pieces, in order:
//   loading        read the file (unzipping .gz files) into `run`
//   colours        which colour each species gets
//   drawing        the map from above, the side view and the two charts
//   interaction    play/pause, the slider, hovering, and keyboard keys

"use strict";

var run = null;              // the loaded simulation; see readViewerFile
var cycleIndex = 0;          // which cycle is shown (position in run.cycles)
var playTimer = null;        // set while playing
var colourBy = "species";    // "species" or "light"
var highlightSpecies = -1;   // a species number, or -1 for all species
var hoverTargets = {};       // what the pointer can hover over, per canvas
var chartHover = {};         // the cycle the pointer is over, per chart

// The palette gives three categorical colours (see viewer.css); species past
// the three most common are grouped as "Other". Three is the most that stay
// easy to tell apart when every colour can sit next to every other, as on
// the map.
var SPECIES_SLOTS = 3;

// Light received (the part of the canopy in sunlight), from none to full, in
// a single blue. On the light page more light is darker; on the dark page it
// is lighter. Neither end is so faint that a canopy disappears.
var LIGHT_RAMP = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
  "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"];
var LIGHT_RAMP_DARK = ["#184f95", "#1c5cab", "#256abf", "#2a78d6", "#3987e5",
  "#5598e7", "#6da7ec", "#86b6ef", "#9ec5f4", "#cde2fb"];

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

function readViewerFile(text) {
  // Turn the text of a viewer.jsonl file into the `run` object.
  var lines = text.split("\n");
  var header = null;
  var cycles = [];
  var species = [];
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i].trim();
    if (line === "") {
      continue;
    }
    var data = JSON.parse(line);
    if (header === null) {
      if (data.format !== "vida-viewer") {
        throw new Error("This is not a Vida viewer file (made with Vida's -j option).");
      }
      header = data;
      continue;
    }
    for (var s = 0; s < data.newSpecies.length; s++) {
      var oneSpecies = data.newSpecies[s];
      species[oneSpecies.number] = oneSpecies;
    }
    cycles.push(data);
  }
  if (header === null || cycles.length === 0) {
    throw new Error("The file has no cycles in it.");
  }
  var newRun = { header: header, cycles: cycles, species: species };
  summarise(newRun);
  assignSpeciesColours(newRun);
  return newRun;
}

function field(plant, name) {
  // one number from a plant or seed, by the name given in the header
  return plant[run.fieldIndex[name]];
}

function summarise(theRun) {
  // Work out the totals the charts need, once, when the file is loaded.
  var header = theRun.header;
  theRun.fieldIndex = {};
  for (var f = 0; f < header.plantFields.length; f++) {
    theRun.fieldIndex[header.plantFields[f]] = f;
  }
  var index = theRun.fieldIndex;
  theRun.speciesPlantCycles = [];
  for (var s = 0; s < theRun.species.length; s++) {
    theRun.speciesPlantCycles.push(0);
  }
  theRun.tallest = 1.0;
  for (var c = 0; c < theRun.cycles.length; c++) {
    var cycle = theRun.cycles[c];
    cycle.plantsBySpecies = [];
    cycle.seedsBySpecies = [];
    for (var k = 0; k < theRun.species.length; k++) {
      cycle.plantsBySpecies.push(0);
      cycle.seedsBySpecies.push(0);
    }
    for (var p = 0; p < cycle.plants.length; p++) {
      var plant = cycle.plants[p];
      var number = plant[index.species];
      cycle.plantsBySpecies[number] += 1;
      theRun.speciesPlantCycles[number] += 1;
      var top = (plant[index.elevation] || 0) + plant[index.stemHeight];
      if (top > theRun.tallest) {
        theRun.tallest = top;
      }
    }
    for (var d = 0; d < cycle.seeds.length; d++) {
      cycle.seedsBySpecies[cycle.seeds[d][4]] += 1;
    }
    cycle.deathCount = 0;
    for (var cause in cycle.deaths) {
      cycle.deathCount += cycle.deaths[cause];
    }
  }
  var terrain = header.terrain;
  theRun.highestGround = 0;
  if (terrain) {
    for (var row = 0; row < terrain.cells; row++) {
      for (var col = 0; col < terrain.cells; col++) {
        var height = terrain.elevation[row][col] || 0;
        if (height > theRun.highestGround) {
          theRun.highestGround = height;
        }
      }
    }
  }
  if (theRun.highestGround > theRun.tallest) {
    theRun.tallest = theRun.highestGround;
  }
}

function assignSpeciesColours(theRun) {
  // The most common species over the whole run get the colours, so a
  // species keeps its colour from the first cycle to the last.
  var order = [];
  for (var s = 0; s < theRun.species.length; s++) {
    order.push(s);
  }
  order.sort(compareByPlantCycles);
  function compareByPlantCycles(a, b) {
    return theRun.speciesPlantCycles[b] - theRun.speciesPlantCycles[a];
  }
  for (var i = 0; i < order.length; i++) {
    if (i < SPECIES_SLOTS && theRun.speciesPlantCycles[order[i]] > 0) {
      theRun.species[order[i]].slot = i;
    } else {
      theRun.species[order[i]].slot = -1;
    }
  }
  theRun.speciesOrder = order;
}

function looksGzipped(bytes) {
  return bytes.length > 2 && bytes[0] === 0x1f && bytes[1] === 0x8b;
}

async function textFromBytes(buffer) {
  // The text of a file, unzipping it first if it is gzipped.
  var bytes = new Uint8Array(buffer);
  if (looksGzipped(bytes)) {
    var stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    return await new Response(stream).text();
  }
  return new TextDecoder().decode(bytes);
}

async function loadBytes(buffer, name) {
  showMessage("Reading " + name + "…");
  try {
    var text = await textFromBytes(buffer);
    run = readViewerFile(text);
  } catch (error) {
    showMessage("Could not read " + name + ": " + error.message);
    return;
  }
  showMessage("");
  startViewing(name);
}

async function loadFile(file) {
  var buffer = await file.arrayBuffer();
  await loadBytes(buffer, file.name);
}

async function loadUrl(url) {
  try {
    var response = await fetch(url);
    if (!response.ok) {
      throw new Error(response.status + " " + response.statusText);
    }
    var buffer = await response.arrayBuffer();
    await loadBytes(buffer, url);
  } catch (error) {
    showMessage("Could not load " + url + " (" + error.message + "). Browsers do not let a page " +
      "opened straight from disk load other files, so use \"Open viewer.jsonl…\" and choose " +
      "viewer/sample/viewer.jsonl.gz, or run  python -m http.server  in the viewer folder and " +
      "open http://localhost:8000.");
  }
}

function showMessage(text) {
  document.getElementById("load-message").textContent = text;
}

// ---------------------------------------------------------------------------
// Colours
// ---------------------------------------------------------------------------

function cssColour(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function isDark() {
  var theme = document.documentElement.dataset.theme;
  if (theme === "dark") {
    return true;
  }
  if (theme === "light") {
    return false;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function slotColour(slot) {
  if (slot < 0) {
    return cssColour("--other");
  }
  return cssColour("--series-" + (slot + 1));
}

function speciesColour(number) {
  return slotColour(run.species[number].slot);
}

function lightColour(light) {
  var ramp = LIGHT_RAMP;
  if (isDark()) {
    ramp = LIGHT_RAMP_DARK;
  }
  var step = Math.floor((light || 0) * ramp.length);
  if (step >= ramp.length) {
    step = ramp.length - 1;
  }
  if (step < 0) {
    step = 0;
  }
  return ramp[step];
}

function mixColours(low, high, amount) {
  // a colour part way between two "#rrggbb" colours (amount 0 to 1)
  var a = parseInt(low.slice(1), 16);
  var b = parseInt(high.slice(1), 16);
  var parts = [];
  for (var shift = 16; shift >= 0; shift -= 8) {
    var from = (a >> shift) & 255;
    var to = (b >> shift) & 255;
    parts.push(Math.round(from + (to - from) * amount));
  }
  return "rgb(" + parts[0] + "," + parts[1] + "," + parts[2] + ")";
}

// ---------------------------------------------------------------------------
// Drawing helpers
// ---------------------------------------------------------------------------

function prepareCanvas(canvas) {
  // Size the canvas to its box on screen (sharp on high resolution screens).
  // Returns the drawing context, working in screen pixels.
  var box = canvas.getBoundingClientRect();
  var ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(box.width * ratio));
  canvas.height = Math.max(1, Math.round(box.height * ratio));
  var context = canvas.getContext("2d");
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, box.width, box.height);
  return { context: context, width: box.width, height: box.height };
}

function niceStep(range, wantedTicks) {
  // a round step (1, 2 or 5 times a power of ten) for axis ticks
  var rough = range / wantedTicks;
  var power = Math.pow(10, Math.floor(Math.log10(rough)));
  var steps = [1, 2, 5, 10];
  for (var i = 0; i < steps.length; i++) {
    if (steps[i] * power >= rough) {
      return steps[i] * power;
    }
  }
  return 10 * power;
}

function plantDrawOrder(plants, key) {
  // positions of the plants, sorted by one of their numbers (lowest first)
  var order = [];
  for (var i = 0; i < plants.length; i++) {
    order.push(i);
  }
  order.sort(compareByKey);
  function compareByKey(a, b) {
    return key(plants[a]) - key(plants[b]);
  }
  return order;
}

function plantTop(plant) {
  return (field(plant, "elevation") || 0) + field(plant, "stemHeight");
}

function plantNorth(plant) {
  return -field(plant, "y");
}

function plantFill(plant) {
  // the colour and see-through-ness of a plant's canopy
  var number = field(plant, "species");
  if (highlightSpecies >= 0 && number !== highlightSpecies) {
    return { colour: cssColour("--other"), alpha: 0.18 };
  }
  if (colourBy === "light") {
    return { colour: lightColour(field(plant, "light")), alpha: 0.75 };
  }
  var colour = speciesColour(number);
  if (highlightSpecies >= 0 && run.species[number].slot < 0) {
    colour = cssColour("--series-1");
  }
  return { colour: colour, alpha: 0.6 };
}

// ---------------------------------------------------------------------------
// The map, from above
// ---------------------------------------------------------------------------

var terrainImage = null;     // the ground, drawn once per theme
var terrainImageDark = null;

function drawTerrain(context, left, top, size) {
  var terrain = run.header.terrain;
  if (!terrain) {
    return;
  }
  var dark = isDark();
  if ((dark && terrainImageDark === null) || (!dark && terrainImage === null)) {
    var image = document.createElement("canvas");
    image.width = terrain.cells;
    image.height = terrain.cells;
    var imageContext = image.getContext("2d");
    var low = cssColour("--terrain-low");
    var high = cssColour("--terrain-high");
    var highest = run.highestGround || 1;
    for (var row = 0; row < terrain.cells; row++) {
      for (var col = 0; col < terrain.cells; col++) {
        imageContext.fillStyle = mixColours(low, high, (terrain.elevation[row][col] || 0) / highest);
        // row 0 is the lowest y, which is at the bottom of the map
        imageContext.fillRect(col, terrain.cells - 1 - row, 1, 1);
      }
    }
    if (dark) {
      terrainImageDark = image;
    } else {
      terrainImage = image;
    }
  }
  context.imageSmoothingEnabled = true;
  if (dark) {
    context.drawImage(terrainImageDark, left, top, size, size);
  } else {
    context.drawImage(terrainImage, left, top, size, size);
  }
}

function waterPattern(context) {
  // Water is shown with thin diagonal lines, so it can't be mistaken for a
  // species or for the light colours, which are all solid fills.
  var tile = document.createElement("canvas");
  tile.width = 6;
  tile.height = 6;
  var tileContext = tile.getContext("2d");
  tileContext.strokeStyle = cssColour("--water");
  tileContext.lineWidth = 1;
  tileContext.beginPath();
  // a line from bottom left to top right, and the two corners of the lines
  // beside it, so the tiles join up
  tileContext.moveTo(0, 6);
  tileContext.lineTo(6, 0);
  tileContext.moveTo(-1, 1);
  tileContext.lineTo(1, -1);
  tileContext.moveTo(5, 7);
  tileContext.lineTo(7, 5);
  tileContext.stroke();
  return context.createPattern(tile, "repeat");
}

function drawWater(context, cycle, left, top, size) {
  var terrain = run.header.terrain;
  if (!terrain || cycle.waterLevel === null || cycle.waterLevel <= 0) {
    return;
  }
  // every cell under water goes into one shape, filled once
  var cell = size / terrain.cells;
  context.beginPath();
  for (var row = 0; row < terrain.cells; row++) {
    for (var col = 0; col < terrain.cells; col++) {
      if (terrain.elevation[row][col] <= cycle.waterLevel) {
        context.rect(left + col * cell, top + (terrain.cells - 1 - row) * cell, cell, cell);
      }
    }
  }
  context.fillStyle = waterPattern(context);
  context.fill();
}

function drawMap() {
  var canvas = document.getElementById("map-canvas");
  var sheet = prepareCanvas(canvas);
  var context = sheet.context;
  var cycle = run.cycles[cycleIndex];
  var world = run.header.worldSize;
  var pad = 8;
  var size = Math.min(sheet.width, sheet.height) - 2 * pad;
  var left = (sheet.width - size) / 2;
  var top = (sheet.height - size) / 2;
  var scale = size / world;
  function screenX(x) { return left + (x + world / 2) * scale; }
  function screenY(y) { return top + (world / 2 - y) * scale; }

  context.fillStyle = cssColour("--surface");
  context.fillRect(left, top, size, size);
  // nothing is drawn outside the world, even canopies that reach past its edge
  context.save();
  context.beginPath();
  context.rect(left, top, size, size);
  context.clip();
  drawTerrain(context, left, top, size);
  drawWater(context, cycle, left, top, size);

  // regions
  context.strokeStyle = cssColour("--ink-2");
  context.lineWidth = 1;
  context.fillStyle = cssColour("--ink-2");
  context.font = "12px system-ui, sans-serif";
  for (var r = 0; r < cycle.regions.length; r++) {
    var region = cycle.regions[r];
    context.beginPath();
    if (region.shape === "circle") {
      context.arc(screenX(region.x), screenY(region.y), region.size / 2 * scale, 0, 2 * Math.PI);
    } else {
      context.rect(screenX(region.x - region.size / 2), screenY(region.y + region.size / 2),
        region.size * scale, region.size * scale);
    }
    context.stroke();
    context.fillText(region.name + " (light " + region.lightIntensity + ")",
      screenX(region.x - region.size / 2) + 4, screenY(region.y + region.size / 2) + 14);
  }

  // seeds on the ground
  context.fillStyle = cssColour("--seed");
  context.globalAlpha = 0.55;
  for (var s = 0; s < cycle.seeds.length; s++) {
    var seed = cycle.seeds[s];
    context.fillRect(screenX(seed[0]) - 1, screenY(seed[1]) - 1, 2, 2);
  }
  context.globalAlpha = 1.0;

  // canopies, the tallest drawn last so they are on top
  var order = plantDrawOrder(cycle.plants, plantTop);
  var targets = [];
  for (var i = 0; i < order.length; i++) {
    var plant = cycle.plants[order[i]];
    var x = screenX(field(plant, "x"));
    var y = screenY(field(plant, "y"));
    var radius = Math.max(1.5, field(plant, "canopyRadius") * scale);
    var fill = plantFill(plant);
    context.globalAlpha = fill.alpha;
    context.fillStyle = fill.colour;
    context.beginPath();
    context.arc(x, y, radius, 0, 2 * Math.PI);
    context.fill();
    targets.push({ x: x, y: y, radius: Math.max(radius, 6), plant: plant });
  }
  context.globalAlpha = 1.0;

  // stems
  context.fillStyle = cssColour("--stem");
  for (var t = 0; t < cycle.plants.length; t++) {
    var stemPlant = cycle.plants[t];
    context.beginPath();
    context.arc(screenX(field(stemPlant, "x")), screenY(field(stemPlant, "y")),
      Math.max(1, field(stemPlant, "stemRadius") * scale), 0, 2 * Math.PI);
    context.fill();
  }
  context.restore();

  // the edge of the world
  context.strokeStyle = cssColour("--axis");
  context.strokeRect(left + 0.5, top + 0.5, size - 1, size - 1);

  hoverTargets["map-canvas"] = targets;
}

// ---------------------------------------------------------------------------
// The side view
// ---------------------------------------------------------------------------

function drawSide() {
  var canvas = document.getElementById("side-canvas");
  var sheet = prepareCanvas(canvas);
  var context = sheet.context;
  var cycle = run.cycles[cycleIndex];
  var world = run.header.worldSize;
  var padLeft = 36;
  var padRight = 10;
  var padTop = 10;
  var padBottom = 22;
  var width = sheet.width - padLeft - padRight;
  var height = sheet.height - padTop - padBottom;
  // the same scale across and up, so trees keep their shape, unless the
  // tallest tree would not fit
  var scaleX = width / world;
  var scaleY = Math.min(scaleX, height / (run.tallest * 1.05));
  function screenX(x) { return padLeft + (x + world / 2) * scaleX; }
  function screenY(z) { return padTop + height - z * scaleY; }

  // height axis and gridlines
  context.font = "12px system-ui, sans-serif";
  context.fillStyle = cssColour("--muted");
  context.strokeStyle = cssColour("--grid");
  context.lineWidth = 1;
  var visibleHeight = height / scaleY;
  var step = niceStep(visibleHeight, 5);
  for (var h = 0; h <= visibleHeight; h += step) {
    var gridY = Math.round(screenY(h)) + 0.5;
    context.beginPath();
    context.moveTo(padLeft, gridY);
    context.lineTo(padLeft + width, gridY);
    context.stroke();
    context.fillText(h + " m", 2, gridY + 4);
  }

  // water, then the ground in front of it (the highest ground across the world)
  var terrain = run.header.terrain;
  // nothing is drawn over the height labels or past the edge of the world
  context.save();
  context.beginPath();
  context.rect(padLeft, 0, width, sheet.height);
  context.clip();
  if (terrain && cycle.waterLevel !== null && cycle.waterLevel > 0) {
    context.fillStyle = waterPattern(context);
    context.fillRect(padLeft, screenY(cycle.waterLevel), width, cycle.waterLevel * scaleY);
  }
  context.fillStyle = cssColour("--terrain-high");
  context.beginPath();
  context.moveTo(padLeft, screenY(0));
  if (terrain) {
    for (var col = 0; col < terrain.cells; col++) {
      var highest = 0;
      for (var row = 0; row < terrain.cells; row++) {
        if (terrain.elevation[row][col] > highest) {
          highest = terrain.elevation[row][col];
        }
      }
      var groundX = -world / 2 + col * terrain.cellSize;
      context.lineTo(screenX(groundX), screenY(highest));
      context.lineTo(screenX(groundX + terrain.cellSize), screenY(highest));
    }
  }
  context.lineTo(padLeft + width, screenY(0));
  context.closePath();
  context.fill();
  context.strokeStyle = cssColour("--axis");
  context.beginPath();
  context.moveTo(padLeft, screenY(0) + 0.5);
  context.lineTo(padLeft + width, screenY(0) + 0.5);
  context.stroke();

  // plants, from the far (north) side to the near side
  var order = plantDrawOrder(cycle.plants, plantNorth);
  var targets = [];
  for (var i = order.length - 1; i >= 0; i--) {
    var plant = cycle.plants[order[i]];
    var x = screenX(field(plant, "x"));
    var base = field(plant, "elevation") || 0;
    var stemTop = base + field(plant, "stemHeight");
    var canopy = field(plant, "canopyRadius");
    // stem
    context.strokeStyle = cssColour("--stem");
    context.lineWidth = Math.max(1, 2 * field(plant, "stemRadius") * scaleX);
    context.beginPath();
    context.moveTo(x, screenY(base));
    context.lineTo(x, screenY(stemTop));
    context.stroke();
    // canopy: a dome whose top is the top of the stem, as in Vida's 3D files
    var fill = plantFill(plant);
    context.globalAlpha = fill.alpha;
    context.fillStyle = fill.colour;
    context.beginPath();
    context.ellipse(x, screenY(stemTop - canopy), Math.max(1.5, canopy * scaleX),
      Math.max(1.5, canopy * scaleY), 0, Math.PI, 2 * Math.PI);
    context.closePath();
    context.fill();
    context.globalAlpha = 1.0;
    targets.push({ x: x, y: screenY(stemTop - canopy / 2), radius: Math.max(6, canopy * scaleX), plant: plant });
  }

  // seeds on the ground
  context.fillStyle = cssColour("--seed");
  for (var s = 0; s < cycle.seeds.length; s++) {
    var seed = cycle.seeds[s];
    context.fillRect(screenX(seed[0]) - 1, screenY(seed[2] || 0) - 2, 2, 2);
  }
  context.restore();
  hoverTargets["side-canvas"] = targets;
}

// ---------------------------------------------------------------------------
// Charts over time
// ---------------------------------------------------------------------------

function drawLineChart(canvasId, lines) {
  // lines: [{name, colour, values}], one value per cycle
  var canvas = document.getElementById(canvasId);
  var sheet = prepareCanvas(canvas);
  var context = sheet.context;
  var padLeft = 44;
  var padRight = 16;
  var padTop = 10;
  var padBottom = 24;
  var width = sheet.width - padLeft - padRight;
  var height = sheet.height - padTop - padBottom;
  var cycles = run.cycles;
  var highest = 1;
  for (var l = 0; l < lines.length; l++) {
    for (var v = 0; v < lines[l].values.length; v++) {
      if (lines[l].values[v] > highest) {
        highest = lines[l].values[v];
      }
    }
  }
  var step = niceStep(highest, 4);
  var top = Math.ceil(highest / step) * step;
  var lastIndex = Math.max(1, cycles.length - 1);
  function screenX(index) { return padLeft + index / lastIndex * width; }
  function screenY(value) { return padTop + height - value / top * height; }

  // gridlines and axis labels
  context.font = "12px system-ui, sans-serif";
  context.lineWidth = 1;
  for (var tick = 0; tick <= top; tick += step) {
    var y = Math.round(screenY(tick)) + 0.5;
    if (tick === 0) {
      context.strokeStyle = cssColour("--axis");
    } else {
      context.strokeStyle = cssColour("--grid");
    }
    context.beginPath();
    context.moveTo(padLeft, y);
    context.lineTo(padLeft + width, y);
    context.stroke();
    context.fillStyle = cssColour("--muted");
    context.textAlign = "right";
    context.fillText(tick.toLocaleString(), padLeft - 6, y + 4);
  }
  context.textAlign = "center";
  var cycleStep = niceStep(cycles[cycles.length - 1].cycle - cycles[0].cycle + 1, 6);
  for (var c = 0; c < cycles.length; c++) {
    if (cycles[c].cycle % cycleStep === 0) {
      context.fillText(String(cycles[c].cycle), screenX(c), sheet.height - 6);
    }
  }
  context.textAlign = "left";

  // the cycle being shown
  context.strokeStyle = cssColour("--muted");
  context.beginPath();
  context.moveTo(Math.round(screenX(cycleIndex)) + 0.5, padTop);
  context.lineTo(Math.round(screenX(cycleIndex)) + 0.5, padTop + height);
  context.stroke();
  // the cycle the pointer is over
  var hoverIndex = chartHover[canvasId];
  if (hoverIndex !== undefined && hoverIndex !== cycleIndex) {
    context.strokeStyle = cssColour("--axis");
    context.setLineDash([3, 3]);
    context.beginPath();
    context.moveTo(Math.round(screenX(hoverIndex)) + 0.5, padTop);
    context.lineTo(Math.round(screenX(hoverIndex)) + 0.5, padTop + height);
    context.stroke();
    context.setLineDash([]);
  }

  // the lines
  context.lineWidth = 2;
  context.lineJoin = "round";
  context.lineCap = "round";
  for (var n = 0; n < lines.length; n++) {
    context.strokeStyle = lines[n].colour;
    context.beginPath();
    for (var i = 0; i < lines[n].values.length; i++) {
      if (i === 0) {
        context.moveTo(screenX(i), screenY(lines[n].values[i]));
      } else {
        context.lineTo(screenX(i), screenY(lines[n].values[i]));
      }
    }
    context.stroke();
    // a dot where the shown cycle is, and where the pointer is
    drawDot(context, screenX(cycleIndex), screenY(lines[n].values[cycleIndex]), lines[n].colour);
    if (hoverIndex !== undefined) {
      drawDot(context, screenX(hoverIndex), screenY(lines[n].values[hoverIndex]), lines[n].colour);
    }
    context.lineWidth = 2;
  }
  hoverTargets[canvasId] = { lines: lines, left: padLeft, width: width, lastIndex: lastIndex };
}

function drawDot(context, x, y, colour) {
  // a dot on a line, with a ring of the background colour round it
  context.fillStyle = colour;
  context.strokeStyle = cssColour("--surface");
  context.lineWidth = 2;
  context.beginPath();
  context.arc(x, y, 4, 0, 2 * Math.PI);
  context.fill();
  context.stroke();
}

function populationLines() {
  var plants = [];
  var seeds = [];
  for (var c = 0; c < run.cycles.length; c++) {
    plants.push(run.cycles[c].plants.length);
    seeds.push(run.cycles[c].seeds.length);
  }
  return [
    { name: "Plants", colour: cssColour("--series-1"), values: plants },
    { name: "Seeds", colour: cssColour("--series-2"), values: seeds },
  ];
}

function speciesLines() {
  // one line per coloured species, and one for all the others together
  var lines = [];
  var other = [];
  for (var c = 0; c < run.cycles.length; c++) {
    other.push(0);
  }
  for (var o = 0; o < run.speciesOrder.length; o++) {
    var number = run.speciesOrder[o];
    var values = [];
    for (var k = 0; k < run.cycles.length; k++) {
      values.push(run.cycles[k].plantsBySpecies[number]);
    }
    if (run.species[number].slot >= 0) {
      lines.push({ name: run.species[number].name, colour: speciesColour(number), values: values });
    } else {
      for (var m = 0; m < values.length; m++) {
        other[m] += values[m];
      }
    }
  }
  if (run.species.length > lines.length) {
    lines.push({ name: "Other species", colour: cssColour("--other"), values: other });
  }
  return lines;
}

// ---------------------------------------------------------------------------
// Numbers, legends and tables
// ---------------------------------------------------------------------------

function makeElement(tag, className, text) {
  var element = document.createElement(tag);
  if (className) {
    element.className = className;
  }
  if (text !== undefined) {
    element.textContent = text;
  }
  return element;
}

function statTile(label, value, detail) {
  var tile = makeElement("div", "stat");
  tile.appendChild(makeElement("div", "label", label));
  tile.appendChild(makeElement("div", "value", value));
  if (detail) {
    tile.appendChild(makeElement("div", "detail", detail));
  }
  return tile;
}

function drawStats() {
  var cycle = run.cycles[cycleIndex];
  var box = document.getElementById("stats");
  box.replaceChildren();
  var present = 0;
  for (var s = 0; s < cycle.plantsBySpecies.length; s++) {
    if (cycle.plantsBySpecies[s] > 0) {
      present += 1;
    }
  }
  var tallest = 0;
  for (var p = 0; p < cycle.plants.length; p++) {
    if (field(cycle.plants[p], "stemHeight") > tallest) {
      tallest = field(cycle.plants[p], "stemHeight");
    }
  }
  var mainCause = "";
  var mainCount = 0;
  for (var cause in cycle.deaths) {
    if (cycle.deaths[cause] > mainCount) {
      mainCount = cycle.deaths[cause];
      mainCause = cause;
    }
  }
  var detail = "";
  if (mainCount > 0) {
    detail = "most: " + mainCause + " (" + mainCount + ")";
  }
  box.appendChild(statTile("Plants", cycle.plants.length.toLocaleString()));
  box.appendChild(statTile("Seeds on the ground", cycle.seeds.length.toLocaleString()));
  box.appendChild(statTile("Species with plants", String(present), "of " + run.species.length));
  box.appendChild(statTile("Tallest stem", tallest.toFixed(1) + " m"));
  box.appendChild(statTile("Died this cycle", cycle.deathCount.toLocaleString(), detail));
  if (cycle.waterLevel !== null && run.header.terrain) {
    box.appendChild(statTile("Water level", cycle.waterLevel.toFixed(1) + " m"));
  }
}

function legendKey(colour, text, shape) {
  // shape is "swatch", "line" or "hatch" (hatch takes its colour from the css)
  var key = makeElement("span", "key");
  var mark = makeElement("span", shape);
  if (colour) {
    mark.style.background = colour;
  }
  key.appendChild(mark);
  key.appendChild(document.createTextNode(text));
  return key;
}

function drawLegends() {
  var mapLegend = document.getElementById("map-legend");
  mapLegend.replaceChildren();
  if (colourBy === "light") {
    var ramp = LIGHT_RAMP;
    if (isDark()) {
      ramp = LIGHT_RAMP_DARK;
    }
    var key = makeElement("span", "key");
    key.appendChild(document.createTextNode("Light received: none"));
    var bar = makeElement("span", "ramp");
    bar.style.background = "linear-gradient(to right, " + ramp.join(", ") + ")";
    key.appendChild(bar);
    key.appendChild(document.createTextNode("full"));
    mapLegend.appendChild(key);
  } else {
    var lines = speciesLines();
    for (var i = 0; i < lines.length; i++) {
      mapLegend.appendChild(legendKey(lines[i].colour, lines[i].name, "swatch"));
    }
  }
  mapLegend.appendChild(legendKey(cssColour("--stem"), "stems and seeds", "swatch"));
  if (run.header.terrain) {
    mapLegend.appendChild(legendKey(null, "water", "hatch"));
  }

  var populationLegend = document.getElementById("population-legend");
  populationLegend.replaceChildren();
  var population = populationLines();
  for (var p = 0; p < population.length; p++) {
    populationLegend.appendChild(legendKey(population[p].colour, population[p].name, "line"));
  }
  var speciesLegend = document.getElementById("species-legend");
  speciesLegend.replaceChildren();
  var species = speciesLines();
  for (var s = 0; s < species.length; s++) {
    speciesLegend.appendChild(legendKey(species[s].colour, species[s].name, "line"));
  }
}

function tableRow(cells, header) {
  var row = document.createElement("tr");
  for (var i = 0; i < cells.length; i++) {
    var cell = makeElement(header ? "th" : "td", i > 0 ? "number" : "", cells[i]);
    row.appendChild(cell);
  }
  return row;
}

function drawTables() {
  var cycle = run.cycles[cycleIndex];
  var speciesTable = document.getElementById("species-table");
  var caption = speciesTable.querySelector("caption");
  speciesTable.replaceChildren(caption);
  speciesTable.appendChild(tableRow(["Species", "Plants", "Seeds"], true));
  for (var o = 0; o < run.speciesOrder.length; o++) {
    var number = run.speciesOrder[o];
    speciesTable.appendChild(tableRow([run.species[number].name,
      String(cycle.plantsBySpecies[number]), String(cycle.seedsBySpecies[number])], false));
  }
  var deathsTable = document.getElementById("deaths-table");
  var deathsCaption = deathsTable.querySelector("caption");
  deathsTable.replaceChildren(deathsCaption);
  deathsTable.appendChild(tableRow(["Cause", "Number"], true));
  for (var cause in cycle.deaths) {
    deathsTable.appendChild(tableRow([cause, String(cycle.deaths[cause])], false));
  }
}

function drawEverything() {
  if (run === null) {
    return;
  }
  var cycle = run.cycles[cycleIndex];
  document.getElementById("cycle-slider").value = String(cycleIndex);
  document.getElementById("cycle-label").textContent =
    "Cycle " + cycle.cycle + " of " + run.cycles[run.cycles.length - 1].cycle;
  drawStats();
  drawMap();
  drawSide();
  drawLineChart("population-canvas", populationLines());
  drawLineChart("species-canvas", speciesLines());
  drawLegends();
  drawTables();
}

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

function showTooltip(pageX, pageY, title, rows) {
  // rows: [{name, value, colour (optional)}]. Text goes in with textContent.
  var tooltip = document.getElementById("tooltip");
  tooltip.replaceChildren();
  tooltip.appendChild(makeElement("div", "title", title));
  for (var i = 0; i < rows.length; i++) {
    var row = makeElement("div", "row");
    var name = makeElement("span", "name");
    if (rows[i].colour) {
      var mark = makeElement("span", "line");
      mark.style.background = rows[i].colour;
      name.appendChild(mark);
    }
    name.appendChild(document.createTextNode(rows[i].name));
    row.appendChild(name);
    row.appendChild(makeElement("span", "value", rows[i].value));
    tooltip.appendChild(row);
  }
  tooltip.hidden = false;
  var x = pageX + 14;
  var y = pageY + 14;
  if (x + tooltip.offsetWidth > window.innerWidth - 8) {
    x = pageX - tooltip.offsetWidth - 14;
  }
  if (y + tooltip.offsetHeight > window.innerHeight - 8) {
    y = pageY - tooltip.offsetHeight - 14;
  }
  tooltip.style.left = x + "px";
  tooltip.style.top = y + "px";
}

function hideTooltip() {
  document.getElementById("tooltip").hidden = true;
}

function leaveChart(event) {
  var canvasId = event.target.id;
  hideTooltip();
  if (chartHover[canvasId] !== undefined) {
    delete chartHover[canvasId];
    drawLineChart(canvasId, hoverTargets[canvasId].lines);
  }
}

function plantRows(plant) {
  var rows = [
    { name: "Stem height", value: field(plant, "stemHeight").toFixed(2) + " m" },
    { name: "Stem diameter", value: (field(plant, "stemRadius") * 200).toFixed(1) + " cm" },
    { name: "Canopy radius", value: field(plant, "canopyRadius").toFixed(2) + " m" },
    { name: "Light received", value: Math.round(field(plant, "light") * 100) + "%" },
    { name: "Age", value: field(plant, "age") + " years" },
    { name: "Mature", value: field(plant, "mature") ? "yes" : "no" },
  ];
  if (run.header.terrain) {
    rows.push({ name: "Ground height", value: (field(plant, "elevation") || 0).toFixed(2) + " m" });
  }
  return rows;
}

function hoverPlants(event, canvasId) {
  var targets = hoverTargets[canvasId];
  if (!targets || targets.length === 0) {
    hideTooltip();
    return;
  }
  var box = event.target.getBoundingClientRect();
  var x = event.clientX - box.left;
  var y = event.clientY - box.top;
  // the last one drawn (on top) that the pointer is over
  var found = null;
  for (var i = targets.length - 1; i >= 0; i--) {
    var dx = targets[i].x - x;
    var dy = targets[i].y - y;
    if (dx * dx + dy * dy <= targets[i].radius * targets[i].radius) {
      found = targets[i];
      break;
    }
  }
  if (found === null) {
    hideTooltip();
    return;
  }
  var number = field(found.plant, "species");
  showTooltip(event.clientX, event.clientY, run.species[number].name, plantRows(found.plant));
}

function chartIndexAt(event, canvasId) {
  var chart = hoverTargets[canvasId];
  var box = event.target.getBoundingClientRect();
  var fraction = (event.clientX - box.left - chart.left) / chart.width;
  var index = Math.round(fraction * chart.lastIndex);
  return Math.max(0, Math.min(run.cycles.length - 1, index));
}

function hoverChart(event, canvasId) {
  var chart = hoverTargets[canvasId];
  if (!chart) {
    return;
  }
  var index = chartIndexAt(event, canvasId);
  if (chartHover[canvasId] !== index) {
    chartHover[canvasId] = index;
    drawLineChart(canvasId, chart.lines);
  }
  var rows = [];
  for (var i = 0; i < chart.lines.length; i++) {
    rows.push({ name: chart.lines[i].name, value: chart.lines[i].values[index].toLocaleString(),
      colour: chart.lines[i].colour });
  }
  showTooltip(event.clientX, event.clientY, "Cycle " + run.cycles[index].cycle + " (click to show)", rows);
}

// ---------------------------------------------------------------------------
// Playing and controls
// ---------------------------------------------------------------------------

function showCycle(index) {
  cycleIndex = Math.max(0, Math.min(run.cycles.length - 1, index));
  drawEverything();
}

function play() {
  if (cycleIndex >= run.cycles.length - 1) {
    cycleIndex = 0;
  }
  var speed = Number(document.getElementById("speed-select").value);
  playTimer = window.setInterval(nextCycle, 1000 / speed);
  var button = document.getElementById("play-button");
  button.textContent = "Pause";
  button.setAttribute("aria-label", "Pause");
}

function pause() {
  if (playTimer !== null) {
    window.clearInterval(playTimer);
    playTimer = null;
  }
  var button = document.getElementById("play-button");
  button.textContent = "Play";
  button.setAttribute("aria-label", "Play");
}

function nextCycle() {
  if (cycleIndex >= run.cycles.length - 1) {
    pause();
    return;
  }
  showCycle(cycleIndex + 1);
}

function togglePlay() {
  if (playTimer === null) {
    play();
  } else {
    pause();
  }
}

function startViewing(name) {
  pause();
  terrainImage = null;
  terrainImageDark = null;
  highlightSpecies = -1;
  document.getElementById("welcome").hidden = true;
  document.getElementById("viewer").hidden = false;
  document.title = "Vida viewer: " + (run.header.name || name);
  var slider = document.getElementById("cycle-slider");
  slider.max = String(run.cycles.length - 1);
  var select = document.getElementById("highlight-select");
  select.replaceChildren(makeElement("option", "", "all species"));
  select.firstChild.value = "-1";
  for (var o = 0; o < run.speciesOrder.length; o++) {
    var option = makeElement("option", "", run.species[run.speciesOrder[o]].name);
    option.value = String(run.speciesOrder[o]);
    select.appendChild(option);
  }
  showCycle(0);
}

function onKey(event) {
  if (run === null || event.target.tagName === "SELECT" || event.target.tagName === "INPUT") {
    return;
  }
  if (event.key === " ") {
    event.preventDefault();
    togglePlay();
  } else if (event.key === "ArrowRight") {
    pause();
    showCycle(cycleIndex + 1);
  } else if (event.key === "ArrowLeft") {
    pause();
    showCycle(cycleIndex - 1);
  }
}

function switchTheme() {
  if (isDark()) {
    document.documentElement.dataset.theme = "light";
  } else {
    document.documentElement.dataset.theme = "dark";
  }
  updateThemeButton();
  drawEverything();
}

function updateThemeButton() {
  document.getElementById("theme-button").textContent = isDark() ? "Light" : "Dark";
}

function setUp() {
  document.getElementById("file-input").addEventListener("change", onFileChosen);
  function onFileChosen(event) {
    if (event.target.files.length > 0) {
      loadFile(event.target.files[0]);
    }
    // so choosing the same file again (after running Vida again) still loads it
    event.target.value = "";
  }
  document.getElementById("sample-button").addEventListener("click", onSample);
  function onSample() {
    loadUrl("sample/viewer.jsonl.gz");
  }
  document.getElementById("theme-button").addEventListener("click", switchTheme);
  document.getElementById("play-button").addEventListener("click", togglePlay);
  document.getElementById("cycle-slider").addEventListener("input", onSlide);
  function onSlide(event) {
    pause();
    showCycle(Number(event.target.value));
  }
  document.getElementById("speed-select").addEventListener("change", onSpeed);
  function onSpeed() {
    if (playTimer !== null) {
      pause();
      play();
    }
  }
  document.getElementById("colour-select").addEventListener("change", onColourBy);
  function onColourBy(event) {
    colourBy = event.target.value;
    drawEverything();
  }
  document.getElementById("highlight-select").addEventListener("change", onHighlight);
  function onHighlight(event) {
    highlightSpecies = Number(event.target.value);
    drawEverything();
  }

  var plantCanvases = ["map-canvas", "side-canvas"];
  for (var i = 0; i < plantCanvases.length; i++) {
    var canvas = document.getElementById(plantCanvases[i]);
    canvas.addEventListener("pointermove", onPlantHover);
    canvas.addEventListener("pointerleave", hideTooltip);
  }
  function onPlantHover(event) {
    hoverPlants(event, event.target.id);
  }
  var chartCanvases = ["population-canvas", "species-canvas"];
  for (var j = 0; j < chartCanvases.length; j++) {
    var chart = document.getElementById(chartCanvases[j]);
    chart.addEventListener("pointermove", onChartHover);
    chart.addEventListener("pointerleave", leaveChart);
    chart.addEventListener("click", onChartClick);
  }
  function onChartHover(event) {
    hoverChart(event, event.target.id);
  }
  function onChartClick(event) {
    pause();
    showCycle(chartIndexAt(event, event.target.id));
  }

  document.addEventListener("keydown", onKey);
  window.addEventListener("resize", drawEverything);
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", onSystemTheme);
  function onSystemTheme() {
    updateThemeButton();
    drawEverything();
  }

  // dropping a file anywhere on the page
  var overlay = document.getElementById("drop-overlay");
  document.addEventListener("dragover", onDragOver);
  function onDragOver(event) {
    event.preventDefault();
    overlay.hidden = false;
  }
  overlay.addEventListener("dragleave", onDragLeave);
  function onDragLeave() {
    overlay.hidden = true;
  }
  document.addEventListener("drop", onDrop);
  function onDrop(event) {
    event.preventDefault();
    overlay.hidden = true;
    if (event.dataTransfer.files.length > 0) {
      loadFile(event.dataTransfer.files[0]);
    }
  }

  updateThemeButton();
  // viewer/index.html?data=path/to/viewer.jsonl opens that file straight away
  var dataUrl = new URLSearchParams(window.location.search).get("data");
  if (dataUrl) {
    loadUrl(dataUrl);
  }
}

setUp();
