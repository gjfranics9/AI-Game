import base64

sounds = {
    "block_spawn.wav": "UklGRjQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQcAAAABAACAgICAgICAgIA=",
    "game_over.wav": "UklGRjQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQYAAAAAAAD//wAAAP8A",
    "score_tick.wav": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQcAAAABAACAgID///8="
}

for filename, b64 in sounds.items():
    with open(filename, "wb") as f:
        f.write(base64.b64decode(b64))
print("Sound files saved.")
