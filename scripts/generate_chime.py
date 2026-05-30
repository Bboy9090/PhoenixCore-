import math
import struct
import wave

def generate_chime():
    sample_rate = 44100
    duration = 4.0  # 4 seconds chime
    num_samples = int(sample_rate * duration)
    
    # Define A major chord / ambient notes:
    # A1 (55Hz), A2 (110Hz), E3 (164.81Hz), A3 (220Hz), C#4 (277.18Hz), E4 (329.63Hz), A4 (440Hz)
    frequencies = [55.0, 110.0, 164.81, 220.0, 277.18, 329.63, 440.0]
    # Amplitudes/weights for each frequency to create a rich, balanced ambient sound
    weights = [0.35, 0.25, 0.20, 0.15, 0.12, 0.10, 0.08]
    
    # Wave data list
    wave_data = bytearray()
    
    for i in range(num_samples):
        t = i / sample_rate
        sample_value_l = 0.0
        sample_value_r = 0.0
        
        # Elegant smooth envelope: quick attack (0.2s), slow exponential decay
        if t < 0.2:
            envelope = t / 0.2
        else:
            envelope = math.exp(-2.0 * (t - 0.2))
            
        # Synthesize notes
        for freq, weight in zip(frequencies, weights):
            # Add subtle phase offsets for spatial depth
            phase_offset = freq * 0.1
            angle_l = 2 * math.pi * freq * t
            angle_r = 2 * math.pi * freq * t + phase_offset
            
            # Sub-bass frequencies center, higher frequencies expand to stereo sides
            panning = min(1.0, (freq / 440.0) * 0.8)
            vol_l = weight * (1.0 - panning * 0.5)
            vol_r = weight * (1.0 + panning * 0.5)
            
            sample_value_l += vol_l * math.sin(angle_l)
            sample_value_r += vol_r * math.sin(angle_r)
            
        # Normalize and scale
        sample_value_l = max(-1.0, min(1.0, sample_value_l)) * envelope * 0.4
        sample_value_r = max(-1.0, min(1.0, sample_value_r)) * envelope * 0.4
        
        # Convert to 16-bit integer (-32768 to 32767)
        int_val_l = int(sample_value_l * 32767)
        int_val_r = int(sample_value_r * 32767)
        
        wave_data.extend(struct.pack("<hh", int_val_l, int_val_r))
        
    # Write to WAV file
    out_path = "os/phoenix-os/branding/sounds/startup.wav"
    with wave.open(out_path, "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data)
        
    print(f"✨ Synthesized premium ambient startup chime at {out_path}")

if __name__ == "__main__":
    generate_chime()
