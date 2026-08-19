# Technical Summary — Emergency Response Ambulance

## 1. Header & Team Info

| Field | Value |
|---|---|
| Course Code | _fill in_ |
| Group Number | _10_ |
| Member Names | _Nisanth V S- 2441640, Niharika Nair - 2441638, Ramona Elisha - 2441646_ |
| Selected Track | Track 4 — Emergency Response Ambulance (Dynamic A\* / Replanning) |
| GitHub Repository URL | _fill in_ |

## 2. PEAS Framework Matrix

| Component | Description |
|---|---|
| **Performance Measure** | Total path cost (moves) to reach the hospital; minimizing nodes expanded / search time across both the initial plan and any replans. |
| **Environment** | 10x10 grid city with one static building row (single gate). **Dynamic**: a traffic blockage can spawn on the road mid-route, unknown at planning time. Otherwise deterministic and discrete. |
| **Actuators** | Move Up / Down / Left / Right one cell at a time. |
| **Sensors** | Full visibility of the static grid at all times, plus detection of a new blockage once it spawns on the route ahead (the trigger for replanning). |

## 3. Core Algorithmic Formulation

- **State space**: every free `(x, y)` cell on the 10x10 grid, `x, y ∈ [0, 9]`.
- **Initial state**: `(0, 0)` (depot).
- **Goal test**: current cell `== (9, 9)` (hospital).
- **Path cost**: 1 per move (uniform step cost).
- **Heuristic**:
  ```
  h(n) = |x1 - x2| + |y1 - y2|      (Manhattan distance to goal)
  ```
  Admissible and consistent (no diagonal moves), so every individual A\*
  call — initial plan and each replan — is optimal for the information
  available at that moment.
- **Dynamic replanning rule**: when the agent detects a new blockage on its
  planned route, A\* is re-invoked with `start` = the agent's *current*
  cell (not the depot) and the obstacle set extended with the blockage.
  The returned sub-path replaces the untraveled remainder of the route.
  This is a form of **online replanning search**: the agent commits to
  actions as it learns more about the environment, rather than assuming a
  fully known static world up front.

## 4. Complexity Analysis

| | Theoretical | Observed (this run) |
|---|---|---|
| **Time** | `O(b^d)` per A\* call, `b = 4`. Total cost with `k` replans is `O(k · b^d)` in the worst case, since each replan is a fresh bounded search from the agent's current position (not the full remaining problem from scratch each time — the agent doesn't restart from the depot). | Initial plan: 61 nodes expanded, 0.086 ms. One replan: 22 nodes expanded, 0.258 ms. Total: 83 nodes, 0.344 ms for an 18-step route with one dynamic blockage. |
| **Space** | `O(b^d)` per A\* call (open + closed sets), freed between calls. | Peak of 61 nodes stored during the larger (initial) search — well under the 100-cell grid. |

Replanning from the agent's live position (instead of restarting from the
depot) keeps each individual A\* call small: the reroute search after the
blockage expanded only 22 nodes — about a third of the initial search —
because it only had to solve the *remaining* sub-problem.
