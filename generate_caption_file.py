import json
import sys

class_mapping = {
    "pred_arousal": "raro",
    "pred_dominance": "rdom",
    "pred_valence": "rval",
    "pred_arousal_norm": "arou",
    "pred_dominance_norm": "domi",
    "pred_valence_norm": "vale"
}

def format_time(time):
    # Split the time string into hours, minutes, seconds, and milliseconds
    time_parts = time.split(":")
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds_ms = time_parts[2].split(",")
    seconds = int(seconds_ms[0])
    milliseconds = int(seconds_ms[1])

    # Convert time to milliseconds
    time_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds

    # Convert milliseconds to the WebVTT time format (hh:mm:ss.sss)
    hours = time_ms // 3600000
    time_ms %= 3600000
    minutes = time_ms // 60000
    time_ms %= 60000
    seconds = time_ms // 1000
    milliseconds = time_ms % 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

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
        normalized_temp = [(x - min_value) / (max_value - min_value) for x in temp]
        for i, word in enumerate(data):
            word[f"{field}_norm"] = normalized_temp[i]

def generate_caption_file(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    normalize_data(data)
    # Create the WebVTT content
    webvtt_content = "WEBVTT\n\n"

    for item in data:
        from_time_formatted = format_time(item["from_time"])  # Handles both str and int
        to_time_formatted = format_time(item["to_time"])  # Handles both str and int
        text = item["text"]
        class_attributes = []

        for class_name, class_value in item.items():
            if class_name in class_mapping:
                class_identifier = class_mapping[class_name]
                class_value_str = format_class_value(class_identifier, class_value)
                class_attributes.append(class_value_str)

        class_attribute = ".".join(class_attributes)
        if class_attribute:
            class_attribute = f"<c.{class_attribute}>"

        webvtt_content += f"{from_time_formatted} --> {to_time_formatted}\n{class_attribute}{text}</c>\n\n"



    # Save the content to a .vtt file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(webvtt_content)
    


    
    


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_caption_file.py input_file output_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    generate_caption_file(input_file, output_file)