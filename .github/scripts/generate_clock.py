import math
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
now = datetime.now(IST)

hour = now.hour % 12
minute = now.minute
second = now.second

hour_angle = (hour + minute / 60) * 30
minute_angle = (minute + second / 60) * 6
second_angle = second * 6

cx, cy, r = 100, 100, 78


def hand_end(angle_deg, length):
    angle_rad = math.radians(angle_deg - 90)
    x = cx + length * math.cos(angle_rad)
    y = cy + length * math.sin(angle_rad)
    return x, y


hx, hy = hand_end(hour_angle, 40)
mx, my = hand_end(minute_angle, 58)
sx, sy = hand_end(second_angle, 66)

ticks = []
for i in range(12):
    angle = math.radians(i * 30 - 90)
    x1 = cx + (r - 8) * math.cos(angle)
    y1 = cy + (r - 8) * math.sin(angle)
    x2 = cx + r * math.cos(angle)
    y2 = cy + r * math.sin(angle)
    ticks.append(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="#7aa2f7" stroke-width="2.5" stroke-linecap="round"/>'
    )

date_str = now.strftime("%d %b %Y")
time_str = now.strftime("%I:%M %p")

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 235" width="200" height="235">
<rect width="200" height="235" fill="#1a1b27" rx="14"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="#16161e" stroke="#7aa2f7" stroke-width="3"/>
{''.join(ticks)}
<line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="#c0caf5" stroke-width="5" stroke-linecap="round"/>
<line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" stroke="#c0caf5" stroke-width="3.5" stroke-linecap="round"/>
<line x1="{cx}" y1="{cy}" x2="{sx:.1f}" y2="{sy:.1f}" stroke="#f7768e" stroke-width="1.5" stroke-linecap="round"/>
<circle cx="{cx}" cy="{cy}" r="4" fill="#f7768e"/>
<text x="100" y="205" text-anchor="middle" fill="#c0caf5" font-family="monospace" font-size="13">{time_str} IST</text>
<text x="100" y="222" text-anchor="middle" fill="#7aa2f7" font-family="monospace" font-size="11">{date_str}</text>
</svg>'''

with open("dist/clock.svg", "w") as f:
    f.write(svg)

print(time_str, date_str)