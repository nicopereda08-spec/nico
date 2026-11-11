"""Step 1: synthesize the English voiceover beat by beat (Kokoro TTS, offline) and write the timeline.
Usage: python3 v2/voice.py <dir with kokoro-v1.0.onnx + voices-v1.0.bin>
Outputs v2/build/voice.wav and v2/build/timeline.json (start/end of every beat, used by the animation).
"""
import json, os, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOICE, SPEED, GAP, LEAD, TAIL = "am_michael", 1.05, 0.18, 0.4, 1.4

# id, what the voice says, what appears on screen (None = same words)
BEATS = [
    ("age",     "I'm eighteen.", "I'm 18."),
    ("parents", "And my parents think AI makes me think less.", None),
    ("wrong",   "And if you use it badly... they're right.", "And if you use it badly… they're right."),
    ("copy",    "Copy. Paste. Submit.", None),
    ("zero",    "Zero original ideas.", None),
    ("but",     "But I don't use it like that.", None),
    ("idea",    "I pitch it an idea. Like reselling cologne.", None),
    ("destroy", "And instead of agreeing with me, it tears it apart.", None),
    ("forty",   "I thought my margin was forty percent.", "I thought my margin was 40%."),
    ("nine",    "After shipping and fees... nine.", "After shipping and fees… 9%."),
    ("argue",   "I ask it to push back.", None),
    ("explain", "To explain things, not do them for me.", None),
    ("excuses", "And to call out my excuses.", None),
    ("notless", "That's not thinking less.", None),
    ("more",    "It's thinking with someone who pushes me harder.", None),
    ("test",    "Don't believe me? Ask me what I've learned.", None),
]

def main(model_dir):
    k = Kokoro(os.path.join(model_dir, "kokoro-v1.0.onnx"), os.path.join(model_dir, "voices-v1.0.bin"))
    os.makedirs("v2/build", exist_ok=True)
    parts, beats, t, sr = [], [], LEAD, 24000
    parts.append(np.zeros(int(LEAD * sr), dtype=np.float32))
    for bid, say, show in BEATS:
        a, sr = k.create(say, voice=VOICE, speed=SPEED, lang="en-us")
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
