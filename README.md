# Emergency Response Ambulance — AI Express Hackathon (Track 4)


## What it does

An ambulance agent drives across a 10x10 grid city from its depot `(0,0)` to
a hospital `(9,9)`, using **A\* Search** with the **Manhattan distance
heuristic**. There is one static obstacle — a building row with a single
street gate, at a **randomized row/gap each run** (the seed used is printed
at startup, so a specific layout can be reproduced later). Partway along
its route, **two traffic blockages suddenly spawn** on the road ahead, one
after another. Each time, the agent detects it, **replans from its current
position** (not from the depot) with a fresh A\* call over the updated
obstacle set, and continues live to the hospital along the new route — no
restart. The grid also visualizes the search itself (which cells A* explored)
before each movement phase, and shows a live stats panel alongside the
console log.

## How to run

Requires Python 3 with `tkinter`. No third-party dependencies — but on
**macOS**, the system Python's bundled Tk (8.5) has a long-standing bug
that renders the canvas as solid black. Use a Python built against a
modern Tk instead:

```bash
brew install python-tk   # pulls in a modern python3 + tcl-tk (one-time)
/opt/homebrew/bin/python3.14 main.py
```

(On Linux/Windows, or any Python already linked against Tk 8.6+, plain
`python3 main.py` is fine.)

The window shows the grid (white = free road, gray = buildings, green =
depot, red = hospital, blue = ambulance, orange = the dynamically spawned
blockage). The console logs the initial plan, every movement step
(coordinates, g/h/f, running cost), the blockage event, the replan (from
where, new nodes expanded, new route), and a final summary covering both
search phases.

## Files

- `astar.py` — grid-independent A* implementation (heuristic, search,
  path reconstruction). No knowledge of grids, walls, or blockages.
- `planner.py` — all decision-making logic: random wall generation,
  dynamic blockage scheduling (with a reachability check so a blockage
  can never seal off the only route), and replanning. Pure logic, no
  Tkinter — every function takes plain data in and returns plain data
  out, so it's independently testable.
- `main.py` — Tkinter GUI: grid drawing, agent movement animation,
  search-exploration visualization, the live stats panel, and console
  logging. Calls into `planner` for every decision; has no direct
  dependency on `astar.py`.

`astar.py` + `planner.py` form the "AI/algorithm" half of the project;
`main.py` is the "visualization/presentation" half — a natural split for
two people to own separately.

## Algorithm summary

- **State**: ambulance's `(x, y)` cell.
- **Initial state**: `(0, 0)` (depot).
- **Goal test**: cell `== (9, 9)` (hospital).
- **Actions**: move up / down / left / right, cost 1 each.
- **Heuristic**: Manhattan distance — admissible and consistent, so each
  A\* call (initial and replan) is individually optimal.
- **Dynamic replanning**: when the agent is a few cells from a
  pre-determined trigger point, a new obstacle cell is added to the
  obstacle set ahead on its route. A\* is re-run with `start` = the
  agent's current cell and the updated obstacle set; the resulting
  sub-path is spliced onto the cells already traveled, and animation
  continues without resetting to the depot.# CIA-3-AI