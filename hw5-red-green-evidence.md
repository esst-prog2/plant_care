# HW5: red, then green

Test: `tests/test_web.py::test_watering_interval_is_labelled_as_an_estimate`
Expected value (fixed before the test was written): the label text `Watering (estimate)`,
from `openspec/specs/plant-collection/spec.md` (written 2026-10-02, following the HW4 spike).

## Red

Broke the promise by changing one line in `app/templates/_details.html`:
`<dt>Watering (estimate)</dt>` → `<dt>Watering</dt>`. Ran
`pytest tests/test_web.py::test_watering_interval_is_labelled_as_an_estimate`:

```
F                                                                        [100%]
================================== FAILURES ===================================
______________ test_watering_interval_is_labelled_as_an_estimate ______________

    def test_watering_interval_is_labelled_as_an_estimate(client, db):
        add_ready(db, "Monstera", interval=7)
        html = client.get("/plants/1").text
>       assert "Watering (estimate)" in html
E       assert 'Watering (estimate)' in '<div class="overlay" role="dialog" ...>...</div>'

tests\test_web.py:189: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_web.py::test_watering_interval_is_labelled_as_an_estimate
1 failed, 1 warning in 0.60s
```

## Green

Put the line back (`<dt>Watering (estimate)</dt>`) and ran the full suite:

```
............................................................................... [100%]
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
123 passed, 1 warning in 5.76s
```
