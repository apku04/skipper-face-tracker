#!/usr/bin/env python3
"""
ReSpeaker Audio Test with Volume Control
Generate tone with adjustable volume
"""

import numpy as np
import subprocess
import sys

def generate_tone(frequency=440, duration=2, sample_rate=16000, volume=1.0):
    """
    Generate a sine wave tone
    
    Args:
        frequency: Tone frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        volume: Volume multiplier (0.0 to 2.0, where 1.0 is 100%)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(frequency * 2 * np.pi * t)
    
    # Apply volume (clamp to prevent distortion)
    wave = wave * volume
    wave = np.clip(wave, -1.0, 1.0)
    
    # Scale to 16-bit PCM
    audio = (wave * 32767).astype(np.int16)
    
    return audio.tobytes()

def main():
    print("=" * 50)
    print("ReSpeaker Volume Test")
    print("=" * 50)
    
    # Test at different volume levels
    volumes = [0.5, 1.0, 1.5, 2.0]
    
    for vol in volumes:
        print(f"\n{'='*50}")
        print(f"Testing at {int(vol * 100)}% volume...")
        print(f"{'='*50}")
        print("Listen for the tone...")
        
        # Generate tone at current volume
        audio_data = generate_tone(frequency=440, duration=1.5, sample_rate=16000, volume=vol)
        
        # Play using aplay
        cmd = [
            'aplay',
            '-D', 'plughw:0,0',
            '-f', 'S16_LE',
            '-r', '16000',
            '-c', '1'
        ]
        
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.communicate(input=audio_data)
            proc.wait()
            
            if proc.returncode != 0:
                print(f"❌ Error playing audio")
                continue
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    print("\n" + "=" * 50)
    print("Which volume level sounded best?")
    print("  50%  - Safe, no distortion")
    print("  100% - Standard volume")
    print("  150% - Louder (may distort)")
    print("  200% - Maximum (likely distorts)")
    print("=" * 50)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
