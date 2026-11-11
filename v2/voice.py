"""Step 1: synthesize the Spanish voiceover beat by beat (Kokoro TTS, offline) and write the timeline.
Usage: python3 v2/voice.py <dir with kokoro-v1.0.onnx + voices-v1.0.bin>
Outputs v2/build/voice.wav and v2/build/timeline.json (start/end of every beat, used by the animation).
"""
import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOICE, SPEED, GAP, LEAD, TAIL = "em_alex", 1.08, 0.18, 0.4, 1.4

# id, what the voice says, what appears on screen (None = same words)
BEATS = [
    ("age",     "Tengo dieciocho años.", "Tengo 18 años."),
    ("parents", "Y mis padres creen que la i a me hace pensar menos.", "Y mis padres creen que la IA me hace pensar menos."),
    ("wrong",   "Y si la usas mal... tienen razón.", "Y si la usas mal… tienen razón."),
    ("copy",    "Copias. Pegas. Entregas.", None),
    ("zero",    "Cero ideas tuyas.", None),
    ("but",     "Pero yo no la uso así.", None),
    ("idea",    "Le cuento una idea. Por ejemplo, revender colonias.", None),
    ("destroy", "Y en vez de darme la razón, me la destroza.", None),
    ("forty",   "Yo pensaba que ganaba un cuarenta por ciento.", "Yo pensaba que ganaba un 40%."),
    ("nine",    "Después de envíos y comisiones... un nueve.", "Después de envíos y comisiones… un 9%."),
    ("argue",   "Le pido que me lleve la contraria.", None),
    ("explain", "Que me explique las cosas, no que me las haga.", None),
    ("excuses", "Y que me pille las excusas.", None),
    ("notless", "Eso no es pensar menos.", None),
    ("more",    "Es pensar con alguien que me exige más.", None),
    ("test",    "¿No me creéis? Preguntadme lo que he aprendido.", None),
]

def main(model_dir):
    k = Kokoro(os.path.join(model_dir, "kokoro-v1.0.onnx"), os.path.join(model_dir, "voices-v1.0.bin"))
    os.makedirs("v2/build", exist_ok=True)
    parts, beats, t, sr = [], [], LEAD, 24000
    parts.append(np.zeros(int(LEAD * sr), dtype=np.float32))
    for bid, say, show in BEATS:
        a, sr = k.create(say, voice=VOICE, speed=SPEED, lang="es")
        a = a.astype(np.float32)
        # trim leading/trailing near-silence so beat timing matches the actual words
        idx = np.where(np.abs(a) > 0.01)[0]
        if len(idx): a = a[max(0, idx[0] - 600): idx[-1] + 1200]
        d = len(a) / sr
        beats.append(dict(id=bid, text=show or say, s=round(t, 3), e=round(t + d, 3)))
        parts += [a, np.zeros(int(GAP * sr), dtype=np.float32)]
        t += d + GAP
    parts.append(np.zeros(int(TAIL * sr), dtype=np.float32))
    audio = np.concatenate(parts)
    audio = audio / max(1e-6, np.abs(audio).max()) * 0.9
    sf.write("v2/build/voice.wav", audio, sr)
    total = len(audio) / sr
    json.dump(dict(total=round(total, 3), beats=beats), open("v2/build/timeline.json", "w"), ensure_ascii=False, indent=1)
    print("voice", round(total, 1), "s")
    for b in beats: print(f"{b['s']:6.2f}-{b['e']:6.2f} {b['id']}")

if __name__ == "__main__":
    main(sys.argv[1])
