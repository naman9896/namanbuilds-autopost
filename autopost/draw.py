"""Low-level drawing helpers (cairo) shared by all scenes."""
import math
import cairo

W, H, FPS = 1080, 1920, 30
FONT = "Poppins"


def hx(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255, a)


NAVY = hx('0F1226'); PURPLE = hx('6C5CE7'); CYAN = hx('00D2FF')
GREEN = hx('2ECC71'); CORAL = hx('FF6B6B'); WHITE = hx('FFFFFF')
CARD = hx('1B2045'); CARD2 = hx('252B5A'); MUTED = hx('8A90C0'); YELLOW = hx('FDCB6E')


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else (1.0 if t >= b else 0.0)
def eo(x): return 1 - (1 - x) ** 3
def eio(x): return 4*x*x*x if x < 0.5 else 1 - (-2*x + 2) ** 3 / 2
def back(x, s=1.70158):
    x = x - 1
    return x*x*((s+1)*x + s) + 1
def lerp(a, b, x): return a + (b - a) * x


def col(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], c[3]*a)


def rrect(ctx, x, y, w, h, r):
    r = min(r, w/2, h/2)
    ctx.new_sub_path()
    ctx.arc(x+w-r, y+r, r, -math.pi/2, 0)
    ctx.arc(x+w-r, y+h-r, r, 0, math.pi/2)
    ctx.arc(x+r, y+h-r, r, math.pi/2, math.pi)
    ctx.arc(x+r, y+r, r, math.pi, 3*math.pi/2)
    ctx.close_path()


def font(ctx, size, bold=True):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text_w(ctx, s, size, bold=True):
    font(ctx, size, bold)
    return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size, c, a=1.0, anchor="c", scale=1.0, bold=True, source=None):
    """Draw text; y is the visual centre line of capital letters."""
    if a <= 0.001 or scale <= 0.001: return
    ctx.save()
    font(ctx, size, bold)
    e = ctx.text_extents(s)
    ctx.translate(x, y); ctx.scale(scale, scale)
    dx = -e.x_advance/2 if anchor == "c" else (0 if anchor == "l" else -e.x_advance)
    ctx.new_path(); ctx.move_to(dx, size*0.36)
    if source is not None:
        ctx.text_path(s)
        ctx.set_source(source(dx, e.x_advance))
        ctx.clip_preserve(); ctx.paint_with_alpha(a); ctx.new_path()
    else:
        col(ctx, c, a); ctx.show_text(s)
    ctx.restore()


def glow(ctx, x, y, r, c, a=1.0):
    if a <= 0.001 or r <= 1: return
    g = cairo.RadialGradient(x, y, r*0.3, x, y, r)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], 0.55*a)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.new_path(); ctx.set_source(g); ctx.arc(x, y, r, 0, 2*math.pi); ctx.fill()


def ring(ctx, x, y, r, c, a, lw=6):
    if a <= 0.001: return
    ctx.new_path(); col(ctx, c, a); ctx.set_line_width(lw)
    ctx.arc(x, y, r, 0, 2*math.pi); ctx.stroke(); ctx.new_path()


def check_badge(ctx, x, y, r, a=1.0, s=1.0):
    if a <= 0.001 or s <= 0.001: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    glow(ctx, 0, 0, r*2.4, GREEN, a)
    col(ctx, GREEN, a); ctx.arc(0, 0, r, 0, 2*math.pi); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, a); ctx.set_line_width(r*0.22)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(-r*0.42, 0.02*r); ctx.line_to(-r*0.1, r*0.34); ctx.line_to(r*0.45, -r*0.32); ctx.stroke()
    ctx.restore()


def cross_badge(ctx, x, y, r, s=1.0):
    if s <= 0.001: return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    glow(ctx, 0, 0, r*2.3, CORAL, 1); col(ctx, CORAL); ctx.arc(0, 0, r, 0, 2*math.pi); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 1); ctx.set_line_width(r*0.23); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    k = r*0.35
    ctx.move_to(-k, -k); ctx.line_to(k, k); ctx.move_to(k, -k); ctx.line_to(-k, k); ctx.stroke()
    ctx.restore()


def background(ctx, t_global):
    col(ctx, NAVY); ctx.paint()
    ctx.set_line_width(1.5)
    off = (t_global * 8) % 60
    ctx.set_source_rgba(1, 1, 1, 0.045)
    for x in range(0, W + 60, 60):
        ctx.move_to(x, 0); ctx.line_to(x, H)
    for y in range(-60, H + 60, 60):
        ctx.move_to(0, y + off); ctx.line_to(W, y + off)
    ctx.stroke()
    g = cairo.RadialGradient(W/2, H*0.45, 200, W/2, H*0.45, 1250)
    g.add_color_stop_rgba(0, 0.42, 0.36, 0.91, 0.10)
    g.add_color_stop_rgba(0.5, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    ctx.set_source(g); ctx.paint()


def cloud_path(ctx, cx, cy, s):
    ctx.new_path()
    for (dx, dy, r) in [(-150, 30, 95), (-50, -40, 125), (85, -15, 110), (165, 45, 80)]:
        ctx.new_sub_path(); ctx.arc(cx + dx*s, cy + dy*s, r*s, 0, 2*math.pi)
    rrect(ctx, cx - 240*s, cy + 20*s, 480*s, 110*s, 55*s)


def wrap(ctx, s, size, maxw):
    words = s.split(); lines = []; cur = ""
    for w_ in words:
        tryl = (cur + " " + w_).strip()
        if text_w(ctx, tryl, size) <= maxw or not cur: cur = tryl
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines


def caption(ctx, s, t, D, lead=0.2):
    a = prog(t, lead - 0.05, lead + 0.15) * (1 - prog(t, D - 0.12, D))
    if a <= 0.001 or not s: return
    size = 44; lh = 62
    lines = wrap(ctx, s, size, 880)
    total = lh*len(lines); y0 = 1735 - total/2
    maxw = max(text_w(ctx, l, size) for l in lines)
    ctx.set_source_rgba(0, 0, 0, 0.45*a)
    rrect(ctx, W/2 - maxw/2 - 34, y0 - 18, maxw + 68, total + 36, 22); ctx.fill()
    for i, l in enumerate(lines):
        text(ctx, l, W/2, y0 + lh/2 + i*lh, size, WHITE, a)


def scene_fade(ctx, t, D):
    f = max(1 - prog(t, 0, 0.12), prog(t, D - 0.12, D))
    if f > 0:
        col(ctx, NAVY, f); ctx.paint()


def grad_src(c1, c2):
    def mk(dx, w):
        g = cairo.LinearGradient(dx, 0, dx + w, 0)
        g.add_color_stop_rgba(0, *c1[:3], 1); g.add_color_stop_rgba(1, *c2[:3], 1)
        return g
    return mk
