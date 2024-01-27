import argparse
import json
import parselmouth
from parselmouth.praat import call

praat_executable = "/Applications/Praat.app/Contents/MacOS/Praat"
praat_script = "./syllablenuclei_v3.praat"


# Updated function to read and process the JSON data with an array of elements
def process_json(json_file_path):
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    transcriptions = []

    for segment in data["segments"]:
        for word in segment["words"]:
            transcriptions.append({
                "text": word["text"],
                "start": word["start"],
                "end": word["end"]
            })

    return transcriptions

def main(input_wav_file, input_json_file, output_json_file):
    transcriptions = process_json(input_json_file)

    sound = parselmouth.Sound(input_wav_file)

    prosodic_values = []

    pitch_obj = sound.to_pitch()

    max_pitch = -1
    min_pitch = float("inf")
    max_loud = -1
    min_loud = float("inf")

    for word in transcriptions:
        pitch = call(pitch_obj, "Get mean", word["start"], word["end"], "Hertz")
        sliced_audio = sound.extract_part(from_time=word["start"], to_time=word["end"])
        loudness = call(sliced_audio, "Get intensity (dB)")

        if pitch > max_pitch:
            max_pitch = pitch
        if pitch < min_pitch:
            min_pitch = pitch
        if loudness > max_loud:
            max_loud = loudness
        if loudness < min_loud:
            min_loud = loudness
        
        prosodic_values.append({
            'from_time': word["start"],
            'to_time': word["end"],
            'text': word["text"],
            'raw_loudness': loudness,
            'raw_pitch': pitch,
            'rhythm': 'todo'
        })

    for prosodic_value in prosodic_values:
        prosodic_value['loudness'] = (prosodic_value['raw_loudness'] - min_loud) / (max_loud - min_loud)
        prosodic_value['pitch'] = (prosodic_value['raw_pitch'] - min_pitch) / (max_pitch - min_pitch)

    with open(output_json_file, 'w') as output_file:
        json.dump(prosodic_values, output_file, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract prosodic values from WAV file using JSON timestamps.")
    parser.add_argument("input_wav_file", help="Path to the input WAV file.")
    parser.add_argument("input_json_file", help="Path to the input JSON file with timestamped transcriptions.")
    parser.add_argument("output_json_file", help="Path to the output JSON file for saving prosodic values.")
    args = parser.parse_args()

    main(args.input_wav_file, args.input_json_file, args.output_json_file)
