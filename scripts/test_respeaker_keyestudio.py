#!/usr/bin/env python3
"""
Interactive audio test for the Keyestudio 5V ReSpeaker 2-Mic Pi HAT.

The script will:
  1. List the available ALSA playback and capture devices.
  2. Play a short sine wave tone through the selected speaker output.
  3. Record audio from the selected microphones and play it back.

It defaults to the first ALSA card that looks like the ReSpeaker but you can
override the card or device strings with the command line flags.
"""

from __future__ import annotations

import argparse
import array
import math
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
from typing import Optional


KEYWORDS = ("respeaker", "seeed", "keyestudio", "2mic", "voice")


def require_command(name: str) -> None:
    """Ensure an external command exists before trying to use it."""
    if shutil.which(name) is None:
        raise RuntimeError(
            f"Required command '{name}' not found on PATH. "
            f"Install ALSA utils (provides {name}) and try again."
        )


def run_and_print(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command, stream stdout/stderr live, and return the completed process."""
    print(f"$ {' '.join(shlex.quote(part) for part in cmd)}")
    return subprocess.run(cmd, check=False)


def list_devices() -> None:
    """Print the available playback and capture devices."""
    print("\n=== Available ALSA Playback Devices (aplay -l) ===")
    run_and_print(["aplay", "-l"])
    print("\n=== Available ALSA Capture Devices (arecord -l) ===")
    run_and_print(["arecord", "-l"])
    print("")


def detect_card_index() -> Optional[int]:
    """Try to find the ALSA card index that matches the ReSpeaker HAT."""
    try:
        output = subprocess.check_output(["aplay", "-l"], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    for line in output.splitlines():
        line_lower = line.lower()
        if "card" not in line_lower:
            continue
        if any(keyword in line_lower for keyword in KEYWORDS):
            parts = line.split(":")[0].split()
            # Expected format: 'card 1'
            for part in parts:
                if part.isdigit():
                    return int(part)
    return None


def generate_tone(
    frequency: float,
    duration: float,
    sample_rate: int,
    volume: float = 0.2,
) -> bytes:
    """Create PCM16 mono samples for a simple sine wave."""
    total_samples = int(sample_rate * duration)
    radians_per_sample = 2.0 * math.pi * frequency / sample_rate
    amplitude = max(0.0, min(volume, 1.0)) * 32767
    samples = array.array(
        "h",
        (
            int(amplitude * math.sin(radians_per_sample * n))
            for n in range(total_samples)
        ),
    )
    return samples.tobytes()


def play_tone(playback_device: str, tone: bytes, sample_rate: int) -> None:
    """Send the generated tone to the speaker with aplay."""
    print(
        textwrap.dedent(
            f"""
            === Speaker Test ===
            Device: {playback_device}
            Action: Playing sine wave tone
            Tip: You should hear a clear beep from the attached speaker.
            """
        ).strip()
    )
    cmd = [
        "aplay",
        "-D",
        playback_device,
        "-f",
        "S16_LE",
        "-c",
        "1",
        "-r",
        str(sample_rate),
    ]
    print("")
    print("Playing tone...")
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        proc.communicate(input=tone)
    except FileNotFoundError as exc:
        raise RuntimeError("aplay command not found. Install ALSA utils.") from exc

    if proc.returncode == 0:
        print("✓ Tone playback command completed.\n")
    else:
        raise RuntimeError(f"aplay exited with code {proc.returncode}.")


def record_and_playback(
    capture_device: str,
    playback_device: str,
    duration: float,
    sample_rate: int,
    channels: int,
) -> None:
    """Record audio via arecord then play it back via aplay."""
    print(
        textwrap.dedent(
            f"""
            === Microphone Test ===
            Capture device: {capture_device}
            Playback device: {playback_device}
            Action: Record your voice and play it back.
            Tip: Speak clearly into the microphones once recording starts.
            """
        ).strip()
    )
    with tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False
    ) as tmp_wav:
        tmp_wav_path = tmp_wav.name

    duration_seconds = max(1, int(math.ceil(duration)))
    if not math.isclose(duration_seconds, duration, rel_tol=0.0, abs_tol=1e-6):
        print(
            f"Requested duration {duration:.2f}s rounded up to "
            f"{duration_seconds}s for arecord compatibility."
        )

    print("")
    print(f"Recording {duration_seconds} seconds of audio...")
    record_cmd = [
        "arecord",
        "-D",
        capture_device,
        "-f",
        "S16_LE",
        "-c",
        str(channels),
        "-r",
        str(sample_rate),
        "-d",
        str(duration_seconds),
        "-t",
        "wav",
        tmp_wav_path,
    ]
    record_proc = run_and_print(record_cmd)
    if record_proc.returncode != 0:
        os.unlink(tmp_wav_path)
        raise RuntimeError(
            f"arecord exited with code {record_proc.returncode}. "
            "Check that the microphones are not muted and the device number is correct."
        )

    print("")
    print(f"Playback of recorded sample ({tmp_wav_path})...")
    play_cmd = [
        "aplay",
        "-D",
        playback_device,
        tmp_wav_path,
    ]
    play_proc = run_and_print(play_cmd)
    if play_proc.returncode != 0:
        raise RuntimeError(
            f"aplay exited with code {play_proc.returncode} while playing the recording."
        )

    print("")
    print("✓ Microphone loopback complete.")
    print(f"The recording has been left at: {tmp_wav_path}")
    print("Remove it manually when you no longer need it.")
    print("")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test speaker and microphone on the Keyestudio ReSpeaker 2-Mic Pi HAT."
        )
    )
    parser.add_argument(
        "--card",
        type=int,
        help="Override the ALSA card index (e.g. --card 1).",
    )
    parser.add_argument(
        "--playback-device",
        help="Override the ALSA playback device string (default: plughw:<card>,0).",
    )
    parser.add_argument(
        "--capture-device",
        help="Override the ALSA capture device string (default: plughw:<card>,0).",
    )
    parser.add_argument(
        "--tone-frequency",
        type=float,
        default=440.0,
        help="Tone frequency in Hz for the speaker test (default: 440.0).",
    )
    parser.add_argument(
        "--tone-duration",
        type=float,
        default=2.0,
        help="Tone duration in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--record-duration",
        type=float,
        default=5.0,
        help="Recording duration in seconds (default: 5.0).",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Sample rate in Hz for both tests (default: 16000).",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=2,
        help="Number of microphone channels to record (default: 2).",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Only list ALSA devices and exit.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        require_command("aplay")
        require_command("arecord")
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    args = parse_args()

    if args.list_devices:
        list_devices()
        return 0

    card_index = args.card if args.card is not None else detect_card_index()

    if card_index is None:
        print(
            "Could not automatically detect the ReSpeaker ALSA card. "
            "Use --card <index> or --playback-device/--capture-device to set it explicitly.",
            file=sys.stderr,
        )
        return 1

    playback_device = args.playback_device or f"plughw:{card_index},0"
    capture_device = args.capture_device or f"plughw:{card_index},0"

    print(
        textwrap.dedent(
            f"""
            =======================================
            Keyestudio ReSpeaker Audio Test Utility
            =======================================
            Detected ALSA card: {card_index}
            Playback device:    {playback_device}
            Capture device:     {capture_device}
            Sample rate:        {args.sample_rate} Hz
            """
        ).strip()
    )
    print("")
    print("Press Ctrl+C at any time to abort.\n")

    try:
        tone = generate_tone(
            frequency=args.tone_frequency,
            duration=args.tone_duration,
            sample_rate=args.sample_rate,
        )
        play_tone(playback_device, tone, args.sample_rate)
        record_and_playback(
            capture_device,
            playback_device,
            duration=args.record_duration,
            sample_rate=args.sample_rate,
            channels=args.channels,
        )
    except KeyboardInterrupt:
        print("\nAborted by user.")
        return 1
    except RuntimeError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1

    print("All tests completed.")
    print("If you heard both the tone and your recorded voice, the HAT is working.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
