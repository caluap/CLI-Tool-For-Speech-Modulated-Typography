import json
import sys

def merge_words_with_punctuation(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)["transcription"]

    merged_data = []
    current_entry = None

    for entry in data:
        entry["text"] = entry["text"].strip()
        if current_entry is None and entry["text"] != "":
            current_entry = entry
        elif entry["text"] in (".", ",", "!", "?") or entry["text"].startswith("'"):
            current_entry["text"] += entry["text"]
            current_entry["timestamps"]["to"] = entry["timestamps"]["to"]
            current_entry["offsets"]["to"] = entry["offsets"]["to"]
        else:
            if current_entry != None and current_entry["text"] != "":
              merged_data.append(current_entry)
            if entry["text"] == "":
                current_entry = None
            else:
                current_entry = entry

    if current_entry is not None:
        merged_data.append(current_entry)

    with open(output_file, 'w') as f:
        json.dump(merged_data, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python merge_script.py input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    merge_words_with_punctuation(input_file, output_file)
