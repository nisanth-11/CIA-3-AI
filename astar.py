import heapq

MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(cell, grid_width, grid_height, obstacles):
    x, y = cell
    for dx, dy in MOVES:
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid_width and 0 <= ny < grid_height and (nx, ny) not in obstacles:
            yield (nx, ny)


def a_star(grid_width, grid_height, obstacles, start, goal):
    frontier = [(heuristic(start, goal), 0, start)]
    came_from = {start: None}
    g_score = {start: 0}
    visited = set()
    nodes_expanded = 0
    expansion_log = []

    while frontier:
        f, g, current = heapq.heappop(frontier)

        if current in visited:
            continue
        visited.add(current)

        nodes_expanded += 1
        h = heuristic(current, goal)
        expansion_log.append((current, g, h, f))

        if current == goal:
            path = []
            node = current
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path, nodes_expanded, expansion_log

        for neighbor in neighbors(current, grid_width, grid_height, obstacles):
            tentative_g = g + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                h_n = heuristic(neighbor, goal)
                heapq.heappush(frontier, (tentative_g + h_n, tentative_g, neighbor))

    return [], nodes_expanded, expansion_log