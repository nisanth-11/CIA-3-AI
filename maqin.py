import random
import time
import tkinter as tk

import planner
from planner import heuristic

GRID_WIDTH = 10
GRID_HEIGHT = 10
CELL_SIZE = 45
STEP_DELAY_MS = 300
SEARCH_STEP_DELAY_MS = 12
SEARCH_PAUSE_MS = 250

START = (0, 0)
GOAL = (9, 9)

RANDOM_SEED = None

BLOCKAGE_COUNT = 2
BLOCKAGE_FRACTION_RANGE = (0.4, 0.75)

COLOR_FREE = "white"
COLOR_OBSTACLE = "#555555"
COLOR_START = "#4CAF50"
COLOR_GOAL = "#F44336"
COLOR_AGENT = "#2196F3"
COLOR_EXPLORED = "#90CAF9"
COLOR_TRAVELED = "#C8E6C9"
COLOR_BLOCKAGE = "#FF9800"


class AmbulanceGUI:
    def __init__(self, root, static_obstacles, rng):
        self.root = root
        self.static_obstacles = static_obstacles
        self.rng = rng
        self.obstacles = set(static_obstacles)
        self.blockage_cell = None
        self.replanned_count = 0
        self.total_nodes_expanded = 0
        self.total_search_time = 0.0
        self.traveled = set()
        self.pending_blockage_fractions = [
            rng.uniform(*BLOCKAGE_FRACTION_RANGE) for _ in range(BLOCKAGE_COUNT)
        ]
        self.next_blockage_cell = None
        self.next_trigger_step = None
        self.phase = "Setup"
        self.path = []
        self.step_index = 0

        canvas_w = GRID_WIDTH * CELL_SIZE
        canvas_h = GRID_HEIGHT * CELL_SIZE
        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.status = tk.Label(root, text="", font=("Courier", 11), justify="left", anchor="w")
        self.status.pack(fill="x")

        self.cell_rects = {}
        self._draw_grid()
        self.agent = self._draw_marker(START, COLOR_AGENT)

        print(f"[SETUP] Grid {GRID_WIDTH}x{GRID_HEIGHT} | depot={START} | hospital={GOAL} | "
              f"static obstacles={len(self.static_obstacles)}")

        t0 = time.perf_counter()
        self.path, nodes, log = planner.initial_plan(GRID_WIDTH, GRID_HEIGHT, self.obstacles, START, GOAL)
        search_time = time.perf_counter() - t0
        self.total_nodes_expanded += nodes
        self.total_search_time += search_time

        print(f"[PLAN] Initial route computed in {search_time*1000:.3f} ms | "
              f"nodes expanded: {nodes} | cost: {len(self.path)-1}")
        print(f"[PLAN] Route: {self.path}")
        print()

        if not self.path:
            self.phase = "Blocked"
            self._update_stats_panel("No route to the hospital.")
            return

        self._schedule_next_blockage()
        self.phase = "Searching"
        self._update_stats_panel()
        self._animate_search(log, on_complete=self._continue_movement)

    def _draw_grid(self):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                x0, y0 = x * CELL_SIZE, y * CELL_SIZE
                x1, y1 = x0 + CELL_SIZE, y0 + CELL_SIZE
                if (x, y) in self.static_obstacles:
                    color = COLOR_OBSTACLE
                elif (x, y) == START:
                    color = COLOR_START
                elif (x, y) == GOAL:
                    color = COLOR_GOAL
                else:
                    color = COLOR_FREE
                rect = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="#cccccc")
                self.cell_rects[(x, y)] = rect

    def _draw_marker(self, cell, color):
        x, y = cell
        x0, y0 = x * CELL_SIZE, y * CELL_SIZE
        x1, y1 = x0 + CELL_SIZE, y0 + CELL_SIZE
        pad = 6
        return self.canvas.create_oval(x0 + pad, y0 + pad, x1 - pad, y1 - pad, fill=color, outline="")

    def _move_agent_to(self, cell):
        x, y = cell
        x0, y0 = x * CELL_SIZE, y * CELL_SIZE
        pad = 6
        self.canvas.coords(self.agent, x0 + pad, y0 + pad,
                            x0 + CELL_SIZE - pad, y0 + CELL_SIZE - pad)

    def _mark_traveled(self, cell):
        self.traveled.add(cell)
        if cell in (START, GOAL):
            return
        self.canvas.itemconfig(self.cell_rects[cell], fill=COLOR_TRAVELED)

    def _update_stats_panel(self, extra=""):
        total_cost = len(self.path) - 1 if self.path else 0
        lines = [
            f"Phase: {self.phase}",
            f"Step: {self.step_index}/{total_cost}   Cost so far: {min(self.step_index, total_cost)}",
            f"Nodes expanded (total): {self.total_nodes_expanded}   "
            f"Search time (total): {self.total_search_time*1000:.2f} ms",
            f"Blockages encountered: {self.replanned_count}",
        ]
        if extra:
            lines.append(extra)
        self.status.config(text="\n".join(lines))

    def _schedule_next_blockage(self):
        self.next_blockage_cell, self.next_trigger_step, self.pending_blockage_fractions = (
            planner.schedule_next_blockage(self.path, self.step_index, self.obstacles,
                                            self.pending_blockage_fractions,
                                            GRID_WIDTH, GRID_HEIGHT, GOAL)
        )

    def _trigger_blockage(self, current_cell):
        self.blockage_cell = self.next_blockage_cell
        self.next_trigger_step = None
        self.obstacles.add(self.blockage_cell)
        self.canvas.itemconfig(self.cell_rects[self.blockage_cell], fill=COLOR_BLOCKAGE)
        print(f"[EVENT] Sudden traffic blockage spawned at {self.blockage_cell}!")

        print(f"[REPLAN] Ambulance at {current_cell} detects the blockage ahead. Replanning "
              f"(NOT restarting from depot)...")
        t0 = time.perf_counter()
        new_path, nodes, log = planner.replan_from(current_cell, self.obstacles, GRID_WIDTH, GRID_HEIGHT, GOAL)
        search_time = time.perf_counter() - t0
        self.total_nodes_expanded += nodes
        self.total_search_time += search_time

        if not new_path:
            print("[REPLAN] No alternate route found!")
            self.phase = "Blocked"
            self._update_stats_panel("Blocked: no alternate route to the hospital.")
            return

        self.path = self.path[:self.step_index + 1] + new_path[1:]
        self.step_index += 1
        self.replanned_count += 1
        print(f"[REPLAN] New route computed in {search_time*1000:.3f} ms | "
              f"nodes expanded: {nodes} | remaining cost: {len(new_path)-1}")
        print(f"[REPLAN] Updated route: {self.path}")
        print()

        self._schedule_next_blockage()
        self.phase = "Replanning"
        self._update_stats_panel()
        self._animate_search(log, on_complete=self._continue_movement)

    def _animate_search(self, log, on_complete):
        self._search_log = log
        self._search_idx = 0
        self._search_on_complete = on_complete
        self._search_step()

    def _search_step(self):
        if self._search_idx >= len(self._search_log):
            self.root.after(SEARCH_PAUSE_MS, self._search_on_complete)
            return
        cell, g, h, f = self._search_log[self._search_idx]
        if (cell not in (START, GOAL) and cell not in self.static_obstacles
                and cell != self.blockage_cell and cell not in self.traveled):
            self.canvas.itemconfig(self.cell_rects[cell], fill=COLOR_EXPLORED)
        self._search_idx += 1
        self.root.after(SEARCH_STEP_DELAY_MS, self._search_step)

    def _continue_movement(self):
        self.phase = "Moving"
        self._update_stats_panel()
        if self.step_index < len(self.path):
            self.root.after(STEP_DELAY_MS, self._animate_step)
        else:
            self._finish()

    def _animate_step(self):
        cell = self.path[self.step_index]
        self._move_agent_to(cell)
        self._mark_traveled(cell)

        g = self.step_index
        h = heuristic(cell, GOAL)
        line = f"Step {self.step_index:2d}: ambulance at {cell} | g={g} h={h} f={g+h} | cost so far={g}"
        print(f"[MOVE] {line}")
        self._update_stats_panel()

        if self.next_trigger_step is not None and self.step_index == self.next_trigger_step:
            self._trigger_blockage(cell)
            return

        self.step_index += 1
        if self.step_index < len(self.path):
            self.root.after(STEP_DELAY_MS, self._animate_step)
        else:
            self._finish()

    def _finish(self):
        total_cost = len(self.path) - 1
        self.phase = "Done"
        summary = (f"Reached hospital {GOAL} | total cost={total_cost} | "
                   f"nodes expanded={self.total_nodes_expanded} | "
                   f"search time={self.total_search_time*1000:.2f} ms | "
                   f"blockages encountered={self.replanned_count}")
        print(f"[SUMMARY] {summary}")
        self._update_stats_panel(summary)


def _nudge_repaint(root):
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    root.geometry(f"{w+1}x{h+1}")
    root.after(50, lambda: root.geometry(f"{w}x{h}"))


def main():
    seed = RANDOM_SEED if RANDOM_SEED is not None else random.SystemRandom().randrange(10**9)
    rng = random.Random(seed)
    static_obstacles, wall_row, gap_col = planner.generate_wall(rng, GRID_WIDTH, GRID_HEIGHT, START, GOAL)
    print(f"[SETUP] seed={seed} | wall row={wall_row} gap col={gap_col} "
          f"(hardcode RANDOM_SEED={seed} to reproduce this exact layout)")

    root = tk.Tk()
    root.title("Emergency Response Ambulance — Dynamic A* Replanning")
    AmbulanceGUI(root, static_obstacles, rng)
    root.after(150, lambda: _nudge_repaint(root))
    root.mainloop()


if __name__ == "__main__":
    main()