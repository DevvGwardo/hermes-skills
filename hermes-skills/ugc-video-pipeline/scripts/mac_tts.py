#!/usr/bin/env python3
"""
mac_tts.py — macOS-native TTS using the `say` command.
No internet, no API keys, no GPU needed.
"""

import argparse
import os
import subprocess
import tempfile
import time


AVAILABLE_VOICES = {
    "Samantha":      "com.apple.voice.compact.en-US.Samantha",
    "Allison":       "com.apple.voice.compact.en-US.Allison",
    "Ava":           "com.apple.voice.enhanced.en-US.Ava",
    "Victoria":      "com.apple.voice.enhanced.en-US.Victoria",
    "Karen":         "com.apple.voice.compact.en-AU.Karen",
    "Daniel":        "com.apple.voice.compact.en-GB.Daniel",
    "Moira":         "com.apple.voice.compact.en-IE.Moira",
    "Tessa":         "com.apple.voice.compact.en-ZA.Tessa",
    "Fiona":         "com.apple.voice.compact.en-GB.Fiona",
    "Fred":          "com.apple.voice.enhanced.en-US.Fred",
    "Albert":        "com.apple.voice.enhanced.de-DE.Albert",
    "Alice":         "com.apple.voice.enhanced.it-IT.Alice",
    "Alva":          "com.apple.voice.enhanced.sv-SE.Alva",
    "Kylie":         "com.apple.voice.compact.en-AU.Kylie",
    "Zosia":         "com.apple.voice.compact.pl-PL.Zosia",
    "Maged":         "com.apple.voice.enhanced.ar-SA.Maged",
    "Tian-Tian":     "com.apple.voice.enhanced.zh-CN.TianTian",
    "Yuna":          "com.apple.voice.enhanced.ko-KR.Yuna",
    "Milena":        "com.apple.voice.compact.ru-RU.Milena",
}

# Speech rates: 0.0 (normal) → 0.5 (fast) → -0.5 (slow)
# Typical audiobook = 0.48, podcast = 0.52, urgent = 0.55
RATE_LABELS = {
    "slow":   0.45,
    "normal": 0.50,
    "fast":   0.55,
    "urgent": 0.58,
}


def list_voices():
    """List all available macOS voices."""
    result = subprocess.run(
        ["say", "-v", "?"],
        capture_output=True, text=True, check=True
    )
    for line in result.stdout.splitlines():
        print(line)


def get_audio_duration(aiff_path: str) -> float:
    """Get duration of AIFF file using afinfo."""
    result = subprocess.run(
        ["afinfo", aiff_path],
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if "estimated duration" in line.lower():
            parts = line.split(":")
            if len(parts) > 1:
                return float(parts[1].strip().split()[0])
    return 0.0


def synthesize(
    text: str,
    output_path: str,
    voice: str = "Samantha",
    rate: float = 0.52,
    input_file: str = None,
) -> str:
    """
    Synthesize speech using macOS `say` command.

    Args:
        text:           Text to speak. If None, reads from input_file.
        output_path:     Output AIFF/M4A path.
        voice:          Voice name (see AVAILABLE_VOICES).
        rate:           Speech rate (0.45 slow → 0.58 fast).
        input_file:     Optional: read text from file instead.

    Returns:
        Path to the audio file.
    """
    voice_id = AVAILABLE_VOICES.get(voice, voice)

    cmd = [
        "say",
        "-v", voice_id,
        "-r", str(int(rate * 175)),  # convert 0-1 to WPM-ish
        "-o", output_path,
    ]

    if input_file:
        with open(input_file, "r") as f:
            text = f.read().strip()

    if not text:
        raise ValueError("No text provided and no input file given.")

    print(f"[mac_tts] Voice: {voice} ({voice_id}), rate: {rate}")
    print(f"[mac_tts] Text: {text[:80]}{'...' if len(text) > 80 else ''}")

    # say reads text from stdin if given -
    result = subprocess.run(
        cmd + ["--"],
        input=text,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"say command failed: {result.stderr}")

    if not os.path.exists(output_path):
        raise RuntimeError(f"say produced no output at {output_path}")

    duration = get_audio_duration(output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"[mac_tts] Saved: {output_path} ({size_kb:.0f} KB, {duration:.1f}s)")

    return output_path


def text_to_wav(text: str, wav_path: str, voice: str = "Samantha", rate: float = 0.52) -> str:
    """
    Synthesize speech and convert to WAV (16kHz mono, UGC pipeline compatible).
    Converts AIFF → WAV using FFmpeg.
    """
    aiff_path = wav_path.replace(".wav", ".aiff")
    synthesize(text, aiff_path, voice=voice, rate=rate)

    # Convert AIFF to 16kHz mono WAV (pipeline standard)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", aiff_path,
        "-ar", "16000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        wav_path,
    ], check=True, capture_output=True)

    os.remove(aiff_path)
    print(f"[mac_tts] WAV: {wav_path}")
    return wav_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="macOS-native TTS via `say` command")
    parser.add_argument("--text", help="Text to synthesize")
    parser.add_argument("--input-file", help="Read text from file")
    parser.add_argument("--output", required=True, help="Output WAV path")
    parser.add_argument("--voice", default="Samantha",
                        choices=list(AVAILABLE_VOICES.keys()),
                        help="Voice name (default: Samantha)")
    parser.add_argument("--rate", type=float, default=0.52,
                        help="Speech rate 0.45-0.58 (default: 0.52)")
    parser.add_argument("--rate-label",
                        choices=list(RATE_LABELS.keys()),
                        help="Preset rate: slow=0.45, normal=0.50, fast=0.55, urgent=0.58")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available voices and exit")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
    elif args.rate_label:
        rate = RATE_LABELS[args.rate_label]
        text_to_wav(args.text or "", args.output, voice=args.voice, rate=rate)
    else:
        text_to_wav(args.text or "", args.output, voice=args.voice, rate=args.rate)
