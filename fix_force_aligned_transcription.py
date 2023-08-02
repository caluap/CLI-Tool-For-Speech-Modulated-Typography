import json
import argparse
import re


def read_original_transcription(transcription_file):
    with open(transcription_file, 'r', encoding='utf-8') as f:
        return f.read().strip().split()


def remove_punctuation(text):
    return re.sub(r'[^\w\s]', '', text)


def convert_to_desired_format(input_json, original_transcription):
    output_data = []
    prev_end = 0

    i = 0
    j = 0

    while i < len(input_json['words']) and j < len(original_transcription):

        original_word = original_transcription[j]
        # Split compound words into individual words
        original_words = original_word.split('-')

        if all(
            remove_punctuation(original_word).lower() == remove_punctuation(
                input_json['words'][i + k]['word']).lower()
            for k, original_word in enumerate(original_words)
        ):
            case = input_json['words'][i]['case']
            num_words_in_json = len(original_words)

            if case == 'success':
                start_time = input_json['words'][i]['start']
                end_time = input_json['words'][i +
                                               num_words_in_json - 1]['end']
            else:
                # Special handling for 'not-found-in-audio' case
                start_time = prev_end
                if i < len(input_json['words']) - 1:
                    end_time = input_json['words'][i +
                                                   1]['startOffset'] / 1000
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
                "text": original_word
            })

            j += 1  # Move forward in the transcription
            i += num_words_in_json  # Move forward in the JSON
        else:
            j += 1  # Move forward in the transcription

    return output_data


def __convert_to_desired_format(input_json, original_transcription):
    output_data = []
    prev_end = 0

    i = 0
    j = 0

    while i < len(input_json['words']) and j < len(original_transcription):

        original_word = original_transcription[i]
        if remove_punctuation(original_word).lower() != remove_punctuation(input_json['words'][j]['word']).lower():
            case = 'missing-word'
        else:
            case = input_json['words'][i]['case']

        if case == 'success':
            start_time = input_json['words'][i]['start']
            end_time = input_json['words'][i]['end']
        else:
            # Special handling for 'not-found-in-audio' case
            start_time = prev_end
            if i < len(input_json['words']) - 1:
                end_time = input_json['words'][i + 1]['start']
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
            "text": original_word
        })

        j += 1  # transcript txt always moves forward
        if case == 'success' or case == 'not-found-in-audio':
            i += 1

    return output_data


def main():
    parser = argparse.ArgumentParser(
        description='Convert JSON structure to desired format')
    parser.add_argument('input_json', help='Input JSON file path')
    parser.add_argument('original_transcription',
                        help='File containing original transcription without timing data')
    parser.add_argument('output_file', help='Output JSON file path')
    args = parser.parse_args()

    with open(args.input_json, 'r') as f:
        input_json = json.load(f)

    original_transcription = read_original_transcription(
        args.original_transcription)

    converted_data = convert_to_desired_format(
        input_json, original_transcription)

    with open(args.output_file, 'w') as f:
        json.dump(converted_data, f, indent=2)


if __name__ == '__main__':
    main()
