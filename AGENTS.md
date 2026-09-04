# Agent notes — IPA/water distillation app

Facts from production breakage and profiling. Not style preferences.

## Rating vs design

- Design steps Ponchon–Savarit to a purity target. Rating inverts the monotone
  `N(x_D)` at fixed `R` and `D`.
- Probes interpolate the cached saturation envelope (`dew_envelope` /
  `bubble_envelope`); one exact `solve_design_column` at the selected split
  draws the charts. Do not call the full design solver 14 times.
- Unattainable `N` returns the window endpoint. 10 and 13 stages can be the
  same column. Say so in the banner; do not fake extra stages.
- McCabe–Thiele is independent CMO. It can pinch (`R < R_min`) while Ponchon
  still closes — especially saturated-vapour feed near the azeotrope. Report
  a pinch, not a 100-stage staircase.

## Feed stage

- Hardware, not a locker DOF. Default is the feed-line crossing (tutorial §5D).
- Specified tray must change the Ponchon switch *and* the McCabe operating-line
  switch (`feed_stage_spec`). A number input that only tie-breaks is a lie.
- Clamp `specified_feed_stage` before render when `N` shrinks
  (`StreamlitValueAboveMaxError`). Sequence-test it.

## Charts

- McCabe (`key` prefix `xy_`) is the only 1:1 mole-fraction plot. T-x-y and
  Ponchon are not square.
- Do not use Plotly `scaleanchor` here. Streamlit fullscreen writes the
  viewport into `layout.width/height`; on revert the stale height plus
  scaleanchor is the postage-stamp subplot. `inject_square_xy_guard` pads
  fullscreen and restores a square figure after.
- Hash physics into Plotly `key=` or traces from the previous solve can stick.

## Cloud

- `_refresh_source_modules` is keyed on a hash of `app.py` and `src.*`. A
  no-argument `@st.cache_resource` will skip reload when Community Cloud
  hot-swaps files without a process restart.
- `hasattr` new `src.ui` entry points so a stale module cannot crash the app.
  If the red banner survives a deploy, reboot from Manage app.

## Tests

- Golden characterization (`tests/golden/reference.npz`) pins design physics
  at 1e-8..1e-12. Do not regenerate to make a refactor pass.
- CSS must not use `:has()`. AppTest sequences, not single renders, catch
  widget `max_value` crashes.
