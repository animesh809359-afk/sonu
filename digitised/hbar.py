"""Generic digitiser for raster HORIZONTAL grouped bar charts with the value axis on top (Mondal et al. 2021 EJSS Figs 1-3).
- Calibration: tick marks just above the top axis line, equally spaced (first tick = axis minimum).
- Groups: the first bar of each group is solid black (TA); its black rows give the group start; the following bars are delimited by the
  dark border rows (horizontal outlines) below it.
- Bar end: the first column (scanning right from the y axis) that is inked over > 90 % of the bar height AND whose columns x+2..x+5
  carrying ink only in the central 70 % of the bar height (error-bar line / caps) or none - i.e. the bar's own right outline, before the error bar, its cap,
  the significance letters and any legend box further right.
"""
import numpy as np


def ticks(g, axis_row, x0, x1):
    ink = g < 160
    cols = [x for x in range(x0, x1) if ink[axis_row - 9:axis_row - 2, x].sum() >= 4]
    out = []
    for x in cols:
        if out and x - out[-1][-1] <= 2:
            out[-1].append(x)
        else:
            out.append([x])
    return [sum(c) / len(c) for c in out]


def clusters(rows, gap=2):
    out = []
    for y in rows:
        if out and y - out[-1][-1] <= gap:
            out[-1].append(y)
        else:
            out.append([y])
    return out


def groups(g, axis_col, y0, y1, nbars=4, width=56):
    ink = g < 200
    full = [y for y in range(y0, y1) if ink[y, axis_col + 3:axis_col + 3 + width].mean() > 0.9]
    cl = clusters(full)
    res, i = [], 0
    while i < len(cl):
        c = cl[i]
        if len(c) >= 12:                                  # solid black TA bar
            edges = [c[0], c[-1]]
            j = i + 1
            while len(edges) < nbars + 1 and j < len(cl) and len(cl[j]) < 12:
                edges.append(sum(cl[j]) / len(cl[j]))
                j += 1
            res.append(edges)
            i = j
        else:
            i += 1
    return res


def right_end(g, top, bot, axis_col, maxgap=15):
    """first full-height column (outline) after which columns x+2..x+5 carry ink only in the central 70 % of the bar height
    (error-bar line and caps) or none - hatch / dot patterns and the next bar's outline reach the top and bottom rows"""
    ink = g < 235
    t, b = int(top) + 4, int(bot) - 4   # skip the outline rows shared with the neighbouring bars
    lo, hi = t + 0.15 * (b - t), b - 0.15 * (b - t)
    for x in range(axis_col + 8, g.shape[1] - 5):
        if ink[t:b, x].mean() <= 0.9:
            continue
        ok = True
        for xx in range(x + 2, x + 6):   # skip one anti-aliased column after the outline
            rows = np.nonzero(ink[t:b, xx])[0] + t
            if len(rows) and (rows.min() < lo or rows.max() > hi or len(rows) > 0.75 * (b - t)):
                ok = False
                break
        if ok:
            return x
    return None


def read(g, axis_row, axis_col, vmin, step, y0, y1, nbars=4, x1=None, nticks=None):
    tk = ticks(g, axis_row, axis_col - 5, x1 or g.shape[1])[:nticks]
    px = np.mean(np.diff(tk))
    out = []
    for edges in groups(g, axis_col, y0, y1, nbars):
        vals = []
        for k in range(len(edges) - 1):
            e = right_end(g, edges[k], edges[k + 1], axis_col)
            vals.append(None if e is None else round(vmin + (e - tk[0]) / px * step, 3))
        out.append(vals)
    return tk, out


def overlay(g, ends, path):
    """save an RGB copy with each detected bar end marked by a red vertical tick (for visual checking)"""
    from PIL import Image
    rgb = np.stack([g, g, g], -1).astype(np.uint8)
    for (top, bot, x) in ends:
        if x is not None:
            rgb[int(top):int(bot), max(0, x - 1):x + 2] = (255, 0, 0)
    Image.fromarray(rgb).save(path)
