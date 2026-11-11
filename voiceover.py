"""Adds a Spanish TTS voiceover (Piper, offline) to the Spanish video.
Usage: python3 voiceover.py <path/to/voice.onnx>  -> out/video_es_voz.mp4
Scenes stretch to fit each narration line, so text and voice stay in sync.
"""
import sys, wave, subprocess, os, array
import make_video as mv

NARR = [
    "Mis padres creen que la inteligencia artificial me hace pensar menos.",
    "Y tienen razón... si la usas mal.",
    "Dos formas de usarla: que piense por ti, o que te haga pensar.",
    "Así la uso yo. En vez de darme la razón, me pregunta por los márgenes, "
    "y por qué alguien me compraría a mí.",
    "Le pido que me lleve la contraria, que me explique, y que señale mis excusas.",
    "Eso no es pensar menos. Es tener a alguien que me exige más.",
    "La pregunta no es si uso inteligencia artificial. Es cómo la uso.",
    "Haced la prueba. Preguntadme lo que he aprendido.",
]
LEAD, TAIL, SPEED = 0.3, 0.5, 0.85  # SPEED <1 = faster speech

def main(model):
    os.makedirs("out/vo", exist_ok=True)
    clips = []
    for i, line in enumerate(NARR):
        path = f"out/vo/{i}.wav"
        subprocess.run(["piper", "-m", model, "-f", path, "--length_scale", str(SPEED), "--sentence_silence", "0.25",
                        "--noise-w-scale", "0.25", "--noise-scale", "0.45"],
                       input=line.encode(), check=True, capture_output=True)
        with wave.open(path) as w:
            sr, data = w.getframerate(), array.array("h", w.readframes(w.getnframes()))
        clips.append(data)
    durs = [max(base, LEAD + len(c) / sr + TAIL) for (_, base), c in zip(mv.SCENES, clips)]
    durs = [int(d * mv.FPS) / mv.FPS for d in durs]  # match the frame-exact scene lengths
    total = array.array("h", [0] * int(sum(durs) * sr + sr))
    t = 0.0
    for d, c in zip(durs, clips):
        start = int((t + LEAD) * sr)
        total[start:start + len(c)] = c
        t += d
    with wave.open("out/vo/full.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(total.tobytes())
    mv.render("es", durs, "out/vo/silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "out/vo/silent.mp4", "-i", "out/vo/full.wav",
                    "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "out/video_es_voz.mp4"], check=True)
    print("out/video_es_voz.mp4", round(sum(durs), 1), "s")

if __name__ == "__main__":
    main(sys.argv[1])
