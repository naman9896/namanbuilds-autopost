"""'Tech in 30 Seconds' explainer template.

A video is a JSON spec: a list of scenes, each with a voiceover line ("vo") and
scene-type parameters. Visual beats are tied to words in the voiceover ("cue"),
so one spec drives animation, captions, voice and sound effects.
"""
import json, math, os, subprocess, sys
from multiprocessing import Pool
import numpy as np
import cairo

from .draw import (W, H, FPS, PURPLE, CYAN, GREEN, CORAL, WHITE, NAVY, CARD, CARD2, MUTED, YELLOW,
                   hx, clamp, prog, eo, eio, back, lerp, col, rrect, text, text_w, glow, ring,
                   check_badge, cross_badge, background, grad_src, wrap, cloud_path, caption, scene_fade)
from . import sfx

COLORS = dict(purple=PURPLE, cyan=CYAN, green=GREEN, coral=CORAL, white=WHITE, muted=MUTED)
ICONS = ["browser", "server", "dns", "database", "lock", "unlock", "postcard", "envelope", "phone", "waiter",
         "hacker", "globe", "key", "card", "sun", "cloud", "laptop", "code", "user"]
VO_LEAD = 0.2
MODEL_DIR = os.environ.get("MODEL_DIR", os.path.expanduser("~/models"))


# ------------------------------------------------------------------ icons
def icon(ctx, kind, cx, cy, size, c, a=1.0):
    if a <= 0.001: return
    s = size / 2
    ctx.save(); ctx.translate(cx, cy); ctx.new_path()
    lw = max(3, size * 0.05)
    ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    def stroke(): ctx.set_source_rgba(1, 1, 1, a); ctx.stroke()
    def fill(cc=c, al=1.0): col(ctx, cc, a * al); ctx.fill()
    if kind == "browser":
        rrect(ctx, -0.85*s, -0.65*s, 1.7*s, 1.3*s, 0.14*s); stroke()
        ctx.move_to(-0.85*s, -0.32*s); ctx.line_to(0.85*s, -0.32*s); stroke()
        for k, cc in enumerate([CORAL, YELLOW, GREEN]):
            ctx.arc(-0.65*s + k*0.17*s, -0.49*s, 0.055*s, 0, 2*math.pi); fill(cc)
        rrect(ctx, -0.12*s, -0.57*s, 0.85*s, 0.16*s, 0.08*s); fill(c, 0.9)
        for k, w_ in enumerate([1.1, 0.8, 0.95]):
            rrect(ctx, -0.65*s, (-0.08 + k*0.22)*s, w_*s, 0.09*s, 0.045*s); fill(WHITE, 0.55)
    elif kind == "server":
        for k in range(3):
            y = (-0.78 + k*0.54)*s
            rrect(ctx, -0.72*s, y, 1.44*s, 0.42*s, 0.1*s); stroke()
            ctx.arc(0.45*s, y + 0.21*s, 0.07*s, 0, 2*math.pi); fill(c)
            ctx.arc(0.25*s, y + 0.21*s, 0.07*s, 0, 2*math.pi); fill(GREEN)
            ctx.move_to(-0.5*s, y + 0.21*s); ctx.line_to(-0.05*s, y + 0.21*s); stroke()
    elif kind == "dns":
        rrect(ctx, -0.6*s, -0.82*s, 1.2*s, 1.64*s, 0.12*s); stroke()
        for k, yy in enumerate([-0.5, 0, 0.5]):
            ctx.arc(-0.6*s, yy*s, 0.1*s, 0, 2*math.pi); fill(WHITE)
            rrect(ctx, 0.6*s, (yy - 0.12)*s, 0.18*s, 0.24*s, 0.05*s); fill([CORAL, CYAN, GREEN][k])
        text(ctx, "A-Z", 0, -0.35*s, 0.38*s, c, a)
        for k in range(3):
            rrect(ctx, -0.32*s, (0.05 + k*0.22)*s, 0.68*s, 0.08*s, 0.04*s); fill(WHITE, 0.55)
    elif kind == "database":
        rx, ry = 0.65*s, 0.2*s
        for yy in (-0.55, 0.0, 0.55):
            ctx.save(); ctx.translate(0, yy*s); ctx.scale(rx, ry)
            ctx.arc(0, 0, 1, 0, 2*math.pi) if yy == -0.55 else ctx.arc(0, 0, 1, 0, math.pi)
            ctx.restore(); stroke()
        ctx.move_to(-rx, -0.55*s); ctx.line_to(-rx, 0.55*s); stroke()
        ctx.move_to(rx, -0.55*s); ctx.line_to(rx, 0.55*s); stroke()
        ctx.save(); ctx.translate(0, -0.55*s); ctx.scale(rx*0.6, ry*0.6); ctx.arc(0, 0, 1, 0, 2*math.pi); ctx.restore(); fill(c)
    elif kind in ("lock", "unlock"):
        if kind == "lock":
            ctx.arc(0, -0.25*s, 0.38*s, math.pi, 0); ctx.line_to(0.38*s, 0); ctx.move_to(-0.38*s, 0); ctx.line_to(-0.38*s, -0.25*s)
        else:
            ctx.arc(0.3*s, -0.42*s, 0.38*s, math.pi, 0); ctx.move_to(-0.08*s, -0.42*s); ctx.line_to(-0.08*s, 0)
        stroke()
        rrect(ctx, -0.62*s, -0.05*s, 1.24*s, 0.88*s, 0.14*s); fill(c)
        ctx.arc(0, 0.3*s, 0.12*s, 0, 2*math.pi); fill(NAVY)
        rrect(ctx, -0.05*s, 0.32*s, 0.1*s, 0.25*s, 0.04*s); fill(NAVY)
    elif kind == "postcard":
        rrect(ctx, -0.88*s, -0.58*s, 1.76*s, 1.16*s, 0.1*s); stroke()
        ctx.move_to(0.05*s, -0.4*s); ctx.line_to(0.05*s, 0.4*s); stroke()
        rrect(ctx, 0.45*s, -0.42*s, 0.28*s, 0.34*s, 0.04*s); fill(c)
        for k in range(3):
            yy = (-0.25 + k*0.25)*s
            ctx.move_to(-0.7*s, yy)
            for j in range(4):
                ctx.curve_to(-0.62*s + j*0.17*s, yy - 0.08*s, -0.56*s + j*0.17*s, yy + 0.08*s, -0.53*s + j*0.17*s, yy)
            ctx.set_source_rgba(1, 1, 1, 0.7*a); ctx.stroke()
        for k in range(2):
            ctx.move_to(0.22*s, (0.12 + k*0.18)*s); ctx.line_to(0.72*s, (0.12 + k*0.18)*s); stroke()
    elif kind == "envelope":
        rrect(ctx, -0.88*s, -0.58*s, 1.76*s, 1.16*s, 0.1*s); stroke()
        ctx.move_to(-0.86*s, -0.52*s); ctx.line_to(0, 0.08*s); ctx.line_to(0.86*s, -0.52*s); stroke()
        ctx.arc(0, 0.08*s, 0.2*s, 0, 2*math.pi); fill(c)
    elif kind == "phone":
        rrect(ctx, -0.46*s, -0.88*s, 0.92*s, 1.76*s, 0.18*s); stroke()
        ctx.move_to(-0.12*s, -0.72*s); ctx.line_to(0.12*s, -0.72*s); stroke()
        pal = [PURPLE, CYAN, GREEN, CORAL, YELLOW, PURPLE, CYAN, GREEN, CORAL]
        for i in range(3):
            for j in range(3):
                rrect(ctx, (-0.3 + j*0.22)*s, (-0.5 + i*0.25)*s, 0.16*s, 0.16*s, 0.04*s); fill(pal[i*3 + j])
    elif kind == "waiter":
        ctx.move_to(-0.88*s, 0.42*s); ctx.line_to(0.88*s, 0.42*s); stroke()
        ctx.arc(0, 0.35*s, 0.7*s, math.pi, 2*math.pi); ctx.close_path(); fill(c)
        ctx.arc(0, -0.42*s, 0.1*s, 0, 2*math.pi); fill(WHITE)
    elif kind == "hacker":
        ctx.move_to(-0.9*s, 0)
        ctx.curve_to(-0.45*s, -0.6*s, 0.45*s, -0.6*s, 0.9*s, 0)
        ctx.curve_to(0.45*s, 0.6*s, -0.45*s, 0.6*s, -0.9*s, 0); ctx.close_path(); stroke()
        ctx.arc(0, 0, 0.3*s, 0, 2*math.pi); fill(c)
        ctx.arc(0, 0, 0.12*s, 0, 2*math.pi); fill(NAVY)
        ctx.arc(0.1*s, -0.1*s, 0.05*s, 0, 2*math.pi); fill(WHITE)
    elif kind == "globe":
        ctx.arc(0, 0, 0.82*s, 0, 2*math.pi); stroke()
        ctx.save(); ctx.scale(0.42, 1); ctx.arc(0, 0, 0.82*s, 0, 2*math.pi); ctx.restore(); stroke()
        ctx.move_to(-0.82*s, 0); ctx.line_to(0.82*s, 0); stroke()
        for yy in (-0.42, 0.42):
            hw = math.sqrt(0.82**2 - yy**2)
            ctx.move_to(-hw*s, yy*s); ctx.line_to(hw*s, yy*s); stroke()
    elif kind == "key":
        ctx.arc(-0.45*s, 0, 0.32*s, 0, 2*math.pi); stroke()
        ctx.arc(-0.45*s, 0, 0.12*s, 0, 2*math.pi); fill(c)
        ctx.move_to(-0.13*s, 0); ctx.line_to(0.85*s, 0); stroke()
        ctx.move_to(0.55*s, 0); ctx.line_to(0.55*s, 0.25*s); ctx.move_to(0.75*s, 0); ctx.line_to(0.75*s, 0.3*s); stroke()
    elif kind == "card":
        rrect(ctx, -0.88*s, -0.58*s, 1.76*s, 1.16*s, 0.12*s); stroke()
        ctx.rectangle(-0.86*s, -0.36*s, 1.72*s, 0.22*s); fill(c)
        rrect(ctx, -0.65*s, 0.05*s, 0.32*s, 0.24*s, 0.05*s); fill(YELLOW)
        rrect(ctx, 0.1*s, 0.3*s, 0.6*s, 0.09*s, 0.04*s); fill(WHITE, 0.6)
    elif kind == "sun":
        ctx.arc(0, 0, 0.38*s, 0, 2*math.pi); fill(YELLOW)
        for k in range(8):
            ang = k*math.pi/4
            ctx.move_to(math.cos(ang)*0.55*s, math.sin(ang)*0.55*s); ctx.line_to(math.cos(ang)*0.8*s, math.sin(ang)*0.8*s)
        stroke()
    elif kind == "cloud":
        sc = size/640
        cloud_path(ctx, 0, -40*sc, sc); stroke()
    elif kind == "laptop":
        rrect(ctx, -0.72*s, -0.62*s, 1.44*s, 0.95*s, 0.1*s); stroke()
        ctx.move_to(-0.9*s, 0.5*s); ctx.line_to(0.9*s, 0.5*s); stroke()
        for k, w_ in enumerate([0.7, 0.5, 0.85]):
            rrect(ctx, -0.5*s, (-0.42 + k*0.22)*s, w_*s, 0.08*s, 0.04*s); fill([c, WHITE, WHITE][k], 0.8)
    elif kind == "code":
        text(ctx, "</>", 0, 0, 0.95*s, c, a)
    elif kind == "user":
        ctx.arc(0, -0.35*s, 0.3*s, 0, 2*math.pi); stroke()
        ctx.arc(0, 0.75*s, 0.65*s, math.pi, 2*math.pi); stroke()
    else:
        raise ValueError("unknown icon " + kind)
    ctx.new_path(); ctx.restore()


def tile(ctx, kind, cx, cy, size, c, a=1.0, scale=1.0, label=None, label_size=34, pulse=0.0):
    if a <= 0.001 or scale <= 0.001: return
    ctx.save(); ctx.translate(cx, cy); ctx.scale(scale, scale)
    glow(ctx, 0, 0, size*1.05, c, a*(0.7 + 0.6*pulse))
    col(ctx, CARD2, a); rrect(ctx, -size/2, -size/2, size, size, size*0.22); ctx.fill()
    col(ctx, c, a); ctx.set_line_width(6); rrect(ctx, -size/2, -size/2, size, size, size*0.22); ctx.stroke()
    icon(ctx, kind, 0, 0, size*0.62, c, a)
    ctx.restore()
    if label:
        for i, l in enumerate(wrap(ctx, label, label_size, 320)):
            text(ctx, l, cx, cy + size*scale/2 + 42 + i*label_size*1.25, label_size, WHITE, a*0.95)


def fit_text(ctx, s, x, y, size, c, a=1.0, maxw=960, **kw):
    w_ = text_w(ctx, s, size)
    if w_ > maxw: size = size * maxw / w_
    text(ctx, s, x, y, size, c, a, **kw)


def pill(ctx, s, x, y, c, a=1.0, size=38, sc=1.0):
    if a <= 0.001 or sc <= 0.001: return
    w_ = text_w(ctx, s, size) + 56; h_ = size*1.7
    ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc)
    glow(ctx, 0, 0, w_*0.7, c, 0.6*a)
    col(ctx, c, a); rrect(ctx, -w_/2, -h_/2, w_, h_, h_/2); ctx.fill()
    text(ctx, s, 0, 0, size, hx('0B0E22'), a)
    ctx.restore()


def header(ctx, t, word, sub, c, gradient=None, y=300):
    p = prog(t, 0.05, 0.45)
    if p <= 0: return
    x = lerp(-300, W/2, back(p)) if p < 1 else W/2
    src = grad_src(COLORS[gradient[0]], COLORS[gradient[1]]) if gradient else None
    fit_text(ctx, word, x, y, 140, c, clamp(p*2), source=src)
    if sub:
        p2 = prog(t, 0.3, 0.7)
        fit_text(ctx, sub, W/2, y + 108, 56, WHITE, eo(p2), scale=lerp(0.9, 1, eo(p2)))


# ------------------------------------------------------------------ scenes
class Scene:
    tail_default = 0.45

    def __init__(self, spec, vo_dur):
        self.spec = spec; self.vo = spec.get("vo", ""); self.vo_dur = vo_dur
        self.tail = spec.get("tail", self.tail_default)
        self.D = self._q(VO_LEAD + vo_dur + self.tail)
        self.ev = []

    @staticmethod
    def _q(x): return round(x * FPS) / FPS

    def cue(self, word, off=0.0):
        if isinstance(word, (int, float)): return float(word)
        i = self.vo.lower().find(str(word).lower())
        if i < 0: raise ValueError(f"cue '{word}' is not in the voiceover line: {self.vo}")
        return VO_LEAD + self.vo_dur * i / max(1, len(self.vo)) + off

    def sfx(self, t, kind, gain=1.0): self.ev.append((t, kind, gain))
    def caption(self): return self.vo


class Hook(Scene):
    tail_default = 0.35

    def __init__(self, spec, d):
        super().__init__(spec, d)
        self.swap = self.cue(spec["swap_cue"], -0.05)
        self.c1 = COLORS[spec.get("accent_a", "coral")]; self.c2 = COLORS[spec.get("accent_b", "cyan")]
        self.sfx(0.05, "pop", 0.5); self.sfx(0.32, "whoosh", 0.5); self.sfx(0.52, "thud", 0.7)
        self.sfx(self.swap - 0.1, "whoosh", 0.5); self.sfx(self.swap + 0.12, "thud", 0.45)

    def draw(self, ctx, t):
        s = self.spec
        sh = prog(t, 0.5, 0.85)
        if 0 < sh < 1:
            amp = 18*(1 - sh); ctx.translate(math.sin(t*90)*amp, math.cos(t*77)*amp)
        pop = back(prog(t, 0.0, 0.4))
        ic_c = self.c1 if t < self.swap else self.c2
        tile(ctx, s["icon"], W/2, 1180 + math.sin(t*3)*8, 300, ic_c, 1, pop, pulse=0.5 + 0.5*math.sin(t*5))
        p1 = prog(t, 0.35, 0.6); o1 = prog(t, self.swap - 0.1, self.swap + 0.05)
        if p1 > 0 and o1 < 1:
            sc = lerp(1.9, 1.0, eo(p1))*lerp(1, 0.6, o1); a = p1*(1 - o1)
            fit_text(ctx, s["a"][0], W/2, 650, 110, WHITE, a, scale=sc)
            fit_text(ctx, s["a"][1], W/2, 800, 150, self.c1, a, scale=sc)
        p2 = prog(t, self.swap, self.swap + 0.3)
        if p2 > 0:
            sc = back(p2); a = clamp(p2*2)
            fit_text(ctx, s["b"][0], W/2, 650, 110, WHITE, a, scale=sc)
            fit_text(ctx, s["b"][1], W/2, 800, 150, self.c2, a, scale=sc, source=grad_src(self.c2, PURPLE))


class Flow(Scene):
    """Icon tiles appear on cue; labelled packets travel between them."""
    def __init__(self, spec, d):
        super().__init__(spec, d)
        n = len(spec["nodes"])
        default = {2: [(250, 960), (830, 960)], 3: [(175, 960), (540, 960), (905, 960)]}[n]
        self.nodes = []
        for i, nd in enumerate(spec["nodes"]):
            x, y = nd.get("pos", default[i])
            t0 = self.cue(nd["cue"], -0.1) if "cue" in nd else 0.15 + 0.12*i
            self.nodes.append(dict(nd, x=x, y=y, t0=t0, c=COLORS[nd.get("color", spec.get("color", "purple"))]))
            self.sfx(t0, "pop", 0.45)
        self.packets = []
        for p in spec.get("packets", []):
            t0 = self.cue(p["cue"], -0.05)
            self.packets.append(dict(p, t0=t0, c=COLORS[p.get("color", spec.get("color", "cyan"))]))
            self.sfx(t0, "whoosh", 0.35); self.sfx(t0 + 1.5, "pop", 0.3)
        self.bubbles = [dict(b, t0=self.cue(b["cue"], -0.05)) for b in spec.get("bubbles", [])]
        for b in self.bubbles: self.sfx(b["t0"], "pop", 0.4)
        self.col = COLORS[spec.get("color", "purple")]
        last = max([p["t0"] + 1.65 for p in self.packets] + [b["t0"] + 0.9 for b in self.bubbles] + [self.D])
        self.D = self._q(last)

    def draw(self, ctx, t):
        s = self.spec
        header(ctx, t, s["title"], s.get("sub"), self.col, s.get("gradient"))
        tsize = 240 if len(self.nodes) == 2 else 210
        for (i, j) in s.get("links", [[k, k + 1] for k in range(len(self.nodes) - 1)]):
            a, b = self.nodes[i], self.nodes[j]
            la = prog(t, max(a["t0"], b["t0"]) + 0.2, max(a["t0"], b["t0"]) + 0.5)
            if la > 0:
                ang = math.atan2(b["y"] - a["y"], b["x"] - a["x"]); off = 140
                x1, y1 = a["x"] + math.cos(ang)*off, a["y"] + math.sin(ang)*off
                x2, y2 = b["x"] - math.cos(ang)*off, b["y"] - math.sin(ang)*off
                ctx.new_path(); ctx.set_source_rgba(1, 1, 1, 0.28*la); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                ctx.set_dash([2, 22], -t*40); ctx.move_to(x1, y1); ctx.line_to(lerp(x1, x2, eo(la)), lerp(y1, y2, eo(la))); ctx.stroke(); ctx.set_dash([])
        hits = {}
        for p in self.packets: hits.setdefault(p["to"], []).append(p["t0"] + 1.5)
        for k, nd in enumerate(self.nodes):
            p = prog(t, nd["t0"], nd["t0"] + 0.4)
            pulse = 0; rings = []
            for h in hits.get(k, []):
                h2 = max(h, nd["t0"] + 0.4); pp = prog(t, h2, h2 + 0.5)
                if 0 < pp < 1: pulse = max(pulse, 1 - pp); rings.append(pp)
            tile(ctx, nd["icon"], nd["x"], nd["y"], nd.get("size", tsize), nd["c"], clamp(p*2),
                 back(p)*(1 + 0.08*pulse), nd.get("label"), label_size=38, pulse=pulse)
            for pp in rings: ring(ctx, nd["x"], nd["y"], 110 + 80*eo(pp), nd["c"], 0.7*(1 - pp))
        for p in self.packets:
            a, b = self.nodes[p["frm"]], self.nodes[p["to"]]
            lane = p.get("lane", -95 if b["x"] >= a["x"] else 95)
            ox, oy = (0, lane) if abs(b["x"] - a["x"]) > abs(b["y"] - a["y"]) else (lane, 0)
            x1, y1, x2, y2 = a["x"] + ox, a["y"] + oy, b["x"] + ox, b["y"] + oy
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            t0 = p["t0"]
            if t < t0 or t > t0 + 1.75: continue
            if t < t0 + 0.4:
                e = eo(prog(t, t0, t0 + 0.4)); x, y = lerp(x1, mx, e), lerp(y1, my, e); sc = lerp(0.4, 1, e)
            elif t < t0 + 1.15:
                x, y, sc = mx, my, 1.0
            else:
                e = eio(prog(t, t0 + 1.15, t0 + 1.5)); x, y = lerp(mx, x2, e), lerp(my, y2, e); sc = lerp(1, 0.3, e)
            swapped = p.get("label2") and t > t0 + 0.75
            pill(ctx, p["label2"] if swapped else p["label"], x, y,
                 COLORS[p.get("color2", "green")] if swapped else p["c"], 1 - prog(t, t0 + 1.45, t0 + 1.6), sc=sc)
        for bb in self.bubbles:
            nd = self.nodes[bb["node"]]; pb = prog(t, bb["t0"], bb["t0"] + 0.3)
            if pb > 0:
                pill(ctx, bb["text"], nd["x"] + bb.get("dx", 0), nd["y"] + bb.get("dy", -185),
                     COLORS[bb.get("color", "coral")], 1, size=34, sc=back(pb))


class Compare(Scene):
    def __init__(self, spec, d):
        super().__init__(spec, d)
        self.sides = []
        for k, side in enumerate(("left", "right")):
            sd = spec[side]
            t0 = self.cue(sd["cue"], -0.1); tb = self.cue(sd.get("badge_cue", sd["cue"]), 0.4)
            self.sides.append(dict(sd, t0=t0, tb=tb, c=COLORS[sd["color"]], x=290 if k == 0 else 790))
            self.sfx(t0, "whoosh", 0.4); self.sfx(tb, "chime" if sd.get("badge") == "check" else "thud", 0.6)
        self.D = self._q(max(self.D, max(sd["tb"] for sd in self.sides) + 0.8))

    def draw(self, ctx, t):
        s = self.spec
        header(ctx, t, s["title"], s.get("sub"), WHITE, s.get("gradient"))
        for sd in self.sides:
            p = prog(t, sd["t0"], sd["t0"] + 0.45)
            if p <= 0: continue
            dy = 80*(1 - eo(p)); a = clamp(p*1.6); x = sd["x"]
            ctx.save(); ctx.translate(0, dy)
            col(ctx, CARD, a); rrect(ctx, x - 235, 560, 470, 900, 40); ctx.fill()
            col(ctx, sd["c"], a); ctx.set_line_width(5); rrect(ctx, x - 235, 560, 470, 900, 40); ctx.stroke()
            fit_text(ctx, sd["name"], x, 660, 84, sd["c"], a, maxw=420)
            tile(ctx, sd["icon"], x, 900, 250, sd["c"], a)
            for i, l in enumerate(wrap(ctx, sd["point"], 42, 430)):
                text(ctx, l, x, 1150 + i*56, 42, WHITE, a)
            ctx.restore()
            pb = prog(t, sd["tb"], sd["tb"] + 0.35)
            if pb > 0:
                if sd.get("badge") == "check": check_badge(ctx, x + 200, 600, 52, 1, back(pb))
                else: cross_badge(ctx, x + 200, 600, 52, back(pb))


class ListScene(Scene):
    def __init__(self, spec, d):
        super().__init__(spec, d)
        self.items = []
        for it in spec["items"]:
            t0 = self.cue(it["cue"], -0.1)
            self.items.append(dict(it, t0=t0, c=COLORS[it.get("color", "purple")]))
            self.sfx(t0, "whoosh", 0.25); self.sfx(t0 + 0.2, "pop", 0.35)
        self.D = self._q(max(self.D, self.items[-1]["t0"] + 1.0))

    def draw(self, ctx, t):
        s = self.spec
        header(ctx, t, s["title"], s.get("sub"), COLORS[s.get("color", "purple")], s.get("gradient"))
        n = len(self.items); gap = 250 if n <= 3 else 205
        y0 = 1020 - (n - 1)*gap/2
        for i, it in enumerate(self.items):
            p = prog(t, it["t0"], it["t0"] + 0.4)
            if p <= 0: continue
            y = y0 + i*gap; x = lerp(W + 200, 0, back(p))
            ctx.save(); ctx.translate(x, 0)
            col(ctx, CARD, 1); rrect(ctx, 70, y - 95, 940, 190, 36); ctx.fill()
            col(ctx, it["c"], 0.8); ctx.set_line_width(4); rrect(ctx, 70, y - 95, 940, 190, 36); ctx.stroke()
            tile(ctx, it["icon"], 190, y, 130, it["c"], 1)
            lines = wrap(ctx, it["text"], 50, 700)
            for k, l in enumerate(lines):
                text(ctx, l, 300, y + (k - (len(lines) - 1)/2)*62, 50, WHITE, 1, anchor="l")
            ctx.restore()


class CTA(Scene):
    tail_default = 1.6

    def __init__(self, spec, d):
        super().__init__(spec, d)
        self.sfx(0.9, "pop", 0.6); self.sfx(1.9, "tick", 2.0)

    def caption(self): return ""

    def draw(self, ctx, t):
        s = self.spec
        tp = prog(t, 0.05, 0.4)
        pill(ctx, s.get("tag", "TECH IN 30 SECONDS"), W/2, 520, PURPLE, eo(tp), size=40, sc=lerp(0.8, 1, back(tp)))
        p = prog(t, 0.25, 0.65)
        text(ctx, "Follow for more tech,", W/2, 800, 72, WHITE, eo(p), scale=lerp(0.9, 1, eo(p)))
        text(ctx, "made simple", W/2, 900, 96, CYAN, eo(p), scale=lerp(0.9, 1, eo(p)), source=grad_src(CYAN, PURPLE))
        if s.get("next"):
            fit_text(ctx, "Next: " + s["next"], W/2, 1020, 44, MUTED, eo(prog(t, 0.6, 0.9)))
        bp = prog(t, 0.9, 1.25)
        if bp > 0:
            tt = max(0, t - 1.25)
            sc = back(bp)*(1 + 0.08*math.sin(tt*9)*math.exp(-tt*1.5))
            ctx.save(); ctx.translate(W/2, 1250); ctx.scale(sc, sc)
            glow(ctx, 0, 0, 300, PURPLE, 0.7)
            g = cairo.LinearGradient(-230, 0, 230, 0); g.add_color_stop_rgba(0, *PURPLE[:3], 1); g.add_color_stop_rgba(1, *CYAN[:3], 1)
            ctx.set_source(g); rrect(ctx, -230, -60, 460, 120, 60); ctx.fill()
            text(ctx, "FOLLOW", 30, 0, 56, WHITE, 1)
            ctx.set_source_rgba(1, 1, 1, 1); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(-140, 0); ctx.line_to(-104, 0); ctx.move_to(-122, -18); ctx.line_to(-122, 18); ctx.stroke()
            ctx.restore()
            tpp = prog(t, 1.5, 1.9)
            if tpp > 0:
                px, py = lerp(W/2 + 330, W/2 + 195, eo(tpp)), lerp(1430, 1295, eo(tpp))
                ctx.new_path(); ctx.set_source_rgba(1, 1, 1, 0.95); ctx.arc(px, py, 24, 0, 2*math.pi); ctx.fill()
                rp = prog(t, 1.9, 2.4); ring(ctx, px, py, 24 + 50*eo(rp), WHITE, 0.8*(1 - rp) if rp > 0 else 0, 5)
        text(ctx, s.get("handle", "@namanbuilds.ai"), W/2, 1420, 52, MUTED, eo(prog(t, 1.1, 1.4)))


TYPES = dict(hook=Hook, flow=Flow, compare=Compare, list=ListScene, cta=CTA)


def build(spec, durs):
    return [TYPES[sc["type"]](sc, d) for sc, d in zip(spec["scenes"], durs)]


def estimate_durations(spec, speed=None):
    speed = speed or spec.get("speed", 1.08)
    return [max(1.2, len(sc["vo"]) / (14.6 * speed)) for sc in spec["scenes"]]


def validate(spec, max_seconds=35.0):
    """Raise ValueError with a readable message if the spec cannot be rendered well."""
    errs = []
    sc = spec.get("scenes") or []
    if len(sc) < 3: errs.append("need at least 3 scenes")
    if sc and sc[0].get("type") != "hook": errs.append("first scene must be a hook")
    if sc and sc[-1].get("type") != "cta": errs.append("last scene must be a cta")
    for i, s in enumerate(sc):
        tname = s.get("type")
        if tname not in TYPES: errs.append(f"scene {i}: unknown type {tname}"); continue
        if not s.get("vo"): errs.append(f"scene {i}: missing vo")
        icons = []
        if tname == "hook": icons.append(s.get("icon"))
        if tname == "flow":
            if len(s.get("nodes", [])) not in (2, 3): errs.append(f"scene {i}: flow needs 2 or 3 nodes")
            icons += [n.get("icon") for n in s.get("nodes", [])]
            for p in s.get("packets", []):
                if len(p.get("label", "")) > 16: errs.append(f"scene {i}: packet label too long: {p.get('label')}")
                for k in ("frm", "to"):
                    if not isinstance(p.get(k), int) or p[k] >= len(s.get("nodes", [])): errs.append(f"scene {i}: bad packet {k}")
        if tname == "compare": icons += [s.get("left", {}).get("icon"), s.get("right", {}).get("icon")]
        if tname == "list":
            if not 2 <= len(s.get("items", [])) <= 4: errs.append(f"scene {i}: list needs 2-4 items")
            icons += [it.get("icon") for it in s.get("items", [])]
        for ic in icons:
            if ic not in ICONS: errs.append(f"scene {i}: unknown icon {ic}")
        def colors(o):
            for k, v in o.items():
                if k.startswith("color") or k.startswith("accent"):
                    if v not in COLORS: errs.append(f"scene {i}: unknown colour {v}")
                elif isinstance(v, dict): colors(v)
                elif isinstance(v, list):
                    for x in v:
                        if isinstance(x, dict): colors(x)
        colors(s)
    if errs: raise ValueError("; ".join(errs))
    scenes = build(spec, estimate_durations(spec))  # checks every cue word exists
    total = sum(s.D for s in scenes)
    if total > max_seconds: raise ValueError(f"estimated length {total:.1f}s is over {max_seconds}s; shorten the voiceover")
    return total


# ------------------------------------------------------------------ rendering pipeline
def tts(spec, workdir):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(f"{MODEL_DIR}/kokoro-v1.0.onnx", f"{MODEL_DIR}/voices-v1.0.bin")
    durs = []
    for i, sc in enumerate(spec["scenes"]):
        x, sr = k.create(sc["vo"], voice=spec.get("voice", "am_puck"), speed=spec.get("speed", 1.08), lang="en-us")
        sf.write(f"{workdir}/vo{i}.wav", x, sr); durs.append(len(x)/sr)
    return durs


def frame(sc, t, tg):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_BEST)
    background(ctx, tg)
    ctx.save(); sc.draw(ctx, t); ctx.restore()
    caption(ctx, sc.caption(), t, sc.D, VO_LEAD)
    scene_fade(ctx, t, sc.D)
    return surf


def _render_scene(args):
    spec_path, workdir, i, durs = args
    spec = json.load(open(spec_path)); scenes = build(spec, durs)
    sc = scenes[i]; t_start = sum(s.D for s in scenes[:i])
    tmp = f"{workdir}/s{i}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                          "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for f in range(round(sc.D*FPS)):
        t = f/FPS
        p.stdin.write(bytes(frame(sc, t, t_start + t).get_data()))
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError(f"ffmpeg failed on scene {i}")
    os.replace(tmp, f"{workdir}/s{i}.mp4")
    return i


def mix(scenes, workdir, out_wav):
    import soundfile as sf
    SR = sfx.SR
    total = sum(s.D for s in scenes); N = int(total*SR)
    vo = np.zeros(N); fx = np.zeros(N); t0 = 0.0
    for i, sc in enumerate(scenes):
        x, sr = sf.read(f"{workdir}/vo{i}.wav")
        fl = int(0.012*SR); x = x.copy(); x[:fl] *= np.linspace(0, 1, fl); x[-fl:] *= np.linspace(1, 0, fl)
        sfx.place(vo, x, t0 + VO_LEAD)
        for (t, kind, g) in sc.ev:
            sfx.place(fx, sfx.SOUNDS[kind](), t0 + t, g)
        if i > 0: sfx.place(fx, sfx.whoosh(0.35), t0 + 0.02, 0.3)
        t0 += sc.D
    vo = vo/np.max(np.abs(vo))*0.85; vo = vo + 0.25*sfx.lp(vo, 180)
    m = vo + fx*0.55 + sfx.music_bed(total, vo)
    m = np.tanh(m*1.1)/np.tanh(1.1); m = m/np.max(np.abs(m))*0.95
    sf.write(out_wav, m.astype(np.float32), SR)


def make(spec_path, out_mp4, procs=None, workdir=None, keep_work=False):
    spec = json.load(open(spec_path))
    validate(spec, max_seconds=60)
    workdir = workdir or os.path.splitext(out_mp4)[0] + "_work"; os.makedirs(workdir, exist_ok=True)
    durs = tts(spec, workdir)
    scenes = build(spec, durs)
    procs = procs or max(1, os.cpu_count() or 1)
    with Pool(procs) as pool:
        list(pool.imap_unordered(_render_scene, [(spec_path, workdir, i, durs) for i in range(len(scenes))]))
    with open(f"{workdir}/list.txt", "w") as f:
        for i in range(len(scenes)): f.write(f"file 's{i}.mp4'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{workdir}/list.txt", "-c", "copy", f"{workdir}/video.mp4"], check=True)
    mix(scenes, workdir, f"{workdir}/mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{workdir}/video.mp4", "-i", f"{workdir}/mix.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    if not keep_work:
        import shutil; shutil.rmtree(workdir, ignore_errors=True)
    return sum(s.D for s in scenes)


if __name__ == "__main__":
    secs = make(sys.argv[1], sys.argv[2])
    print(sys.argv[2], round(secs, 2), "s")
