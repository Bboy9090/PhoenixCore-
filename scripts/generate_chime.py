import math
import struct
import wave
import os

def generate_chime():
    sample_rate = 44100
    duration = 4.5  # 4.5 seconds majestic chime
    num_samples = int(sample_rate * duration)
    
    # 1. Resonant A-Major Golden Chime Frequencies
    # A1 (55Hz), A2 (110Hz), E3 (164.81Hz), A3 (220Hz), C#4 (277.18Hz), E4 (329.63Hz), A4 (440Hz), E5 (659.25Hz), A5 (880Hz)
    chime_freqs = [55.0, 110.0, 164.81, 220.0, 277.18, 329.63, 440.0, 659.25, 880.0]
    chime_weights = [0.35, 0.28, 0.22, 0.18, 0.14, 0.11, 0.09, 0.07, 0.05]
    
    # 2. Celestial Shimmer Sparkle Frequencies (High-pitched shimmers)
    shimmer_freqs = [1800.0, 2500.0, 3200.0, 4500.0, 6000.0]
    shimmer_weights = [0.03, 0.02, 0.02, 0.015, 0.01]
    
    wave_data = bytearray()
    
    # Let's track the phase of each oscillator continuously to prevent clicking
    # and support dynamic frequency modulation (FM) for the phoenix cry.
    phoenix_phase = 0.0
    phoenix_sub_phase = 0.0
    
    for i in range(num_samples):
        t = i / sample_rate
        sample_value_l = 0.0
        sample_value_r = 0.0
        
        # --- ENVELOPES ---
        # Chime: ultra-quick attack (0.15s), exponential decay
        if t < 0.15:
            chime_env = t / 0.15
        else:
            chime_env = math.exp(-1.8 * (t - 0.15))
            
        # Thunder: slow swell (0.5s), long rumble decay
        if t < 0.5:
            thunder_env = (t / 0.5) * 0.4
        else:
            thunder_env = 0.4 * math.exp(-0.8 * (t - 0.5))
            
        # Phoenix Cry: swells starting at 0.25s, peaks at 0.6s, dies off by 2.2s
        if t < 0.25:
            phoenix_env = 0.0
        elif t < 0.6:
            phoenix_env = ((t - 0.25) / 0.35) * 0.5
        elif t < 1.8:
            phoenix_env = 0.5 * math.exp(-1.5 * (t - 0.6))
        else:
            phoenix_env = 0.5 * math.exp(-1.5 * (1.8 - 0.6)) * max(0.0, 1.0 - (t - 1.8) / 0.4)
            
        # Celestial Shimmer: sparks up after the cry, peaks around 1.5s, decays slowly
        if t < 0.8:
            shimmer_env = (t / 0.8) * 0.15
        else:
            shimmer_env = 0.15 * math.exp(-1.2 * (t - 0.8))
            
        # --- SYNTHESIZE COMPONENTS ---
        
        # A) Ambient Thunder Roll & Deep Sub-Bass (35Hz & 42Hz)
        thunder_l = 0.45 * math.sin(2 * math.pi * 35.0 * t + 0.1 * math.sin(2 * math.pi * 12.0 * t))
        thunder_r = 0.45 * math.sin(2 * math.pi * 42.0 * t + 0.1 * math.cos(2 * math.pi * 12.0 * t))
        
        sample_value_l += thunder_l * thunder_env
        sample_value_r += thunder_r * thunder_env
        
        # B) Resonant Golden Chimes
        for freq, weight in zip(chime_freqs, chime_weights):
            phase_offset = freq * 0.05
            angle_l = 2 * math.pi * freq * t
            angle_r = 2 * math.pi * freq * t + phase_offset
            
            # Panning: bass in center, trebles panned out wide
            panning = min(0.9, (freq / 880.0) * 0.8)
            vol_l = weight * (1.0 - panning * 0.45)
            vol_r = weight * (1.0 + panning * 0.45)
            
            sample_value_l += vol_l * math.sin(angle_l) * chime_env
            sample_value_r += vol_r * math.sin(angle_r) * chime_env
            
        # C) Celestial Shimmer (resynthesizing magic high sparkles)
        for freq, weight in zip(shimmer_freqs, shimmer_weights):
            # Dynamic LFO modulation for shimmery chorus effect
            lfo = 1.0 + 0.05 * math.sin(2 * math.pi * 8.0 * t)
            angle_l = 2 * math.pi * (freq * lfo) * t
            angle_r = 2 * math.pi * (freq * lfo) * t + (freq * 0.1)
            
            sample_value_l += weight * math.sin(angle_l) * shimmer_env
            sample_value_r += weight * math.sin(angle_r) * shimmer_env
            
        # D) The Sovereign Phoenix Cry / Screech (Majestic FM Synthesis)
        # We sweep the frequency from a starting pitch (850Hz) up to a peak (1650Hz) and back.
        # Rapid vibrato/throat flutter is achieved by frequency modulating at 35Hz.
        if phoenix_env > 0.0:
            # 1. Base Sweep Pitch
            if t < 0.8:
                # Rising pitch sweep
                base_freq = 850.0 + (1650.0 - 850.0) * ((t - 0.25) / 0.55)
            else:
                # Swooping down pitch sweep
                base_freq = 1650.0 - (1650.0 - 680.0) * min(1.0, (t - 0.8) / 1.2)
                
            # 2. Throat vibrato frequency modulation (35Hz FM)
            vibrato = 90.0 * math.sin(2 * math.pi * 35.0 * t)
            freq_instant = base_freq + vibrato
            
            # Integrate frequency to get phase (prevents phase discontinuities/clicking)
            phoenix_phase += (2 * math.pi * freq_instant) / sample_rate
            
            # Rich harmonic timbre (add primary screech and a slightly offset secondary overtone for texture)
            primary_screech = math.sin(phoenix_phase)
            
            # Second overtone for shrieking thickness (1.47x frequency to mimic natural organic bird vocal cord friction)
            phoenix_sub_phase += (2 * math.pi * (freq_instant * 1.47)) / sample_rate
            secondary_screech = 0.65 * math.sin(phoenix_sub_phase)
            
            # Dynamic spatial panning: start center, fly to the left, then swoop right
            panning_factor = math.sin(math.pi * (t - 0.25) / 2.0)
            vol_cry_l = 0.5 * (1.0 - panning_factor * 0.6)
            vol_cry_r = 0.5 * (1.0 + panning_factor * 0.6)
            
            sample_value_l += (primary_screech + secondary_screech) * phoenix_env * vol_cry_l
            sample_value_r += (primary_screech + secondary_screech) * phoenix_env * vol_cry_r
            
        # --- FINAL MIX & CLIP PROTECTION ---
        sample_value_l = max(-1.0, min(1.0, sample_value_l)) * 0.35
        sample_value_r = max(-1.0, min(1.0, sample_value_r)) * 0.35
        
        # Convert to 16-bit signed PCM
        int_val_l = int(sample_value_l * 32767)
        int_val_r = int(sample_value_r * 32767)
        
        wave_data.extend(struct.pack("<hh", int_val_l, int_val_r))
        
    # Ensure branding folders exist
    os.makedirs("os/phoenix-os/branding/sounds", exist_ok=True)
    out_path = "os/phoenix-os/branding/sounds/startup.wav"
    
    with wave.open(out_path, "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data)
        
    print(f"✨ Synthesized premium ambient startup chime with Phoenix Cry at {out_path}")

if __name__ == "__main__":
    generate_chime()

