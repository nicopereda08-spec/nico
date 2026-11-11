"""Renders a ~40s vertical (1080x1920) kinetic-text video: why AI doesn't have to make you think less.
Usage: python3 make_video.py es|en   -> out/video_<lang>.mp4
"""
import subprocess, sys, math, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (14, 14, 16)
FG = (240, 238, 232)
DIM = (130, 128, 122)
ACC = (232, 140, 80)
GOOD = (120, 200, 140)
BAD = (220, 95, 90)
BUB_ME = (46, 46, 52)
BUB_AI = (36, 30, 26)

F = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(F + f"Inter-{w}.otf", s)

TEXT = {
  "es": dict(
    hook=["Mis padres creen que", "la IA me hace", "pensar menos."],
    fair=["Y tienen razón…", "si la usas mal."],
    vs_title="Hay dos formas de usarla:",
    bad_l="Que piense por ti", bad_s="“Hazme el trabajo.”",
    good_l="Que te haga pensar", good_s="“Dime en qué me equivoco.”",
    chat_title="Así la uso yo:",
    me1="Quiero revender colonias online.",
    ai1="¿Has calculado el margen después de envíos y comisiones? ¿Por qué te comprarían a ti y no a una tienda grande?",
    me2="…no lo había pensado.",
    rules_title="Le pido que:",
    rules=["me lleve la contraria", "me explique, no que me lo haga", "señale mis excusas"],
    punch=["Eso no es pensar menos.", "Es tener a alguien", "que me exige más."],
    close=["La pregunta no es", "si uso IA.", "Es cómo la uso."],
    test=["Haced la prueba:", "preguntadme lo que", "he aprendido."],
  ),
  "en": dict(
    hook=["My parents think", "AI makes me", "think less."],
    fair=["And they're right…", "if you use it wrong."],
    vs_title="There are two ways to use it:",
    bad_l="It thinks for you", bad_s="“Just do it for me.”",
    good_l="It makes you think", good_s="“Tell me where I'm wrong.”",
    chat_title="This is how I use it:",
    me1="I want to resell cologne online.",
    ai1="Have you worked out your margin after shipping and fees? Why would anyone buy from you instead of a big store?",
    me2="…I hadn't thought about that.",
    rules_title="I ask it to:",
    rules=["argue against me", "explain, not do it for me", "call out my excuses"],
    punch=["That's not thinking less.", "It's having someone", "who pushes me harder."],
    close=["The question isn't", "whether I use AI.", "It's how I use it."],
    test=["Test me:", "ask me about anything", "I've learned."],
  ),
}

def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3

def mix(c, a):  # fade colour toward background
    return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def center_text(d, y, text, f, color, a=1.0, dy=0):
    tw = d.textlength(text, font=f)
    d.text(((W - tw) / 2, y + dy), text, font=f, fill=mix(color, a))

def stack(d, t, lines, colors, size=96, gap=1.25, stagger=0.35, y0=None, weight="Bold"):
    f = font(weight, size)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while max(probe.textlength(l, font=f) for l in lines) > W - 140:
        size -= 4; f = font(weight, size)
    lh = size * gap
    y0 = y0 if y0 is not None else (H - lh * len(lines)) / 2
    for i, ln in enumerate(lines):
        a = ease((t - i * stagger) / 0.45)
        center_text(d, y0 + i * lh, ln, f, colors[i] if isinstance(colors, list) else colors, a, dy=(1 - a) * 40)

def scene_fade(t, dur):  # global fade in/out per scene
    return min(ease(t / 0.25), ease((dur - t) / 0.25))

# ---------- scenes ----------
def s_hook(d, t, L):
    stack(d, t, L["hook"], [FG, FG, ACC], size=104, stagger=0.4)

def s_fair(d, t, L):
    stack(d, t, L["fair"], [FG, BAD], size=96, stagger=0.8)

def s_vs(d, t, L):
    center_text(d, 360, L["vs_title"], font("SemiBold", 60), DIM, ease(t / 0.4))
    for i, (lab, sub, col, mark) in enumerate([(L["bad_l"], L["bad_s"], BAD, "✕"), (L["good_l"], L["good_s"], GOOD, "✓")]):
        a = ease((t - 0.6 - i * 1.4) / 0.5)
        y = 640 + i * 480
        x0, x1 = 90, W - 90
        d.rounded_rectangle((x0, y + (1 - a) * 40, x1, y + 360 + (1 - a) * 40), 36,
                            outline=mix(col, a), width=5, fill=mix((24, 24, 28), a))
        f_big = font("Bold", 74)
        center_text(d, y + 80, lab, f_big, col, a, dy=(1 - a) * 40)
        center_text(d, y + 200, sub, font("Medium", 54), FG, a * 0.85, dy=(1 - a) * 40)
    # strike the bad option late in the scene
    s = ease((t - 3.6) / 0.4)
    if s > 0:
        d.line((140, 820, 140 + (W - 280) * s, 820), fill=BAD, width=8)

def bubble(d, t, start, text, mine, y, label):
    a = ease((t - start) / 0.4)
    if a <= 0: return y
    f = font("Medium", 50)
    maxw = 720
    lines = wrap(d, text, f, maxw)
    lh = 66
    bw = max(d.textlength(l, font=f) for l in lines) + 80
    bh = lh * len(lines) + 60
    x = W - 70 - bw if mine else 70
    yy = y + (1 - a) * 30
    d.text((x + 10, yy - 50), label, font=font("SemiBold", 36), fill=mix(DIM, a))
    d.rounded_rectangle((x, yy, x + bw, yy + bh), 34,
                        fill=mix(BUB_ME if mine else BUB_AI, a),
                        outline=None if mine else mix(ACC, a * 0.7), width=3)
    for i, l in enumerate(lines):
        d.text((x + 40, yy + 30 + i * lh), l, font=f, fill=mix(FG, a))
    return y + bh + 110

def s_chat(d, t, L, lang):
    center_text(d, 260, L["chat_title"], font("Bold", 72), ACC, ease(t / 0.4))
    me, ai = ("Yo", "IA") if lang == "es" else ("Me", "AI")
    y = 520
    y = bubble(d, t, 0.6, L["me1"], True, y, me)
    y = bubble(d, t, 1.8, L["ai1"], False, y, ai)
    bubble(d, t, 5.4, L["me2"], True, y, me)

def s_rules(d, t, L):
    center_text(d, 560, L["rules_title"], font("Bold", 80), FG, ease(t / 0.4))
    fs = 60
    f = font("SemiBold", fs)
    while max(d.textlength(r, font=f) for r in L["rules"]) > W - 340:
        fs -= 2; f = font("SemiBold", fs)
    for i, r in enumerate(L["rules"]):
        a = ease((t - 0.7 - i * 0.7) / 0.4)
        y = 780 + i * 170
        x = 110 + (1 - a) * -40
        d.ellipse((x, y + 12, x + 52, y + 64), fill=mix(ACC, a))
        d.text((x + 13, y + 10), "✓", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40), fill=mix(BG, a))
        d.text((x + 90, y + 4), r, font=f, fill=mix(FG, a))

def s_punch(d, t, L):
    stack(d, t, L["punch"], [DIM, FG, ACC], size=88, stagger=0.7)

def s_close(d, t, L):
    stack(d, t, L["close"], [FG, FG, ACC], size=96, stagger=0.6)

def s_test(d, t, L):
    stack(d, t, L["test"], [ACC, FG, FG], size=96, stagger=0.5)

SCENES = [  # (fn, seconds)
    (s_hook, 3.6), (s_fair, 3.4), (s_vs, 5.4), ("chat", 8.0),
    (s_rules, 4.6), (s_punch, 4.4), (s_close, 4.2), (s_test, 4.6),
]

def render(lang):
    L = TEXT[lang]
    os.makedirs("out", exist_ok=True)
    out = f"out/video_{lang}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for fn, dur in SCENES:
        for k in range(int(dur * FPS)):
            t = k / FPS
            img = Image.new("RGB", (W, H), BG)
            layer = Image.new("RGB", (W, H), BG)
            d = ImageDraw.Draw(layer)
            if fn == "chat": s_chat(d, t, L, lang)
            else: fn(d, t, L)
            a = scene_fade(t, dur)
            img = Image.blend(img, layer, a) if a < 1 else layer
            p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    print(out, sum(d for _, d in SCENES), "s")

if __name__ == "__main__":
    for lang in (sys.argv[1:] or ["es", "en"]):
        render(lang)
