import math


def _scale_x(val: float, x_min: float, x_max: float, plot_left: float, plot_width: float) -> float:
    if x_max == x_min:
        return plot_left + plot_width / 2.0
    ratio = (val - x_min) / (x_max - x_min)
    return plot_left + ratio * plot_width


def _square_size_from_weight(weight: float, max_weight: float, min_pixels: float = 4.0, max_pixels: float = 22.0) -> float:
    if max_weight <= 0:
        return (min_pixels + max_pixels) / 2.0
    r = weight / max_weight
    r = max(0.0, min(1.0, r))
    area_min = min_pixels * min_pixels
    area_max = max_pixels * max_pixels
    area = area_min + r * (area_max - area_min)
    return math.sqrt(area)


def forest_svg_bytes(studies: list[dict], pooled: dict, heterogeneity: dict, *, title: str = "Forest Plot") -> bytes:
    n = len(studies)
    row_h = 36.0
    top_pad = 60.0
    bottom_pad = 80.0
    left_pad = 180.0
    right_pad = 160.0
    plot_left = left_pad + 10.0
    plot_width = 520.0

    all_effects = []
    all_ci = []
    for s in studies:
        all_effects.append(s["effect"])
        all_ci.append(s["ci_low"])
        all_ci.append(s["ci_high"])
    all_effects.append(pooled["effect"])
    all_ci.append(pooled["ci_low"])
    all_ci.append(pooled["ci_high"])

    x_min_data = min(all_ci)
    x_max_data = max(all_ci)
    x_min = x_min_data - 0.1 * abs(x_min_data) - 0.05
    x_max = x_max_data + 0.1 * abs(x_max_data) + 0.05
    if x_min > 0.0 and 1.0 < x_max:
        x_min = min(x_min, 0.5)
    if x_max < 1.0:
        x_max = max(x_max, 1.5)

    mid_line = 1.0

    height = top_pad + (n + 2) * row_h + bottom_pad
    width = left_pad + plot_width + right_pad

    svg_parts: list[str] = []
    vb = f"0 0 {width:.1f} {height:.1f}"
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{width:.1f}" height="{height:.1f}">')

    svg_parts.append('<style>')
    svg_parts.append('text { font-family: Arial, Helvetica, sans-serif; fill: #222; }')
    svg_parts.append('.title { font-size: 18px; font-weight: bold; }')
    svg_parts.append('.label { font-size: 13px; }')
    svg_parts.append('.axis { font-size: 11px; fill: #555; }')
    svg_parts.append('.study-line { stroke: #333; stroke-width: 1.2; }')
    svg_parts.append('.ci-line { stroke: #2563eb; stroke-width: 1.8; }')
    svg_parts.append('.zero-line { stroke: #999; stroke-width: 1; stroke-dasharray: 4 3; }')
    svg_parts.append('.pooled-line { stroke: #111827; stroke-width: 1.4; stroke-dasharray: 2 2; }')
    svg_parts.append('</style>')

    svg_parts.append(f'<text x="{width/2:.1f}" y="30" text-anchor="middle" class="title">{title}</text>')

    zero_x = _scale_x(mid_line, x_min, x_max, plot_left, plot_width)
    y_top = top_pad
    y_bottom = top_pad + (n + 1) * row_h
    svg_parts.append(f'<line x1="{zero_x:.2f}" y1="{y_top:.2f}" x2="{zero_x:.2f}" y2="{y_bottom:.2f}" class="zero-line" />')

    max_weight = 0.0
    for s in studies:
        if s.get("weight", 0.0) > max_weight:
            max_weight = s["weight"]

    for i, s in enumerate(studies):
        yc = top_pad + i * row_h + row_h / 2.0
        label = s.get("label", f"Study {i+1}")
        svg_parts.append(f'<text x="{left_pad - 8:.1f}" y="{yc + 4:.1f}" text-anchor="end" class="label">{label}</text>')

        effect = s["effect"]
        ci_low = s["ci_low"]
        ci_high = s["ci_high"]
        weight = s.get("weight", 0.0)

        ex = _scale_x(effect, x_min, x_max, plot_left, plot_width)
        lx = _scale_x(ci_low, x_min, x_max, plot_left, plot_width)
        rx = _scale_x(ci_high, x_min, x_max, plot_left, plot_width)

        svg_parts.append(f'<line x1="{lx:.2f}" y1="{yc:.2f}" x2="{rx:.2f}" y2="{yc:.2f}" class="ci-line" />')
        tick_h = 5.0
        svg_parts.append(f'<line x1="{lx:.2f}" y1="{yc - tick_h:.2f}" x2="{lx:.2f}" y2="{yc + tick_h:.2f}" class="study-line" />')
        svg_parts.append(f'<line x1="{rx:.2f}" y1="{yc - tick_h:.2f}" x2="{rx:.2f}" y2="{yc + tick_h:.2f}" class="study-line" />')

        sq = _square_size_from_weight(weight, max_weight)
        svg_parts.append(f'<rect x="{ex - sq/2:.2f}" y="{yc - sq/2:.2f}" width="{sq:.2f}" height="{sq:.2f}" fill="#1e40af" stroke="#0f172a" />')

    pooled_y = top_pad + (n + 0.5) * row_h
    svg_parts.append(f'<line x1="{plot_left:.2f}" y1="{pooled_y - 6:.2f}" x2="{plot_left + plot_width:.2f}" y2="{pooled_y - 6:.2f}" class="pooled-line" />')
    svg_parts.append(f'<text x="{left_pad - 8:.1f}" y="{pooled_y + 4:.1f}" text-anchor="end" class="label" font-weight="bold">Pooled</text>')

    pe = pooled["effect"]
    p_low = pooled["ci_low"]
    p_high = pooled["ci_high"]
    cx = _scale_x(pe, x_min, x_max, plot_left, plot_width)
    lx_p = _scale_x(p_low, x_min, x_max, plot_left, plot_width)
    rx_p = _scale_x(p_high, x_min, x_max, plot_left, plot_width)
    half_h = 10.0
    half_w = max(2.0, abs(rx_p - cx))
    half_w_left = max(2.0, abs(cx - lx_p))
    p1 = f"{cx:.2f},{pooled_y - half_h:.2f}"
    p2 = f"{cx + half_w:.2f},{pooled_y:.2f}"
    p3 = f"{cx:.2f},{pooled_y + half_h:.2f}"
    p4 = f"{cx - half_w_left:.2f},{pooled_y:.2f}"
    svg_parts.append(f'<polygon id="diamond-pooled" points="{p1} {p2} {p3} {p4}" fill="#15803d" stroke="#052e16" stroke-width="1.2" />')

    axis_y = top_pad + (n + 1.7) * row_h
    svg_parts.append(f'<line x1="{plot_left:.2f}" y1="{axis_y:.2f}" x2="{plot_left + plot_width:.2f}" y2="{axis_y:.2f}" stroke="#555" stroke-width="1" />')
    nticks = 5
    for i in range(nticks + 1):
        t = i / nticks
        v = x_min + t * (x_max - x_min)
        tx = _scale_x(v, x_min, x_max, plot_left, plot_width)
        svg_parts.append(f'<line x1="{tx:.2f}" y1="{axis_y - 3:.2f}" x2="{tx:.2f}" y2="{axis_y + 3:.2f}" stroke="#555" stroke-width="1" />')
        svg_parts.append(f'<text x="{tx:.1f}" y="{axis_y + 16:.1f}" text-anchor="middle" class="axis">{v:.2f}</text>')
    svg_parts.append(f'<text x="{plot_left + plot_width/2:.1f}" y="{axis_y + 36:.1f}" text-anchor="middle" class="axis" font-size="12">Effect size (OR / RR)</text>')

    i2_pct = heterogeneity.get("I2_pct", None)
    if i2_pct is not None:
        i2_text = f"I² = {i2_pct:.1f}%"
        svg_parts.append(f'<text x="{plot_left + plot_width:.1f}" y="32" text-anchor="end" class="label" font-weight="bold" fill="#92400e">{i2_text}</text>')

    svg_parts.append('</svg>')
    svg_str = "".join(svg_parts)
    return svg_str.encode("utf-8")
