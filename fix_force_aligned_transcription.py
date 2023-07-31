import json
import argparse

def read_original_transcription(transcription_file):
    with open(transcription_file, 'r', encoding='utf-8') as f:
        return f.read().strip().split()

def convert_to_desired_format(input_json, original_transcription):
    output_data = []
    prev_end = 0

    for word_info, original_word in zip(input_json['words'], original_transcription):
        word = original_word

        if word_info['case'] == 'success':
            start_time = word_info['start']
            end_time = word_info['end']
        else:
            # Special handling for 'not-found-in-audio' case
            start_time = prev_end
            if not input_json['words'].index(word_info) == len(input_json['words']) - 1:
                end_time = input_json['words'][input_json['words'].index(word_info) + 1]['start']
            else:
                end_time = start_time + 1

        prev_end = end_time

        formatted_timestamps = {
            "from": "{:.3f}".format(start_time),
            "to": "{:.3f}".format(end_time)
        }

        formatted_offsets = {
            "from": int(start_time * 1000),
            "to": int(end_time * 1000)
        }

        output_data.append({
            "timestamps": formatted_timestamps,
            "offsets": formatted_offsets,
            "text": word
        })

    return output_data

def main():
    parser = argparse.ArgumentParser(description='Convert JSON structure to desired format')
    parser.add_argument('input_json', help='Input JSON file path')
    parser.add_argument('original_transcription', help='File containing original transcription without timing data')
    parser.add_argument('output_file', help='Output JSON file path')
    args = parser.parse_args()

    with open(args.input_json, 'r') as f:
        input_json = json.load(f)

    original_transcription = read_original_transcription(args.original_transcription)

    converted_data = convert_to_desired_format(input_json, original_transcription)

    with open(args.output_file, 'w') as f:
        json.dump(converted_data, f, indent=2)

if __name__ == '__main__':
    main()
