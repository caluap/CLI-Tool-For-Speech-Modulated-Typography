import argparse
import soundfile as sf
import json

# Function to load the WAV file
def load_wav(wav_file_path):
    audio_signal, sampling_rate = sf.read(wav_file_path)
    return audio_signal, sampling_rate

# Function to extract the relevant audio segment
def extract_audio_segment(audio_signal, sampling_rate, from_offset, to_offset):
    from_sample = int(from_offset / 1000 * sampling_rate)
    to_sample = int(to_offset / 1000 * sampling_rate)
    
    print(from_sample, to_sample)
    # Check if the audio segment has a valid length
    if from_sample >= len(audio_signal):
        return None
    
    # Adjust to_sample if it exceeds the length of the audio signal
    if to_sample >= len(audio_signal):
        to_sample = len(audio_signal) - 1
    
    audio_segment = audio_signal[from_sample:to_sample]
    return audio_segment

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
def extract_affective_avlues(wav_file_path, json_file_path):
    audio_signal, sampling_rate = load_wav(wav_file_path)
    transcriptions = process_json(json_file_path)

    affective_values = []
    for from_time, to_time, from_offset, to_offset, text in transcriptions:
        audio_segment = extract_audio_segment(audio_signal, sampling_rate, from_offset, to_offset)
        print(audio_segment)
        if audio_segment is None:
            continue;  # Skip processing invalid audio segments
        affective_values.append({
            'from_time': from_time,
            'to_time': to_time,
            'text': text,
            'affective_values': None
        })
        print(len(affective_values))

    return affective_values


def main(input_wav_file, input_json_file, output_json_file):
    affective_values = extract_affective_avlues(input_wav_file, input_json_file)

    with open(output_json_file, 'w') as output_file:
        json.dump(affective_values, output_file, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract prosodic values from WAV file using JSON timestamps.")
    parser.add_argument("input_wav_file", help="Path to the input WAV file.")
    parser.add_argument("input_json_file", help="Path to the input JSON file with timestamped transcriptions.")
    parser.add_argument("output_json_file", help="Path to the output JSON file for saving prosodic values.")
    args = parser.parse_args()

    main(args.input_wav_file, args.input_json_file, args.output_json_file)
