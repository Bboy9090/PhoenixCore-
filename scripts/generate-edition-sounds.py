#!/usr/bin/env python3
import os
import shutil
import numpy as np
from scipy.io import wavfile
import scipy.signal as signal

SAMPLE_RATE = 44100

def generate_wave(wave_type, freq, duration, amplitude=1.0):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    if wave_type == 'sine':
        audio = amplitude * np.sin(2 * np.pi * freq * t)
    elif wave_type == 'saw':
        audio = amplitude * signal.sawtooth(2 * np.pi * freq * t)
    elif wave_type == 'square':
        audio = amplitude * signal.square(2 * np.pi * freq * t)
    elif wave_type == 'noise':
        audio = amplitude * np.random.uniform(-1, 1, len(t))
    else:
        audio = np.zeros_like(t)
    return audio

def apply_envelope(audio, attack, decay, sustain, release):
    total_len = len(audio)
    a_len = int(attack * SAMPLE_RATE)
    d_len = int(decay * SAMPLE_RATE)
    r_len = int(release * SAMPLE_RATE)
    s_len = total_len - a_len - d_len - r_len
    
    if s_len < 0:
        # Scale envelope if it exceeds audio duration
        scale = total_len / (a_len + d_len + r_len)
        a_len = int(a_len * scale)
        d_len = int(d_len * scale)
        r_len = total_len - a_len - d_len
        s_len = 0
        sustain = 0

    env = np.concatenate([
        np.linspace(0, 1, a_len),
        np.linspace(1, sustain, d_len),
        np.full(s_len, sustain),
        np.linspace(sustain, 0, r_len)
    ])
    return audio * env

def lowpass_filter(audio, cutoff, order=4):
    nyq = 0.5 * SAMPLE_RATE
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return signal.lfilter(b, a, audio)

def bitcrush(audio, bits, sample_rate_reduction):
    # Reduce bit depth
    steps = 2 ** bits
    audio_crushed = np.round(audio * steps) / steps
    
    # Reduce sample rate
    if sample_rate_reduction > 1:
        for i in range(0, len(audio_crushed), sample_rate_reduction):
            audio_crushed[i:i+sample_rate_reduction] = audio_crushed[i]
            
    return audio_crushed

def mix(*audios):
    max_len = max(len(a) for a in audios)
    mixed = np.zeros(max_len)
    for a in audios:
        mixed[:len(a)] += a
    # Normalize to avoid clipping
    if np.max(np.abs(mixed)) > 1.0:
        mixed = mixed / np.max(np.abs(mixed))
    return mixed

def save_wav(filename, audio):
    # Ensure float32 between -1 and 1
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = np.int16(audio * 32767)
    wavfile.write(filename, SAMPLE_RATE, audio_int16)

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# --- EDITION SOUND GENERATORS ---

def generate_aurelia(out_dir):
    ensure_dir(out_dir)
    print("Generating Aurelia (Celestial Chimes)...")
    
    # Login: Shimmering ascending chime
    w1 = apply_envelope(generate_wave('sine', 523.25, 3.0), 0.1, 0.5, 0.6, 2.0) # C5
    w2 = apply_envelope(generate_wave('sine', 659.25, 3.0), 0.2, 0.5, 0.5, 2.0) # E5
    w3 = apply_envelope(generate_wave('sine', 783.99, 3.0), 0.3, 0.5, 0.4, 2.0) # G5
    w4 = apply_envelope(generate_wave('sine', 1046.50, 3.0, 0.5), 0.5, 0.5, 0.3, 2.0) # C6
    save_wav(f"{out_dir}/desktop-login.wav", mix(w1, w2, w3, w4))
    
    # Logout: Descending soft chime
    w1 = apply_envelope(generate_wave('sine', 783.99, 2.0), 0.1, 0.4, 0.4, 1.5)
    w2 = apply_envelope(generate_wave('sine', 523.25, 2.0), 0.3, 0.4, 0.3, 1.0)
    save_wav(f"{out_dir}/desktop-logout.wav", mix(w1, w2))
    
    # Notification: Quick bright ping
    w1 = apply_envelope(generate_wave('sine', 1046.50, 0.8), 0.02, 0.1, 0.1, 0.5)
    save_wav(f"{out_dir}/message.wav", w1)
    
    # Error: Dissonant soft chime
    w1 = apply_envelope(generate_wave('sine', 440.0, 1.0), 0.05, 0.2, 0.2, 0.5)
    w2 = apply_envelope(generate_wave('sine', 466.16, 1.0), 0.05, 0.2, 0.2, 0.5)
    save_wav(f"{out_dir}/dialog-error.wav", mix(w1, w2))

def generate_arcwyre(out_dir):
    ensure_dir(out_dir)
    print("Generating Arcwyre (Cyber Storm Crackle)...")
    
    # Login: Aggressive sweep and bitcrushed chord
    w1 = apply_envelope(generate_wave('saw', 110.0, 2.0), 0.05, 0.5, 0.5, 1.0)
    w2 = apply_envelope(generate_wave('saw', 164.81, 2.0), 0.05, 0.5, 0.5, 1.0)
    crushed = bitcrush(mix(w1, w2), bits=6, sample_rate_reduction=4)
    noise = lowpass_filter(apply_envelope(generate_wave('noise', 0, 1.0, 0.3), 0.05, 0.2, 0, 0.5), 2000)
    save_wav(f"{out_dir}/desktop-login.wav", mix(crushed, noise))
    
    # Logout: Short glitch
    w1 = apply_envelope(generate_wave('saw', 55.0, 1.0), 0.05, 0.1, 0.1, 0.5)
    crushed = bitcrush(w1, bits=4, sample_rate_reduction=8)
    save_wav(f"{out_dir}/desktop-logout.wav", crushed)
    
    # Notification: Digital glitch
    w1 = apply_envelope(generate_wave('square', 880.0, 0.3), 0.01, 0.05, 0, 0.1)
    w2 = apply_envelope(generate_wave('square', 1760.0, 0.3, 0.5), 0.05, 0.05, 0, 0.1)
    save_wav(f"{out_dir}/message.wav", mix(w1, w2))
    
    # Error: Harsh digital buzz
    w1 = bitcrush(apply_envelope(generate_wave('saw', 55.0, 0.5), 0.01, 0.1, 0.2, 0.2), 4, 8)
    save_wav(f"{out_dir}/dialog-error.wav", w1)

def generate_thundergod(out_dir):
    ensure_dir(out_dir)
    print("Generating Thundergod (Thunder Strike)...")
    
    # Login: Massive bass drop and thunder noise
    t = np.linspace(0, 3.0, int(SAMPLE_RATE * 3.0), endpoint=False)
    freq_sweep = np.linspace(150, 30, len(t))
    bass = np.sin(2 * np.pi * freq_sweep * t)
    bass = apply_envelope(bass, 0.05, 1.0, 0.2, 1.5)
    
    noise = generate_wave('noise', 0, 3.0, 0.8)
    noise_filtered = lowpass_filter(noise, 800)
    noise_env = apply_envelope(noise_filtered, 0.01, 0.5, 0.1, 2.0)
    
    save_wav(f"{out_dir}/desktop-login.wav", mix(bass, noise_env))
    
    # Logout: Short rumble
    noise = generate_wave('noise', 0, 1.5, 0.6)
    noise_filtered = lowpass_filter(noise, 400)
    noise_env = apply_envelope(noise_filtered, 0.05, 0.5, 0, 1.0)
    save_wav(f"{out_dir}/desktop-logout.wav", noise_env)
    
    # Notification: Sharp crack
    noise = generate_wave('noise', 0, 0.5)
    crack = lowpass_filter(apply_envelope(noise, 0.01, 0.1, 0, 0.2), 3000)
    save_wav(f"{out_dir}/message.wav", crack)
    
    # Error: Low rumble
    rumble = lowpass_filter(apply_envelope(generate_wave('noise', 0, 1.0), 0.1, 0.3, 0, 0.5), 200)
    save_wav(f"{out_dir}/dialog-error.wav", rumble)

def generate_native(out_dir):
    ensure_dir(out_dir)
    print("Generating Native (Cosmic Surge)...")
    
    # Login: Deep drone with slow attack
    w1 = apply_envelope(generate_wave('sine', 65.41, 4.0), 1.0, 1.0, 0.8, 2.0) # C2
    w2 = apply_envelope(generate_wave('sine', 98.00, 4.0, 0.5), 1.5, 1.0, 0.6, 2.0) # G2
    w3 = apply_envelope(generate_wave('sine', 130.81, 4.0, 0.3), 2.0, 1.0, 0.4, 2.0) # C3
    
    mix_audio = mix(w1, w2, w3)
    mix_audio = lowpass_filter(mix_audio, 400)
    save_wav(f"{out_dir}/desktop-login.wav", mix_audio)
    
    # Logout: Deep descending pulse
    w1 = apply_envelope(generate_wave('sine', 98.00, 2.0), 0.5, 0.5, 0.4, 1.0)
    save_wav(f"{out_dir}/desktop-logout.wav", lowpass_filter(w1, 300))
    
    # Notification: Resonant low pulse
    w1 = apply_envelope(generate_wave('sine', 130.81, 1.0), 0.2, 0.3, 0, 0.5)
    save_wav(f"{out_dir}/message.wav", lowpass_filter(w1, 600))
    
    # Error: Dissonant low hum
    w1 = apply_envelope(generate_wave('saw', 60.0, 1.5), 0.2, 0.5, 0.5, 0.5)
    w2 = apply_envelope(generate_wave('saw', 63.0, 1.5), 0.2, 0.5, 0.5, 0.5)
    save_wav(f"{out_dir}/dialog-error.wav", lowpass_filter(mix(w1, w2), 300))

if __name__ == "__main__":
    editions_dir = "/Users/bj90-m1/PhoenixCore-/editions"
    
    generate_aurelia(os.path.join(editions_dir, "aurelia", "custom_sounds"))
    generate_arcwyre(os.path.join(editions_dir, "arcwyre", "custom_sounds"))
    generate_thundergod(os.path.join(editions_dir, "thunder-god", "custom_sounds"))
    generate_native(os.path.join(editions_dir, "native", "custom_sounds"))
    
    # Generate identical aliases for the base events required by FreeDesktop
    for variant in ["aurelia", "arcwyre", "thunder-god", "native"]:
        sd = os.path.join(editions_dir, variant, "custom_sounds")
        
        # Aliases
        if os.path.exists(f"{sd}/message.wav"):
            shutil.copy2(f"{sd}/message.wav", f"{sd}/dialog-information.wav")
            shutil.copy2(f"{sd}/message.wav", f"{sd}/device-added.wav")
            shutil.copy2(f"{sd}/message.wav", f"{sd}/device-removed.wav")
        if os.path.exists(f"{sd}/dialog-error.wav"):
            shutil.copy2(f"{sd}/dialog-error.wav", f"{sd}/battery-low.wav")
        if os.path.exists(f"{sd}/desktop-logout.wav"):
            shutil.copy2(f"{sd}/desktop-logout.wav", f"{sd}/trash-empty.wav")
            
    print("All procedural edition sounds generated successfully!")
