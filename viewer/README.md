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

- `index.html` is the layout, `viewer.css` the colours and spacing, and
  `viewer.js` everything else. The sections of `viewer.js` are listed at its
  top.
- All colours are set once, at the top of `viewer.css`, for the light and
  the dark theme.
- Anything new in the file should be added to `vjson.py` and to the list of
  fields in its first line, so older viewer files still open.
