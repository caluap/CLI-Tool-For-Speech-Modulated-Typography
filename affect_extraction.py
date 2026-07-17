import argparse
import json
import os
from pathlib import Path

import audeer
import audinterface
import audonnx
import numpy as np
import soundfile as sf


# ---------------------------------------------------------------------
# Model paths
# ---------------------------------------------------------------------

W2V2_PATH = Path(
    "/Users/calua/google_drive/pessoal/estudo/doutorado/"
    "Research/study2__prosody+emotion/video_selection"
)

# Use the current working directory when the original model directory
# is not available.
if not W2V2_PATH.exists():
    W2V2_PATH = Path.cwd()

MODEL_ROOT = W2V2_PATH / "audeer" / "model"
CACHE_ROOT = W2V2_PATH / "audeer" / "cache"

MODEL_URL = (
    "https://zenodo.org/record/6221127/files/"
    "w2v2-L-robust-12.6bc4a7fd-1.1.0.zip"
)

interface = None


class NumpyValuesEncoder(json.JSONEncoder):
    """
    Converts NumPy values into types supported by JSON.
    """

    def default(self, obj):
        if isinstance(obj, np.floating):
            return float(obj)

        if isinstance(obj, np.integer):
            return int(obj)

        if isinstance(obj, np.bool_):
            return bool(obj)

        if isinstance(obj, np.ndarray):
            return obj.tolist()

        return super().default(obj)


def load_model():
    """
    Downloads, loads, and prepares the wav2vec affect model.
    """

    global interface

    audeer.mkdir(str(CACHE_ROOT))

    archive_path = CACHE_ROOT / "model.zip"

    if not archive_path.exists():
        print("Downloading affect model...")

        audeer.download_url(
            MODEL_URL,
            str(archive_path),
            verbose=True,
        )

    if not MODEL_ROOT.exists():
        print("Extracting affect model...")

        audeer.extract_archive(
            str(archive_path),
            str(MODEL_ROOT),
            verbose=True,
        )

    print(f"Loading affect model from: {MODEL_ROOT}")

    model = audonnx.load(str(MODEL_ROOT))

    np.random.seed(0)

    sampling_rate = 16000

    test_signal = np.random.normal(
        size=sampling_rate,
    ).astype(np.float32)

    # Perform one test call to initialise the model.
    model(
        test_signal,
        sampling_rate,
        outputs="logits",
    )

    interface = audinterface.Feature(
        model.outputs["logits"].labels,
        process_func=model,
        process_func_args={
            # "output_names" was deprecated.
            "outputs": "logits",
        },
        sampling_rate=sampling_rate,
        resample=True,
        verbose=False,
    )

    print("Affect model loaded successfully.")


def load_wav(wav_file_path):
    """
    Loads a WAV file and returns a mono float32 signal and its
    sampling rate.
    """

    audio_signal, sampling_rate = sf.read(
        wav_file_path,
        dtype="float32",
    )

    audio_signal = np.asarray(
        audio_signal,
        dtype=np.float32,
    )

    # Handle stereo or multi-channel input by averaging the channels.
    if audio_signal.ndim > 1:
        audio_signal = np.mean(
            audio_signal,
            axis=1,
            dtype=np.float32,
        )

    return audio_signal, sampling_rate


def extract_audio_segment(
    audio_signal,
    from_offset,
    to_offset,
):
    """
    Extracts a segment from an audio signal using sample positions.
    """

    from_offset = max(0, int(from_offset))
    to_offset = min(
        len(audio_signal),
        int(to_offset),
    )

    if from_offset >= len(audio_signal):
        return None

    if to_offset <= from_offset:
        return None

    return audio_signal[from_offset:to_offset]


def process_json(json_file_path):
    """
    Reads timestamped words from the Whisper JSON file.
    """

    with open(
        json_file_path,
        "r",
        encoding="utf-8",
    ) as json_file:
        data = json.load(json_file)

    if "segments" not in data:
        raise KeyError(
            "The transcription JSON does not contain a "
            "'segments' property."
        )

    transcriptions = []

    for segment in data["segments"]:
        words = segment.get("words", [])

        for word in words:
            if not all(
                key in word
                for key in ("text", "start", "end")
            ):
                print(
                    "Skipping malformed word entry:",
                    word,
                )
                continue

            transcriptions.append(
                {
                    "text": word["text"],
                    "start": float(word["start"]),
                    "end": float(word["end"]),
                }
            )

    return transcriptions


def get_affect_prediction(
    audio_segment,
    sampling_rate,
):
    """
    Processes one audio segment and returns its valence,
    arousal, and dominance predictions.
    """

    if interface is None:
        raise RuntimeError(
            "The affect model interface has not been loaded."
        )

    output = interface.process_signal(
        audio_segment,
        sampling_rate,
    )

    if output.empty:
        raise RuntimeError(
            "The affect model returned an empty result."
        )

    # The model output is a pandas DataFrame with a time-based
    # MultiIndex. Therefore:
    #
    #     output["valence"][0]
    #
    # incorrectly asks for an index label of 0.
    #
    # iloc[0] explicitly selects the first row by position.
    first_row = output.iloc[0]

    valence = float(first_row["valence"])
    arousal = float(first_row["arousal"])
    dominance = float(first_row["dominance"])

    return valence, arousal, dominance


def extract_affective_values(
    wav_file_path,
    json_file_path,
):
    """
    Extracts affective values for each timestamped word.

    Each word is evaluated using a six-second audio window centred
    around that word where possible.
    """

    audio_signal, sampling_rate = load_wav(
        wav_file_path
    )

    transcriptions = process_json(
        json_file_path
    )

    if not transcriptions:
        raise RuntimeError(
            "No timestamped words were found in the "
            "transcription JSON."
        )

    affective_values = []

    window_size_seconds = 6
    desired_duration_samples = int(
        window_size_seconds * sampling_rate
    )

    total_words = len(transcriptions)

    for index, word in enumerate(
        transcriptions,
        start=1,
    ):
        word_text = word["text"]
        word_start = word["start"]
        word_end = word["end"]

        print(
            f"[{index}/{total_words}] "
            f"Processing {word_text!r} "
            f"({word_start:.3f}s–{word_end:.3f}s)"
        )

        sample_from = int(
            word_start * sampling_rate
        )

        sample_to = int(
            word_end * sampling_rate
        )

        word_duration_samples = (
            sample_to - sample_from
        )

        additional_samples = max(
            0,
            desired_duration_samples
            - word_duration_samples,
        )

        offset = additional_samples / 2

        segment_start = int(
            max(
                0,
                sample_from - offset,
            )
        )

        segment_end = int(
            min(
                len(audio_signal),
                sample_to + offset,
            )
        )

        audio_segment = extract_audio_segment(
            audio_signal,
            segment_start,
            segment_end,
        )

        valence = None
        arousal = None
        dominance = None

        if audio_segment is None:
            print(
                f"Skipping {word_text!r}: "
                "the audio segment is invalid."
            )
        else:
            try:
                (
                    valence,
                    arousal,
                    dominance,
                ) = get_affect_prediction(
                    audio_segment,
                    sampling_rate,
                )

            except Exception as error:
                print(
                    f"Could not process {word_text!r}: "
                    f"{type(error).__name__}: {error}"
                )

        affective_values.append(
            {
                "from_time": word_start,
                "to_time": word_end,
                "text": word_text,
                "pred_valence": valence,
                "pred_arousal": arousal,
                "pred_dominance": dominance,
            }
        )

    return affective_values


def main(
    input_wav_file,
    input_json_file,
    output_json_file,
):
    """
    Main entry point for affect extraction.
    """

    input_wav_path = Path(input_wav_file)
    input_json_path = Path(input_json_file)
    output_json_path = Path(output_json_file)

    if not input_wav_path.is_file():
        raise FileNotFoundError(
            f"WAV file not found: {input_wav_path}"
        )

    if not input_json_path.is_file():
        raise FileNotFoundError(
            "Transcription JSON file not found: "
            f"{input_json_path}"
        )

    load_model()

    affective_values = extract_affective_values(
        str(input_wav_path),
        str(input_json_path),
    )

    output_json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_output = json.dumps(
        affective_values,
        cls=NumpyValuesEncoder,
        separators=(",", ":"),
        sort_keys=True,
        indent=4,
        ensure_ascii=False,
    )

    with open(
        output_json_path,
        "w",
        encoding="utf-8",
    ) as output_file:
        output_file.write(json_output)

    print(
        f"Affect values written to: "
        f"{output_json_path}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Extract valence, arousal, and dominance "
            "values from a WAV file using timestamped "
            "transcription data."
        )
    )

    parser.add_argument(
        "input_wav_file",
        help="Path to the input WAV file.",
    )

    parser.add_argument(
        "input_json_file",
        help=(
            "Path to the JSON file containing "
            "timestamped transcriptions."
        ),
    )

    parser.add_argument(
        "output_json_file",
        help=(
            "Path to the output JSON file for the "
            "affective values."
        ),
    )

    args = parser.parse_args()

    main(
        args.input_wav_file,
        args.input_json_file,
        args.output_json_file,
    )