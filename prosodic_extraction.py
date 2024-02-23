import argparse
import json
import parselmouth
from parselmouth.praat import call
import numpy as np
import pandas as pd
import platform # for OS detection

# needs a pip install py3-tts to work on macos ventura
import pyttsx3

import librosa

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

    engine = None 
    if platform.system() == 'Darwin':
        # specific driver for macos
        engine = pyttsx3.init(driverName='nsss')
    else:
        # use default driver for other OS
        engine = pyttsx3.init()
    sound = parselmouth.Sound(input_wav_file)

    prosodic_values = []

    pitch_obj = sound.to_pitch()

    for word in transcriptions:
        pitch = call(pitch_obj, "Get mean", word["start"], word["end"], "Hertz")
        sliced_audio = sound.extract_part(from_time=word["start"], to_time=word["end"])
        loudness = call(sliced_audio, "Get intensity (dB)")
        raw_duration = word["end"] - word["start"]
    
        engine.save_to_file(word["text"], 'temp.wav')
        engine.runAndWait()

        tts_duration = librosa.get_duration(path='temp.wav')
        if tts_duration == 0:
            duration = 0
        else:
            duration = raw_duration / tts_duration

        
        
        prosodic_values.append({
            'from_time': word["start"],
            'to_time': word["end"],
            'text': word["text"],
            'raw_loudness': loudness,
            'raw_pitch': pitch,
            'raw_duration': raw_duration,
            'ratio_duration': duration
        })

    clipping_distance = 2

    # interpolates missing values for loudness and pitch
    interpolated_loudness = pd.Series([prosodic_value['raw_loudness'] for prosodic_value in prosodic_values]).interpolate().tolist()
    interpolated_pitch = pd.Series([prosodic_value['raw_pitch'] for prosodic_value in prosodic_values]).interpolate().tolist()

    mean_loudness = np.mean(interpolated_loudness)
    std_dev_loudness = np.std(interpolated_loudness)
    max_loudness = mean_loudness + clipping_distance * std_dev_loudness
    min_loudness = mean_loudness - clipping_distance * std_dev_loudness

    mean_pitch = np.mean(interpolated_pitch)
    std_dev_pitch = np.std(interpolated_pitch)
    max_pitch = mean_pitch + clipping_distance * std_dev_pitch
    min_pitch = mean_pitch - clipping_distance * std_dev_pitch

    mean_duration = np.mean([prosodic_value['ratio_duration'] for prosodic_value in prosodic_values])
    std_dev_duration = np.std([prosodic_value['ratio_duration'] for prosodic_value in prosodic_values])
    max_duration = mean_duration + clipping_distance * std_dev_duration
    min_duration = mean_duration - clipping_distance * std_dev_duration

    # normalization
    for i, prosodic_value in enumerate(prosodic_values):
        if interpolated_loudness[i] > max_loudness:
            loudness = max_loudness
        elif interpolated_loudness[i] < min_loudness:
            loudness = min_loudness
        else:
            loudness = interpolated_loudness[i]
        prosodic_value['loudness'] = (loudness - min_loudness) / (max_loudness - min_loudness)
        
        if interpolated_pitch[i] > max_pitch:
            pitch = max_pitch
        elif interpolated_pitch[i] < min_pitch:
            pitch = min_pitch
        else:
            pitch = interpolated_pitch[i]
        prosodic_value['pitch'] = (pitch - min_pitch) / (max_pitch - min_pitch)
        
        if prosodic_value['ratio_duration'] > max_duration:
            duration = max_duration
        elif prosodic_value['ratio_duration'] < min_duration:
            duration = min_duration
        else:
            duration = prosodic_value['ratio_duration']
        prosodic_value['duration'] = (duration - min_duration) / (max_duration - min_duration)

    with open(output_json_file, 'w') as output_file:
        json.dump(prosodic_values, output_file, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract prosodic values from WAV file using JSON timestamps.")
    parser.add_argument("input_wav_file", help="Path to the input WAV file.")
    parser.add_argument("input_json_file", help="Path to the input JSON file with timestamped transcriptions.")
    parser.add_argument("output_json_file", help="Path to the output JSON file for saving prosodic values.")
    args = parser.parse_args()

    main(args.input_wav_file, args.input_json_file, args.output_json_file)
