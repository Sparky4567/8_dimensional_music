from pathlib import Path
from pydub import AudioSegment
import numpy as np
import math

# ==============================
# Configuration
# ==============================

INPUT_DIR = Path("audios")
OUTPUT_DIR = Path("8d")
OUTPUT_DIR.mkdir(exist_ok=True)

SUPPORTED_FORMATS = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"
}

ROTATION_SPEED = 0.075      # Revolutions per second
DEPTH = 0.95               # Stereo width
VOLUME_SWING_DB = 4.0       # Distance illusion
CHUNK_MS = 10               # Processing chunk size


def apply_8d_rotation(audio: AudioSegment) -> AudioSegment:
    """
    Creates a convincing 8D rotating audio effect by combining:
    - Circular stereo panning
    - Distance simulation
    - Smooth motion
    """
    audio = audio.set_channels(2)

    frame_rate = audio.frame_rate
    sample_width = audio.sample_width
    samples = np.array(audio.get_array_of_samples())

    samples = samples.reshape((-1, 2)).astype(np.float32)

    samples_per_chunk = int(frame_rate * CHUNK_MS / 1000)

    processed_chunks = []

    for chunk_index, start in enumerate(
        range(0, len(samples), samples_per_chunk)
    ):
        chunk = samples[start:start + samples_per_chunk]

        if len(chunk) == 0:
            continue

        t = (start / frame_rate)

        # Circular movement angle
        angle = 2 * math.pi * ROTATION_SPEED * t

        # Equal-power panning
        pan = math.sin(angle)
        left_gain = math.sqrt((1 - pan) / 2)
        right_gain = math.sqrt((1 + pan) / 2)

        # Front/back distance illusion
        distance = (math.cos(angle) + 1) / 2
        attenuation = 10 ** (
            (-VOLUME_SWING_DB * (1 - distance)) / 20
        )

        chunk[:, 0] *= left_gain * attenuation * DEPTH
        chunk[:, 1] *= right_gain * attenuation * DEPTH

        processed_chunks.append(chunk)

    result = np.vstack(processed_chunks)

    # Prevent clipping
    peak = np.max(np.abs(result))
    if peak > 32767:
        result *= 32767 / peak

    return AudioSegment(
        result.astype(np.int16).tobytes(),
        frame_rate=frame_rate,
        sample_width=sample_width,
        channels=2
    )


def convert_file(source: Path) -> None:
    print(f"🎧 Processing: {source.name}")

    audio = AudioSegment.from_file(source)
    audio_8d = apply_8d_rotation(audio)

    destination = OUTPUT_DIR / f"rotational_{source.stem}_8d.mp3"
    audio_8d.export(destination, format="mp3")

    print(f"✅ Saved: {destination.name}")


def main() -> None:
    if not INPUT_DIR.exists():
        print(f"Folder not found: {INPUT_DIR}")
        return

    files = [
        file for file in INPUT_DIR.rglob("*")
        if file.suffix.lower() in SUPPORTED_FORMATS
    ]

    if not files:
        print("No audio files found. The silence is deafening.")
        return

    for file in files:
        try:
            convert_file(file)
        except Exception as error:
            print(f"❌ Failed: {file.name} ({error})")


if __name__ == "__main__":
    main()
