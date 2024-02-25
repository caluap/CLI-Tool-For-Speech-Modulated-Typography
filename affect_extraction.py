import argparse
import soundfile as sf
import json

import os
import audeer
import audonnx
import numpy as np
import audinterface

w2v2path = "/Users/calua/google_drive/pessoal/estudo/doutorado/Research/study2__prosody+emotion/video_selection/"
# check if w2v2path is a valid path, if not set to current directory
if not os.path.exists(w2v2path):
    w2v2path = os.getcwd() + os.pathsep

model_root = w2v2path + "audeer/model"
cache_root = w2v2path + "audeer/cache"
# model = None
# signal = None
interface = None

class NumpyFloatValuesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.float32):
            return float(obj)
        return JSONEncoder.default(self, obj)

def load_model():
    global interface
    audeer.mkdir(cache_root)

    url = 'https://zenodo.org/record/6221127/files/w2v2-L-robust-12.6bc4a7fd-1.1.0.zip'
    dst_path = os.path.join(cache_root, 'model.zip')

    if not os.path.exists(dst_path):
        audeer.download_url(
            url, 
            dst_path, 
            verbose=True,
        )
        
    if not os.path.exists(model_root):
        audeer.extract_archive(
            dst_path, 
            model_root, 
            verbose=True,
        )

    model = audonnx.load(model_root)
    np.random.seed(0)

    sampling_rate = 16000
    signal = np.random.normal(
        size=sampling_rate,
    ).astype(np.float32)

    model(signal, sampling_rate)

    interface = audinterface.Feature(
        model.outputs['logits'].labels,
        process_func=model,
        process_func_args={
            'output_names': 'logits',
        },
        sampling_rate=sampling_rate,
        resample=True,
        verbose=True,
    )

    t = interface.process_signal(signal, sampling_rate)
    print(t)


# Function to load the WAV file
def load_wav(wav_file_path):
    audio_signal, sampling_rate = sf.read(wav_file_path)
    return audio_signal, sampling_rate

# Function to extract the relevant audio segment
def extract_audio_segment(audio_signal, sampling_rate, from_offset, to_offset):
    
    # Check if the audio segment has a valid length
    if from_offset >= len(audio_signal):
        return None
    
    # Adjust to_sample if it exceeds the length of the audio signal
    if to_offset >= len(audio_signal):
        to_offset = len(audio_signal) - 1
    
    audio_segment = audio_signal[from_offset:to_offset]
    return audio_segment

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

# Updated function to extract prosodic values from multiple timestamped transcriptions
def extract_affective_values(wav_file_path, json_file_path):
    global interface

    audio_signal, sampling_rate = load_wav(wav_file_path)
    np_wav = np.array(audio_signal,dtype=np.float32)
    transcriptions = process_json(json_file_path)

    affective_values = []
    window_size = 6
    desired_duration = window_size * sampling_rate

    for word in transcriptions:
        print(word)
        sample_from = int(word["start"] * sampling_rate)
        sample_to = int(word["end"] * sampling_rate)
        word_duration = sample_to - sample_from
        offset = (desired_duration - word_duration) / 2

        start = int(max(0, sample_from - offset))
        end = int(min(len(np_wav), sample_to + offset))

        audio_segment = extract_audio_segment(np_wav, sampling_rate, start, end)

        if audio_segment is None:
            continue;  # Skip processing invalid audio segments
        
        try:
            output = interface.process_signal(np_wav[start:end], sampling_rate)
        except Exception as error:
            valence = None
            arousal = None
            dominance = None
            print(error)
        else:
            valence = output["valence"][0]
            arousal = output["arousal"][0]
            dominance = output["dominance"][0]

        affective_values.append({
            'from_time': word["start"],
            'to_time': word["end"],
            'text': word["text"],
            'pred_valence': valence,
            'pred_arousal': arousal,
            'pred_dominance': dominance,
        })

    return affective_values


def main(input_wav_file, input_json_file, output_json_file):
    load_model()
    affective_values = extract_affective_values(input_wav_file, input_json_file)

    f = json.dumps(affective_values, cls=NumpyFloatValuesEncoder,
                   separators=(',',':'),
                   sort_keys=True,
                   indent=4)

    with open(output_json_file, 'w') as text_file:
        text_file.write(f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract prosodic values from WAV file using JSON timestamps.")
    parser.add_argument("input_wav_file", help="Path to the input WAV file.")
    parser.add_argument("input_json_file", help="Path to the input JSON file with timestamped transcriptions.")
    parser.add_argument("output_json_file", help="Path to the output JSON file for saving prosodic values.")
    args = parser.parse_args()

    main(args.input_wav_file, args.input_json_file, args.output_json_file)
