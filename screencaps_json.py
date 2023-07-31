import json

def process_json(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    processed_data = []
    for item in data:
        processed_item = {
            "duration": float(item["to_time"]) - float(item["from_time"]),
            "end": float(item["to_time"]),
            "pred_arousal": item["pred_arousal"],
            "pred_dominance": item["pred_dominance"],
            "pred_valence": item["pred_valence"],
            "processed_rolled_avg_duration": -1.0,
            "processed_rolled_avg_loudness": -1.0,
            "processed_rolled_avg_pitch": -1.0,
            "processed_rolled_avg_relative_duration": -1.0,
            "raw_avg_loudness": -1.0,
            "raw_avg_pitch": -1.0,
            "raw_loudness": [-1.0],
            "raw_pitch": [-1.0],
            "rolling_avg_loudness": -1.0,
            "rolling_avg_pitch": -1.0,
            "rolling_avg_relative_duration": -1.0,
            "start": float(item["from_time"]),
            "target_valence": -1.0,
            "tts_duration": -1.0,
            "word": item["text"]
        }
        processed_data.append(processed_item)

    with open(output_file, 'w') as f:
        json.dump(processed_data, f, indent=2)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python process_json.py input_file.json output_file.json")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        process_json(input_file, output_file)
