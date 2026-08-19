from astar import a_star, heuristic

__all__ = ["a_star", "heuristic", "generate_wall", "initial_plan",
           "schedule_next_blockage", "replan_from"]


def generate_wall(rng, grid_width, grid_height, start, goal):
    while True:
        wall_row = rng.randint(2, grid_height - 3)
        gap_col = rng.randint(0, grid_width - 1)
        obstacles = {(x, wall_row) for x in range(grid_width) if x != gap_col}
        path, _, _ = a_star(grid_width, grid_height, obstacles, start, goal)
        if path:
            return obstacles, wall_row, gap_col


def initial_plan(grid_width, grid_height, obstacles, start, goal):
    return a_star(grid_width, grid_height, obstacles, start, goal)


def schedule_next_blockage(path, step_index, obstacles, pending_fractions,
                            grid_width, grid_height, goal):
    pending = list(pending_fractions)
    while pending:
        fraction = pending.pop(0)
        remaining = path[step_index:]
        if len(remaining) < 6:
            continue
        base_offset = min(max(3, int(len(remaining) * fraction)), len(remaining) - 2)
        for delta in (0, 1, -1, 2, -2, 3, -3):
            offset = base_offset + delta
            if offset < 3 or offset > len(remaining) - 2:
                continue
            candidate_cell = path[step_index + offset]
            trial_obstacles = set(obstacles)
            trial_obstacles.add(candidate_cell)
            trial_path, _, _ = a_star(grid_width, grid_height, trial_obstacles,
                                       path[step_index], goal)
            if trial_path:
                trigger_step = step_index + max(2, offset - 3)
                return candidate_cell, trigger_step, pending
    return None, None, pending


def replan_from(current_cell, obstacles, grid_width, grid_height, goal):
    return a_star(grid_width, grid_height, obstacles, current_cell, goal)