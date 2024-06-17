import json
import sys

class_mapping = {
    "pred_arousal": "v_arou",
    "pred_dominance": "v_domi",
    "pred_valence": "v_vale",
    "pred_arousal_norm": "v_naro",
    "pred_dominance_norm": "v_ndom",
    "pred_valence_norm": "v_nval",
    "raw_loudness": "v_rlou",
    "raw_pitch": "v_rpit",
    "raw_duration": "v_rdur",
    "loudness": "v_loud",
    "pitch": "v_pitc",
    "duration": "v_dura"
}

def format_time(time):
    time = float(time)
    hours = int(time) // 3600
    minutes = int(time) % 3600 // 60
    seconds = int(time) % 60
    milliseconds = int((time % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def format_class_value(class_name, value):
    # Convert the numerical value to the class format (e.g., 0.5050724744796753 to '0p505')
    return f"{class_name}_{value:.3f}".replace('.', 'p')

def normalize_data(data):
    fields = list(data[0].keys())

    fields.remove("from_time")
    fields.remove("to_time")
    fields.remove("text")

    for field in fields:
        temp = [word[field] for word in data]
        min_value = min(temp)
        max_value = max(temp)
        if max_value - min_value == 0:
            normalized_temp = [0 for x in temp]
        else:
            normalized_temp = [(x - min_value) / (max_value - min_value) for x in temp]
        for i, word in enumerate(data):
            word[f"{field}_norm"] = normalized_temp[i]

def caption_blocks(data, raw_transcript_file):
    with open(raw_transcript_file, 'r') as f:
        raw_transcript = json.load(f)
    block_data = []
    i = 0

def get_class_attribute(item, t0 = -1, t1 = -1):
    class_attributes = []

    for class_name, class_value in item.items():
        if class_name in class_mapping:
            class_identifier = class_mapping[class_name]
            class_value_str = format_class_value(class_identifier, class_value)
            class_attributes.append(class_value_str)


    if t0 != -1 and t1 != -1:
        start = format_class_value("v_strt", t0)
        class_attributes.append(start)
        end = format_class_value("v_endd", t1)
        class_attributes.append(end)


    class_attribute = ".".join(class_attributes)

    if class_attribute:
        class_attribute = f"<c.{class_attribute}>"
    return class_attribute

def scrolling_caption(data):
    webvtt_content = "WEBVTT\n\n"

    for item in data:
        from_time_formatted = format_time(item["from_time"])  # Handles both str and int
        to_time_formatted = format_time(item["to_time"])  # Handles both str and int
        text = item["text"]
        class_attribute = get_class_attribute(item)

        webvtt_content += f"{from_time_formatted} --> {to_time_formatted}\n{class_attribute}{text}</c>\n\n"   

    return webvtt_content

def block_captions(data, raw_transcript_file):
    read_time_buffer = 2

    # loads raw transcript file
    with open(raw_transcript_file, 'r') as f:
        raw_transcript = json.load(f)
    webvtt_content = "WEBVTT\n\n"
    i = 0

    for j in range(len(raw_transcript["segments"])):
        segment = raw_transcript["segments"][j]
        start = segment["start"]
        end = segment["end"]
        duration = end - start

        if j < len(raw_transcript["segments"]) - 1:
            next_start = raw_transcript["segments"][j + 1]["start"]
            maximum_duration = next_start - start
            adjusted_duration = min(duration + read_time_buffer, maximum_duration)
        else:
            adjusted_duration = duration + read_time_buffer

        end = start + adjusted_duration


        start_formatted = format_time(start)
        end_formatted = format_time(end)
        webvtt_content += f"{start_formatted} --> {end_formatted}\n"

        for word in segment["words"]:
            item = data[i]
            t0 = item["from_time"]
            t1 = item["to_time"]

            # when should modulations be applied, and when
            # should the end?
            word_t0 = t0 - start
            word_t1 = t1 - start

            text = item["text"]
            class_attribute = get_class_attribute(item, word_t0, word_t1)
            webvtt_content += f"{class_attribute}{text}</c>"

            i += 1

        webvtt_content += "\n\n"
    return webvtt_content

    

def generate_caption_file(input_file, output_file, raw_transcript_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    normalize_data(data)
    if raw_transcript_file == None:
        webvtt_content = scrolling_caption(data)
    else:
        webvtt_content = block_captions(data, raw_transcript_file)


    # Save the content to a .vtt file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(webvtt_content)
    


    
    


if __name__ == "__main__":
    if len(sys.argv) not in [3, 4]:
        print("Usage: python generate_caption_file.py input_file output_file option_raw_transcript")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    raw_transcript_file = sys.argv[3] if len(sys.argv) == 4 else None


    generate_caption_file(input_file, output_file, raw_transcript_file)