# Vida viewer

A web page for watching a Vida simulation cycle by cycle. It is plain HTML, CSS
and JavaScript: nothing to install and no build step.

## Using it

1. Run Vida with `-j` to save every cycle:

   ```
   python Vida.py -n test -s 100 -t 60 -j
   ```

   This writes `Output-test/viewer.jsonl` next to the usual output files.

2. Open `viewer/index.html` in a web browser and click **Open viewer.jsonl…**
   (or drop the file on the page). Files compressed with gzip (`.gz`) open too,
   which helps with long runs: a `viewer.jsonl` usually shrinks to about a
   quarter of its size.

To see an example without running Vida, click **Load sample**. Browsers do not
let a page opened straight from the disk read other files, so for that button
(and for `?data=`, below) serve the folder first:

```
cd viewer
python -m http.server
```

and go to <http://localhost:8000>. A file can be opened straight away with
`http://localhost:8000/?data=path/to/viewer.jsonl`.

## What it shows

Choose **View** to switch between the map and side view (below) and the
**natural scene**, a 3D picture of the world you can turn round and zoom
into (see [The natural scene](#the-natural-scene)).

- **From above**: the world, with every canopy as a circle. The ground is
  shaded by height when a terrain file is used, and ground under water is
  hatched. Regions are outlined.
- **From the side**: every plant seen from the south, with its stem and a dome
  for its canopy (the top of the dome is the top of the stem, as in Vida's 3D
  files). Heights and widths use the same scale unless the tallest plant
  would not fit.
- **Plants and seeds** and **Plants by species**: the counts over the whole
  run. Hover to read the numbers, click to jump to that cycle.
- A table of this cycle's species and causes of death, under **Table view**.

The three species with the most plants over the run each get a colour and
the rest are grouped as "Other species". **Highlight** picks out any one
species. **Colour by light received** shades each canopy by the part of it in
sunlight (Vida's `fractionExposed`). Hover over a plant for its details.

Keys: space plays and pauses, the left and right arrows step one cycle.

## The natural scene

What comes from the simulation is drawn to scale:

- where each plant stands, and the height of the ground under it;
- its stem: a cylinder of the stem's height and width, as in Vida's 3D
  (`.dxf`) files;
- its crown: as wide as the canopy radius, with its top at the top of the
  stem. With **Crowns: as Vida draws them** it is the top half of a sphere,
  as deep as it is wide, or, for species with `crownShape: PARA` in their
  species file, reaching from `boleHeight` percent of the way down the tree
  to the top, as in Vida's 3D files;
- the ground, from the terrain file, and the water level;
- how much light each plant got: leaves are darker where it got less, as in
  Vida's own pictures. **Colour by light received** colours them by it
  instead, and **Highlight** greys out the other species;
- the shade of the canopies on the ground, worked out straight down as Vida
  does: the ground is darker and the grass thinner and shorter under the
  trees.

Everything else is decoration, to make it look like a real place:

- **Crowns: shaped by genus** (the first word of the species name) gives
  each kind of tree its own outline, keeping the plant's height and canopy
  radius: pines grow a long bare trunk with the crown near the top, oaks a
  broad rounded crown, dogwoods a low flat-topped one, sweetgums and
  blackgums pointed ones, and so on (`CROWN_FORMS` in `scene/trees.js`).
  Young trees of every kind have fuller, more pointed crowns;
- leaves by genus too: pines have long needles in tufts, spruces, firs and
  other conifers short needles, and the broadleaved trees their own leaves:
  lobed oak leaves, maple leaves, star-shaped sweetgum leaves, hickory's
  leaflets, big glossy magnolia leaves and plain oval leaves for the rest
  (`FOLIAGE` in `scene/trees.js`), each in its genus's summer green;
- a physically based sky (the Preetham model, from three.js's
  `examples/jsm/objects/Sky.js`) with drifting clouds, and a sun you can put
  at any time of day with the **Sun** slider. **overhead, as Vida's light
  is** puts it straight above, so the shadows fall where the simulation's
  shade does;
- hundreds of thousands of blades of grass, swaying in rolling gusts of wind
  and glowing when the sun is behind them (after well-known open-source
  grass such as al-ro's instanced grass and James Smyth's Breath of the Wild
  style grass), with a scattering of wildflowers;
- water that reflects the world (the reflection maths is from three.js's
  `examples/jsm/objects/Reflector.js`), more so the lower you look across it,
  shows the bottom in the shallows and is dark where deep, glints in the sun
  and has foam along the shore, with a net of light (caustics) on the bottom;
- leaves that sway and glow when the sun shines through them, bark, soil,
  layered rock and wet mud, dust in the air, birds overhead and fireflies at
  dusk;
- all round, well away from the simulated world: low hills with woods on
  them, and blue mountains on the skyline;
- bloom, light shafts through the trees, the ACES filmic curve and a gentle
  colour grade.

Drag to turn, scroll or pinch to zoom, right-drag (or shift-drag, or two
fingers) to move, and double-click to go back to the first view. **Tour**
circles slowly round the world; **wind and water** stops everything moving
(and the page then only draws when something changes). **Quality** chooses
how much grass, how many leaves and how sharp the shadows and reflections
are: high on computers and medium on phones to begin with.

It is drawn with [three.js](https://threejs.org), which is in
`lib/three.min.js` (MIT licence, in `lib/three.LICENSE`). That is version
r149, the last one that works as a plain script, so the page still works
when opened straight from the disk. The scene's own code is in `scene/`,
one file per part (the list is at the top of `scene/scene.js`). None of it
is loaded until the scene is first shown.

## The file

`viewer.jsonl` is "JSON Lines": one JSON object per line. The first line
describes the world and each line after it is one cycle. Plants and seeds are
lists of numbers, in the order given by `plantFields` and `seedFields` in the
first line, to keep the file small. `Vida_Data/vjson.py` writes it and
describes it in full.

## The sample

`sample/viewer.jsonl.gz` is 90 cycles of the CatLand terrain with 19 species.
To make it again (for example after the file format changes), run from the
top folder:

```
python Vida.py -n sample -w 50 -s 150 -t 90 -m 3000 -seed 11 -j -i "Terrain_files/CatLand with xlsx" -iwater 1.5 -a n -f n
gzip -9 -n -c Output-sample/viewer.jsonl > viewer/sample/viewer.jsonl.gz
```

## Changing it

- `index.html` is the layout, `viewer.css` the colours and spacing,
  `scene/` the natural scene, and `viewer.js` everything else. The
  sections of `viewer.js` and the files in `scene/` are listed at their
  tops.
- All colours are set once, at the top of `viewer.css`, for the light and
  the dark theme.
- Anything new in the file should be added to `vjson.py` and to the list of
  fields in its first line, so older viewer files still open.
