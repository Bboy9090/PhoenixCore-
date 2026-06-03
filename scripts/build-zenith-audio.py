import os
import wave
import math
import struct

repo_editions = "/Users/bj90-m1/PhoenixCore-/editions"

# Map editions to acoustic "styles"
editions = {
    "Aurelia": "ethereal",    # Celestial, smooth, chorused
    "Arcwyre": "gritty",      # Cyberpunk, square-wave, fast
    "Thundergod": "punchy",   # Lightning, sharp attack, delay
    "Native": "warm"          # Classic, deep, resonant
}

files = [
    "desktop-login.wav",
    "desktop-logout.wav",
    "dialog-error.wav",
    "dialog-information.wav",
    "message.wav",
    "device-added.wav",
    "device-removed.wav",
    "battery-low.wav",
    "trash-empty.wav"
]

def synthesize_wave(style, duration_ms, base_freq, is_chord=False):
    """
    Synthesize a 16-bit 44.1kHz wave bytearray based on the aesthetic style.
    """
    sample_rate = 44100
    num_samples = int(sample_rate * (duration_ms / 1000.0))
    audio_data = bytearray()
    
    # Simple ADSR envelope parameters based on style
    if style == "ethereal":
        attack = 0.3
        decay = 0.5
        sustain = 0.8
        release = 0.4
    elif style == "gritty":
        attack = 0.05
        decay = 0.2
        sustain = 0.5
        release = 0.1
    elif style == "punchy":
        attack = 0.01
        decay = 0.3
        sustain = 0.2
        release = 0.2
    else: # warm
        attack = 0.1
        decay = 0.3
        sustain = 0.6
        release = 0.3
        
    for i in range(num_samples):
        t = float(i) / sample_rate
        progress = i / float(num_samples)
        
        # Envelope calculation (simplified)
        if progress < attack:
            env = progress / attack
        elif progress < (attack + decay):
            env = 1.0 - (1.0 - sustain) * ((progress - attack) / decay)
        elif progress > (1.0 - release):
            env = sustain * (1.0 - (progress - (1.0 - release)) / release)
        else:
            env = sustain
            
        # Oscillator
        if style == "ethereal":
            # Sine wave with subtle chorus (detuned oscillator)
            val = math.sin(2 * math.pi * base_freq * t) + 0.5 * math.sin(2 * math.pi * (base_freq * 1.01) * t)
            if is_chord:
                val += 0.8 * math.sin(2 * math.pi * (base_freq * 1.5) * t) # Perfect fifth
            val /= (1.5 if not is_chord else 2.3)
        elif style == "gritty":
            # Square-like wave using harsh harmonics
            val = sum(math.sin(2 * math.pi * base_freq * k * t) / k for k in [1, 3, 5])
            if is_chord:
                val += 0.8 * sum(math.sin(2 * math.pi * (base_freq * 1.25) * k * t) / k for k in [1, 3]) # Major third
        elif style == "punchy":
            # Sawtooth-like wave with sharp attack frequency mod
            fm = math.exp(-t * 10) * base_freq * 2
            val = sum(math.sin(2 * math.pi * (base_freq + fm) * k * t) / k for k in range(1, 4))
            if is_chord:
                val += 0.5 * math.sin(2 * math.pi * (base_freq * 2) * t) # Octave
        else: # warm
            # Triangle-like wave
            val = sum(((-1)**k) * math.sin(2 * math.pi * base_freq * (2*k+1) * t) / ((2*k+1)**2) for k in range(3))
            if is_chord:
                val += 0.7 * sum(((-1)**k) * math.sin(2 * math.pi * (base_freq * 1.25) * (2*k+1) * t) / ((2*k+1)**2) for k in range(2))

        # Scale and clip
        sample = int(env * val * 32767 * 0.7) # 70% master volume
        sample = max(-32768, min(32767, sample))
        
        audio_data.extend(struct.pack('<h', sample)) # Little endian 16-bit
        
    return audio_data

def generate_sound(path, style, event_type):
    """
    Map event types to frequencies and durations, then write the WAV file.
    """
    if event_type == "desktop-login.wav":
        freq, dur, chord = (440, 2000, True) # A4, long, chord
    elif event_type == "desktop-logout.wav":
        freq, dur, chord = (220, 1500, True) # A3, medium, chord
    elif event_type == "dialog-error.wav":
        freq, dur, chord = (150, 400, False) # Low beep
    elif event_type == "dialog-information.wav" or event_type == "message.wav":
        freq, dur, chord = (880, 300, False) # High ping
    elif event_type == "device-added.wav":
        freq, dur, chord = (660, 500, True)  # Ascending feel (simulated by chord)
    elif event_type == "device-removed.wav":
        freq, dur, chord = (330, 500, True)  # Descending feel
    else:
        freq, dur, chord = (440, 400, False) # Default

    audio_data = synthesize_wave(style, dur, freq, chord)
    
    with wave.open(path, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes = 16 bit
        wav_file.setframerate(44100)
        wav_file.writeframes(audio_data)

def main():
    folder_map = {
        "Aurelia": "home",
        "Arcwyre": "arcwyre",
        "Thundergod": "thunder-god",
        "Native": "blue-phoenix"
    }
    
    for name, style in editions.items():
        folder = folder_map[name]
        sound_dir = os.path.join(repo_editions, folder, "custom_sounds")
        
        if not os.path.exists(sound_dir):
            os.makedirs(sound_dir)
            
        print(f"🎵 Synthesizing {style} audio palette for {name}...")
        for f in files:
            path = os.path.join(sound_dir, f)
            generate_sound(path, style, f)
            
        print(f"✅ Generated {len(files)} tracks in {folder}/custom_sounds")

if __name__ == "__main__":
    main()
