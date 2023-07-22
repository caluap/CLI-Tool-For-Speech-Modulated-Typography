import json
import argparse

def merge_json_files(file1, file2, output_file):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    merged_data = []

    for item1, item2 in zip(data1, data2):
        merged_item = item1.copy()
        merged_item.update(item2)
        merged_data.append(merged_item)

    with open(output_file, 'w') as output:
        json.dump(merged_data, output, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge two JSON files into one.")
    parser.add_argument("file1", help="Path to the first JSON file")
    parser.add_argument("file2", help="Path to the second JSON file")
    parser.add_argument("output_file", help="Path to the output merged JSON file")
    args = parser.parse_args()

    merge_json_files(args.file1, args.file2, args.output_file)
