import wave, struct, math, os

def make_tone(name, f_start, f_end, duration, volume=0.4, rate=44100):
    os.makedirs("sounds", exist_ok=True)
    n = int(rate * duration)
    with wave.open(os.path.join("sounds", name), "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        phase = 0.0
        for i in range(n):
            t = i / n
            phase += 2 * math.pi * (f_start + (f_end - f_start) * t) / rate
            sample = int(32767 * volume * (1 - t) * math.sin(phase))
            f.writeframes(struct.pack("<h", sample))

make_tone("shoot.wav", 900, 300, 0.15)
make_tone("explosion.wav", 300, 60, 0.30)
make_tone("game_over.wav", 400, 80, 1.00)
