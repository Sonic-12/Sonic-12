import os
import random

COLS, ROWS = 16, 8
CELL = 15
PAD_X = 14
PAD_TOP = 34          # room for the terminal-style title bar
PAD_BOTTOM = 12
W = COLS * CELL + PAD_X * 2
H = ROWS * CELL + PAD_TOP + PAD_BOTTOM

STEP_DUR = 0.30
MAX_STEPS = 130

BG          = "#1e1e2e"
BAR_BG      = "#181825"
BORDER      = "#313244"
DOT_GRID    = "#313244"
HEAD_COLOR  = "#89b4fa"
HEAD_GLOW   = "#89b4fa"
BODY_FROM   = "#89b4fa"
BODY_TO     = "#45475a"
FOOD_COLOR  = "#f38ba8"
FOOD_GLOW   = "#f38ba8"
TEXT_DIM    = "#6c7086"
TEXT_LABEL  = "#cdd6f4"
DOT_RED     = "#f38ba8"
DOT_YELLOW  = "#f9e2af"
DOT_GREEN   = "#a6e3a1"

random.seed()


def in_bounds(c):
    x, y = c
    return 0 <= x < COLS and 0 <= y < ROWS


def new_food(snake_set):
    free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in snake_set]
    return random.choice(free) if free else None


def px(cell):
    x, y = cell
    return PAD_X + x * CELL + CELL / 2, PAD_TOP + y * CELL + CELL / 2


def simulate():
    """Greedy walk toward food with a random wiggle so the path doesn't look robotic."""
    global FOOD_TRACK
    snake = [(3, ROWS // 2), (2, ROWS // 2), (1, ROWS // 2)]
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
            snake = [(3, ROWS // 2), (2, ROWS // 2), (1, ROWS // 2)]
            food = new_food(set(snake))
            frames.append(list(snake))
            FOOD_TRACK.append((food[0], food[1], True))
            continue

        if food:
            def score(c):
                dist = abs(c[0] - food[0]) + abs(c[1] - food[1])
                return dist + random.random() * 1.4   # small wiggle, less "perfect AI" pathing
            safe.sort(key=score)
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


def build_svg(frames):
    n_frames = len(frames)
    total_dur = n_frames * STEP_DUR
    max_len = max(len(f) for f in frames)
    key_times = [round(i / (n_frames - 1), 5) for i in range(n_frames)]
    key_times_attr = ";".join(str(t) for t in key_times)

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
                  f'width="{W}" height="{H}" font-family="\'SF Mono\',Consolas,monospace">')

    parts.append(f'''<defs>
  <linearGradient id="bodyGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{BODY_FROM}"/>
    <stop offset="100%" stop-color="{BODY_TO}"/>
  </linearGradient>
  <radialGradient id="headGlow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{HEAD_GLOW}" stop-opacity="0.55"/>
    <stop offset="100%" stop-color="{HEAD_GLOW}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="foodGlow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{FOOD_GLOW}" stop-opacity="0.6"/>
    <stop offset="100%" stop-color="{FOOD_GLOW}" stop-opacity="0"/>
  </radialGradient>
</defs>''')

    # card background + border
    parts.append(f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>')
    parts.append(f'<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" rx="9.25" '
                 f'fill="none" stroke="{BORDER}" stroke-width="1"/>')

    # terminal title bar
    parts.append(f'<path d="M0.75,9 A9.25,9.25 0 0 1 10,0.75 H{W-10} '
                 f'A9.25,9.25 0 0 1 {W-0.75},9 V26 H0.75 Z" fill="{BAR_BG}"/>')
    parts.append(f'<line x1="0" y1="26" x2="{W}" y2="26" stroke="{BORDER}" stroke-width="1"/>')
    for i, c in enumerate((DOT_RED, DOT_YELLOW, DOT_GREEN)):
        parts.append(f'<circle cx="{14 + i*11}" cy="13" r="3.2" fill="{c}"/>')
    parts.append(f'<text x="{W/2}" y="17" text-anchor="middle" fill="{TEXT_DIM}" '
                 f'font-size="9.5">snake.py</text>')

    # faint dot grid for texture (not a spreadsheet grid)
    dots = []
    for gy in range(ROWS + 1):
        y = PAD_TOP + gy * CELL
        for gx in range(COLS + 1):
            x = PAD_X + gx * CELL
            dots.append(f'<circle cx="{x}" cy="{y}" r="0.9" fill="{DOT_GRID}"/>')
    parts.append(f'<g opacity="0.55">{"".join(dots)}</g>')

    size = CELL - 5

    # snake body, tail -> head so head renders on top; tapered width + glow on head
    for i in reversed(range(max_len)):
        xs, ys, opac = [], [], []
        for f in frames:
            if i < len(f):
                cx, cy = px(f[i])
                xs.append(f"{cx:.2f}")
                ys.append(f"{cy:.2f}")
                opac.append("1")
            else:
                xs.append(xs[-1] if xs else "0")
                ys.append(ys[-1] if ys else "0")
                opac.append("0")

        is_head = i == 0
        taper = max(0.55, 1 - i * 0.06)
        seg_size = size * (1.0 if is_head else taper)
        rx = seg_size / 2 if is_head else seg_size * 0.32
        fill = HEAD_COLOR if is_head else "url(#bodyGrad)"

        anim_x = (f'<animate attributeName="cx" values="{";".join(xs)}" '
                  f'keyTimes="{key_times_attr}" dur="{total_dur:.2f}s" '
                  f'begin="{i*STEP_DUR:.2f}s" repeatCount="indefinite" calcMode="linear"/>')
        anim_y = (f'<animate attributeName="cy" values="{";".join(ys)}" '
                  f'keyTimes="{key_times_attr}" dur="{total_dur:.2f}s" '
                  f'begin="{i*STEP_DUR:.2f}s" repeatCount="indefinite" calcMode="linear"/>')
        anim_o = (f'<animate attributeName="opacity" values="{";".join(opac)}" '
                  f'keyTimes="{key_times_attr}" dur="{total_dur:.2f}s" '
                  f'begin="{i*STEP_DUR:.2f}s" repeatCount="indefinite" calcMode="discrete"/>')

        if is_head:
            # soft glow behind the head, follows the same path
            parts.append(
                f'<circle cx="{xs[0]}" cy="{ys[0]}" opacity="{opac[0]}" r="{seg_size*1.35:.1f}" '
                f'fill="url(#headGlow)">{anim_x}{anim_y}{anim_o}</circle>'
            )

        parts.append(
            f'<g transform="translate({xs[0]},{ys[0]})" opacity="{opac[0]}">{anim_o}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{";".join(f"{x},{y}" for x, y in zip(xs, ys))}" '
            f'keyTimes="{key_times_attr}" dur="{total_dur:.2f}s" begin="{i*STEP_DUR:.2f}s" '
            f'repeatCount="indefinite" calcMode="linear" additive="replace"/>'
            f'<rect x="{-seg_size/2:.1f}" y="{-seg_size/2:.1f}" width="{seg_size:.1f}" '
            f'height="{seg_size:.1f}" rx="{rx:.1f}" fill="{fill}"/>'
            + ('<circle cx="3.1" cy="-2.6" r="1.15" fill="#1e1e2e"/>'
               '<circle cx="3.1" cy="2.6" r="1.15" fill="#1e1e2e"/>' if is_head else '')
            + '</g>'
        )

    # food: small rotating diamond with a soft pulse + glow
    food_xs, food_ys, food_op = [], [], []
    for fx, fy, visible in FOOD_TRACK:
        cx, cy = px((fx, fy))
        food_xs.append(f"{cx:.2f}")
        food_ys.append(f"{cy:.2f}")
        food_op.append("1" if visible else "0")

    fkey_times_attr = ";".join(str(round(i / (len(FOOD_TRACK) - 1), 5)) for i in range(len(FOOD_TRACK)))
    fdur = len(FOOD_TRACK) * STEP_DUR
    fsize = size * 0.62

    parts.append(
        f'<circle cx="{food_xs[0]}" cy="{food_ys[0]}" opacity="{food_op[0]}" r="{fsize*1.6:.1f}" fill="url(#foodGlow)">'
        f'<animate attributeName="cx" values="{";".join(food_xs)}" keyTimes="{fkey_times_attr}" '
        f'dur="{fdur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animate attributeName="cy" values="{";".join(food_ys)}" keyTimes="{fkey_times_attr}" '
        f'dur="{fdur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animate attributeName="opacity" values="{";".join(food_op)}" keyTimes="{fkey_times_attr}" '
        f'dur="{fdur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'</circle>'
    )
    parts.append(
        f'<g>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{";".join(f"{x},{y}" for x, y in zip(food_xs, food_ys))}" '
        f'keyTimes="{fkey_times_attr}" dur="{fdur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<rect x="{-fsize/2:.1f}" y="{-fsize/2:.1f}" width="{fsize:.1f}" height="{fsize:.1f}" rx="2" '
        f'fill="{FOOD_COLOR}" opacity="{food_op[0]}" transform="rotate(45)">'
        f'<animate attributeName="opacity" values="{";".join(food_op)}" keyTimes="{fkey_times_attr}" '
        f'dur="{fdur:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="0.85;1.05;0.85" dur="1.1s" repeatCount="indefinite" additive="sum"/>'
        f'</rect>'
        f'</g>'
    )

    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    frames = simulate()
    svg = build_svg(frames)
    os.makedirs("dist", exist_ok=True)
    with open("dist/snake-game-dark.svg", "w") as f:
        f.write(svg)
    print(f"wrote dist/snake-game-dark.svg — {len(frames)} frames, "
          f"~{len(frames)*STEP_DUR:.1f}s loop, {W}x{H}px")