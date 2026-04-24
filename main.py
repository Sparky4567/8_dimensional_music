from pathlib import Path
from pydub import AudioSegment
import numpy as np
import math

# Supported audio formats
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}

# Input and output directories
INPUT_DIR = Path("audios")
OUTPUT_DIR = Path("8d")
OUTPUT_DIR.mkdir(exist_ok=True)


def apply_8d_effect(audio: AudioSegment, rotation_speed: float = 0.075) -> AudioSegment:
    """
    Applies a simple 8D panning effect by moving audio
    smoothly between left and right channels.
    """
    samples = np.array(audio.get_array_of_samples())

    if audio.channels == 1:
        samples = samples.reshape((-1, 1))
        samples = np.repeat(samples, 2, axis=1)
    else:
        samples = samples.reshape((-1, 2))

    sample_rate = audio.frame_rate
    duration = len(samples) / sample_rate

    for i in range(len(samples)):
        t = i / sample_rate

        # Smooth sinusoidal panning
        pan = math.sin(2 * math.pi * rotation_speed * t)

        left_gain = math.sqrt((1 - pan) / 2)
        right_gain = math.sqrt((1 + pan) / 2)

        samples[i, 0] = int(samples[i, 0] * left_gain)
        samples[i, 1] = int(samples[i, 1] * right_gain)

    return AudioSegment(
        samples.astype(np.int16).tobytes(),
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=2
    )


def process_audio_file(input_file: Path) -> None:
    """Convert a single audio file into an 8D version."""
    print(f"Processing: {input_file.name}")

    audio = AudioSegment.from_file(input_file)
    audio_8d = apply_8d_effect(audio)

    output_file = OUTPUT_DIR / f"{input_file.stem}_8d.mp3"
    audio_8d.export(output_file, format="mp3")

    print(f"Saved: {output_file}")


def main() -> None:
    if not INPUT_DIR.exists():
        print(f"Input folder '{INPUT_DIR}' does not exist.")
        return

    audio_files = [
        file for file in INPUT_DIR.rglob("*")
        if file.is_file() and file.suffix.lower() in AUDIO_EXTENSIONS
    ]

    if not audio_files:
        print("No audio files found. The folder is quieter than a library at midnight.")
        return

    for audio_file in audio_files:
        try:
            process_audio_file(audio_file)
        except Exception as e:
            print(f"Failed to process {audio_file.name}: {e}")


if __name__ == "__main__":
    main()
