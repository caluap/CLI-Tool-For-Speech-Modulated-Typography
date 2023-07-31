import json
import sys

class_mapping = {
    "pred_arousal": "v_arou",
    "pred_dominance": "v_domi",
    "pred_valence": "v_vale",
    "pred_arousal_norm": "v_naro",
    "pred_dominance_norm": "v_ndom",
    "pred_valence_norm": "v_nval"
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