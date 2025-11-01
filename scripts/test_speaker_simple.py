#!/usr/bin/env python3
"""
ReSpeaker Audio Test
Generate a simple tone to test speaker
"""

import numpy as np
import struct
import subprocess
import sys

def generate_tone(frequency=440, duration=2, sample_rate=16000):
    """Generate a sine wave tone"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(frequency * 2 * np.pi * t)
    
    # Scale to 16-bit PCM
    audio = (wave * 32767).astype(np.int16)
    
    return audio.tobytes()

def main():
    print("=" * 50)
    print("ReSpeaker Speaker Test")
    print("=" * 50)
    print("\nGenerating 440Hz tone for 2 seconds...")
    print("Listen for a beep from your speaker!\n")
    
    # Generate tone
    audio_data = generate_tone(frequency=440, duration=2, sample_rate=16000)
    
    # Play using aplay
    cmd = [
        'aplay',
        '-D', 'plughw:0,0',  # ReSpeaker device
        '-f', 'S16_LE',       # 16-bit signed little endian
        '-r', '16000',        # 16kHz sample rate
        '-c', '1'             # Mono
    ]
    
    print(f"Playing audio with: {' '.join(cmd)}")
    
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        proc.communicate(input=audio_data)
        proc.wait()
        
        if proc.returncode == 0:
            print("\n✓ Audio sent to speaker successfully!")
            print("\nDid you hear the beep? (y/n): ", end='')
            sys.stdout.flush()
        else:
            print(f"\n❌ Error playing audio (exit code {proc.returncode})")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
