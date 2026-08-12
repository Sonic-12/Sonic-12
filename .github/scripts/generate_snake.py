
import os
import random


COLS, ROWS = 22, 11
CELL = 20
PAD = 10
W = COLS * CELL + PAD * 2
H = ROWS * CELL + PAD * 2

STEP_DUR = 0.28       
MAX_STEPS = 140       

BG = "#1a1b27"
GRID_LINE = "#20222f"
SNAKE_HEAD = "#7aa2f7"
SNAKE_BODY = "#3d59a1"
FOOD = "#f7768e"
BORDER = "#414868"

random.seed()  


def in_bounds(c):
    x, y = c
    return 0 <= x < COLS and 0 <= y < ROWS


def new_food(snake_set):
    free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in snake_set]
    return random.choice(free) if free else None


def px(cell):
    x, y = cell
    return PAD + x * CELL + CELL / 2, PAD + y * CELL + CELL / 2


def build_svg(frames):
    n_frames = len(frames)
    total_dur = n_frames * STEP_DUR
    max_len = max(len(f) for f in frames)
    key_times = [round(i / (n_frames - 1), 5) for i in range(n_frames)]
    key_times_attr = ";".join(str(t) for t in key_times)

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    )
    parts.append(f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>')
    parts.append(
        f'<rect x="{PAD/2}" y="{PAD/2}" width="{W-PAD}" height="{H-PAD}" rx="10" '
        f'fill="none" stroke="{BORDER}" stroke-width="1.5" opacity="0.6"/>'
    )
    # subtle grid
    for gx in range(COLS + 1):
        x = PAD + gx * CELL
        parts.append(f'<line x1="{x}" y1="{PAD}" x2="{x}" y2="{H-PAD}" stroke="{GRID_LINE}" stroke-width="1"/>')
    for gy in range(ROWS + 1):
        y = PAD + gy * CELL
        parts.append(f'<line x1="{PAD}" y1="{y}" x2="{W-PAD}" y2="{y}" stroke="{GRID_LINE}" stroke-width="1"/>')

    size = CELL - 4

    # snake segments
    for i in range(max_len):
        xs, ys, opac = [], [], []
        for f in frames:
            if i < len(f):
                cx, cy = px(f[i])
                xs.append(f"{cx - size/2:.1f}")
                ys.append(f"{cy - size/2:.1f}")
                opac.append("1")
            else:
                xs.append(xs[-1] if xs else "0")
                ys.append(ys[-1] if ys else "0")
                opac.append("0")
        color = SNAKE_HEAD if i == 0 else SNAKE_BODY
        rx = size / 2 if i == 0 else 4
        parts.append(
            f'<rect x="{xs[0]}" y="{ys[0]}" opacity="{opac[0]}" '
            f'width="{size}" height="{size}" rx="{rx}" fill="{color}">'
            f'<animate attributeName="x" values="{";".join(xs)}" keyTimes="{key_times_attr}" '
            f'dur="{total_dur:.2f}s" begin="{i*STEP_DUR:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
            f'<animate attributeName="y" values="{";".join(ys)}" keyTimes="{key_times_attr}" '
            f'dur="{total_dur:.2f}s" begin="{i*STEP_DUR:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
            f'<animate attributeName="opacity" values="{";".join(opac)}" keyTimes="{key_times_attr}" '
            f'dur="{total_dur:.2f}s" begin="{i*STEP_DUR:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
            f'</rect>'
        )


    food_xs, food_ys, food_op = [], [], []
    for fx, fy, visible in FOOD_TRACK:
        cx, cy = px((fx, fy))
        food_xs.append(f"{cx:.1f}")
        food_ys.append(f"{cy:.1f}")
        food_op.append("1" if visible else "0")

    parts.append(
        f'<circle cx="{food_xs[0]}" cy="{food_ys[0]}" opacity="{food_op[0]}" '
        f'r="{size/3:.1f}" fill="{FOOD}">'
        f'<animate attributeName="cx" values="{";".join(food_xs)}" keyTimes="{key_times_attr}" '
        f'dur="{total_dur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animate attributeName="cy" values="{";".join(food_ys)}" keyTimes="{key_times_attr}" '
        f'dur="{total_dur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animate attributeName="opacity" values="{";".join(food_op)}" keyTimes="{key_times_attr}" '
        f'dur="{total_dur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'</circle>'
    )

    parts.append('</svg>')
    return "".join(parts)


def simulate_with_food_track():
    """Same simulation as simulate(), but also records food position per frame."""
    global FOOD_TRACK
    snake = [(4, ROWS // 2), (3, ROWS // 2), (2, ROWS // 2)]
    food = new_food(set(snake))
    frames = [list(snake)]
    FOOD_TRACK = [(food[0], food[1], True)]

    for _ in range(MAX_STEPS):
        head = snake[0]
        candidates = [(head[0] + 1, head[1]), (head[0] - 1, head[1]),
                      (head[0], head[1] + 1), (head[0], head[1] - 1)]
        body_set = set(snake[:-1])
        safe = [c for c in candidates if in_bounds(c) and c not in body_set]

        if not safe:
            snake = [(4, ROWS // 2), (3, ROWS // 2), (2, ROWS // 2)]
            food = new_food(set(snake))
            frames.append(list(snake))
            FOOD_TRACK.append((food[0], food[1], True))
            continue

        if food:
            safe.sort(key=lambda c: abs(c[0] - food[0]) + abs(c[1] - food[1]))
        new_head = safe[0]
        ate = food is not None and new_head == food
        snake = [new_head] + snake
        if not ate:
            snake.pop()
        else:
            food = new_food(set(snake))

        frames.append(list(snake))
        FOOD_TRACK.append((food[0], food[1], True) if food else (0, 0, False))

    return frames


if __name__ == "__main__":
    frames = simulate_with_food_track()
    svg = build_svg(frames)
    os.makedirs("dist", exist_ok=True)
    with open("dist/snake-game-dark.svg", "w") as f:
        f.write(svg)
    print(f"wrote dist/snake-game-dark.svg — {len(frames)} frames, "
          f"~{len(frames)*STEP_DUR:.1f}s loop")