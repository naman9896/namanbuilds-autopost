"""Synthesised sound effects and the lo-fi music bed (no external audio files needed)."""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 24000
rng = np.random.default_rng(3)


def place(buf, x, t, g=1.0):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if 0 <= i < len(buf): buf[i:j] += x[:j - i] * g


def env(n, a=0.005, r=None):
    e = np.ones(n); na = max(1, int(a*SR)); e[:na] = np.linspace(0, 1, na)
    if r: e *= np.exp(-np.arange(n)/SR / r)
    return e


def tone(f0, f1, dur, decay):
    n = int(dur*SR); f = np.linspace(f0, f1, n)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * env(n, 0.002, decay)


def noise(dur): return rng.standard_normal(int(dur*SR))
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)


def add(a, b):
    n = max(len(a), len(b)); o = np.zeros(n); o[:len(a)] += a; o[:len(b)] += b; return o


def whoosh(dur=0.4):
    n = int(dur*SR); x = noise(dur)
    lo = bp(x, 300, 1500); hi = bp(x, 1500, 6000)
    s = np.linspace(0, 1, n); e = np.sin(np.pi*s)**2
    return (lo*(1 - s) + hi*s) * e * 0.5


def pop(): return add(tone(520, 980, 0.12, 0.035)*0.6, hp(noise(0.01), 3000)*0.15)
def thud(): return add(tone(110, 45, 0.35, 0.09)*0.9, lp(noise(0.08), 400)*env(int(0.08*SR), 0.001, 0.02)*0.5)
def tick(): return tone(2200, 2200, 0.02, 0.004)*0.25


def chime():
    out = np.zeros(int(0.8*SR))
    for k, f in enumerate([1318.5, 1760.0]):
        t_ = add(tone(f, f, 0.7, 0.25)*0.35, tone(2*f, 2*f, 0.7, 0.12)*0.08)
        i = int(k*0.08*SR); out[i:i+len(t_)] += t_
    return out


SOUNDS = dict(whoosh=whoosh, pop=pop, thud=thud, tick=tick, chime=chime)


def music_bed(total, vo):
    """96 bpm lo-fi loop, faded in/out and ducked under the voice."""
    N = int(total*SR); mus = np.zeros(N); bpm = 96; beat = 60/bpm; bar = 4*beat
    midi = lambda n: 440*2**((n - 69)/12)
    chords = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 66]]
    for b in range(int(total/bar) + 1):
        ch = chords[b % 4]; tb = b*bar; n = int(bar*SR); tt = np.arange(n)/SR
        e = np.minimum(1, tt/0.25)*np.minimum(1, (bar - tt)/0.3)
        pad = sum(np.sin(2*np.pi*midi(x)*tt) + 0.5*np.sin(2*np.pi*midi(x)*1.003*tt) for x in ch)
        place(mus, lp(pad, 1800)*e*0.06, tb)
        for bt in (0, 2): place(mus, tone(midi(ch[0] - 12), midi(ch[0] - 12), beat*1.6, 0.5)*0.22, tb + bt*beat)
        for bt in range(4):
            if bt in (0, 2): place(mus, tone(120, 45, 0.3, 0.08)*0.55, tb + bt*beat)
            else: place(mus, bp(noise(0.12), 900, 5000)*env(int(0.12*SR), 0.001, 0.04)*0.35, tb + bt*beat)
        for k in range(8):
            place(mus, hp(noise(0.03), 6000)*env(int(0.03*SR), 0.001, 0.008)*(0.14 if k % 2 else 0.08), tb + k*beat/2)
    fade = np.ones(N); fi = int(0.4*SR); fade[:fi] = np.linspace(0, 1, fi)
    fo = int(1.8*SR); fade[-fo:] = np.linspace(1, 0, fo)
    venv = np.convolve(np.abs(vo), np.ones(int(0.15*SR))/int(0.15*SR), mode='same')
    mus = mus*fade*(1 - 0.45*np.clip(venv/0.05, 0, 1))
    return mus/(np.max(np.abs(mus)) + 1e-9)*0.30
