# Tests

```sh
pip install -r requirements.txt -r requirements-dev.txt
pytest -n auto
```

* `unit/` checks individual functions: the geometry helpers, reading
  heights from a terrain image, and the growth equations in `vplantr.py`.
  Each test is a small worked example of one equation, and the fastest
  place to see what a function does.
* `characterization/` runs whole simulations and checks that the results
  are exactly the same as when they were recorded. See the README there.
