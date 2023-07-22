import argparse
import librosa
import json
import pyworld as pw
import numpy as np

# Function to load the WAV file
def load_wav(wav_file_path):
    audio_signal, sampling_rate = librosa.load(wav_file_path, sr=None)
    return audio_signal, sampling_rate

# Function to extract the relevant audio segment
def extract_audio_segment(audio_signal, sampling_rate, from_offset, to_offset):
    from_sample = int(from_offset * sampling_rate)
    to_sample = int(to_offset * sampling_rate)
    
    # Check if the audio segment has a valid length
    if from_sample >= len(audio_signal) or to_sample <= from_sample:
        return None
    
    # Adjust to_sample if it exceeds the length of the audio signal
    if to_sample >= len(audio_signal):
        to_sample = len(audio_signal) - 1
    
    audio_segment = audio_signal[from_sample:to_sample]
    return audio_segment

# Function to calculate RMS energy
def calculate_rms_energy(audio_segment):
    # Check if the audio_segment is valid (not empty)
    if len(audio_segment) == 0:
        return None

    rms_energy = librosa.feature.rms(y=audio_segment)[0]
    return rms_energy

# Function to calculate MFCC energy
def calculate_mfcc_energy(audio_segment, sampling_rate, n_mfcc=13):
    mfccs = librosa.feature.mfcc(y=audio_segment, sr=sampling_rate, n_mfcc=n_mfcc)
    energy = mfccs[0]
    return energy

# Function to calculate the average pitch frequency for vowel segments
def calculate_average_pitch(audio_segment, sampling_rate):
    # Convert audio_segment to double (64-bit) data type
    audio_segment = audio_segment.astype(np.float64)

    # Ensure the audio segment is non-empty and has a length greater than the FFT size
    n_fft = 2048  # Adjust the value of n_fft based on your needs
    if len(audio_segment) > 0 and len(audio_segment) >= n_fft:
        f0, t = pw.dio(audio_segment, sampling_rate, f0_floor=50.0)  # Set f0_floor to a suitable value
        if len(f0) > 0:
            f0 = pw.stonemask(audio_segment, f0, t, sampling_rate)
            average_pitch = np.mean(f0[f0 > 0])
        else:
            average_pitch = 0.0  # Set average pitch to 0 if no valid F0 points are found
    else:
        average_pitch = 0.0  # Set average pitch to 0 for empty or very short audio segments

    return average_pitch

# Updated function to read and process the JSON data with an array of elements
def process_json(json_file_path):
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    transcriptions = []
    for item in data:
        from_time = item['timestamps']['from']
        to_time = item['timestamps']['to']
        from_offset = item['offsets']['from']
        to_offset = item['offsets']['to']
        text = item['text']

        transcriptions.append((from_time, to_time, from_offset, to_offset, text))

    return transcriptions

# Updated function to extract prosodic values from multiple timestamped transcriptions
def extract_prosodic_values(wav_file_path, json_file_path):
    audio_signal, sampling_rate = load_wav(wav_file_path)
    transcriptions = process_json(json_file_path)

    prosodic_values = []
    for from_time, to_time, from_offset, to_offset, text in transcriptions:
        audio_segment = extract_audio_segment(audio_signal, sampling_rate, from_offset, to_offset)
        if audio_segment is None:
          continue  # Skip processing invalid audio segments
        rms_energy = calculate_rms_energy(audio_segment)
        mfcc_energy = calculate_mfcc_energy(audio_segment, sampling_rate)
        # average_pitch = calculate_average_pitch(audio_segment, sampling_rate)

        prosodic_values.append({
            'from_time': from_time,
            'to_time': to_time,
            'text': text,
            'prosodic_values': {
                'rms_energy': rms_energy.tolist(),
                'mfcc_energy': mfcc_energy.tolist(),
                # 'average_pitch': average_pitch
            }
        })

    return prosodic_values


def main(input_wav_file, input_json_file, output_json_file):
    audio_signal, sampling_rate = load_wav(input_wav_file)
    transcriptions = process_json(input_json_file)

    prosodic_values = []
    for from_time, to_time, from_offset, to_offset, text in transcriptions:
        audio_segment = extract_audio_segment(audio_signal, sampling_rate, from_offset, to_offset)
        rms_energy = calculate_rms_energy(audio_segment)
        mfcc_energy = calculate_mfcc_energy(audio_segment, sampling_rate)
        average_pitch = calculate_average_pitch(audio_segment, sampling_rate)

        prosodic_values.append({
            'from_time': from_time,
            'to_time': to_time,
            'text': text,
            'prosodic_values': {
                'rms_energy': rms_energy.tolist(),
                'mfcc_energy': mfcc_energy.tolist(),
                'average_pitch': average_pitch
            }
        })

    with open(output_json_file, 'w') as output_file:
        json.dump(prosodic_values, output_file, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract prosodic values from WAV file using JSON timestamps.")
    parser.add_argument("input_wav_file", help="Path to the input WAV file.")
    parser.add_argument("input_json_file", help="Path to the input JSON file with timestamped transcriptions.")
    parser.add_argument("output_json_file", help="Path to the output JSON file for saving prosodic values.")
    args = parser.parse_args()

    main(args.input_wav_file, args.input_json_file, args.output_json_file)
