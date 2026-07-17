#!/usr/bin/env node

import chalk from "chalk";
import inquirer from "inquirer";
import { Spinner } from "cli-spinner";
import { exec } from "child_process";
import fs from "fs";
import path from "path";

let spinner = null;

const pathsObject = {
  audioFilePath: "",
  rectifiedAudioFilePath: "",
  rawTranscriptionPath: "",
  syncedTranscriptionPath: "",
  preparedTranscriptionPath: "",
  prosodyJSONPath: "",
  affectJSONPath: "",
  paralanguageJSONPath: "",
  finalWebVTT: "",
  typographyModulationMappingsPath: "",
};

let options;
let language = "English";
let scrollingCaptions = false;

/**
 * Quotes a value so that paths containing spaces can safely be used
 * in shell commands.
 */
function shellQuote(value) {
  return "'" + String(value).replace(/'/g, "'\\''") + "'";
}

function updateSpinner(message) {
  if (spinner !== null && spinner.isSpinning()) {
    spinner.stop(true);
    process.stdout.write("\n");
  }

  spinner = new Spinner(` ${message}`);
  spinner.setSpinnerString(18);
  spinner.start();
}

function stopCurrentSpinner() {
  if (spinner !== null && spinner.isSpinning()) {
    spinner.stop(true);
  }
}

function finishCurrentSpinner(message) {
  stopCurrentSpinner();
  console.log(`${chalk.greenBright("ok")} ${message}`);
}

/**
 * Runs a shell command and returns a Promise.
 *
 * Importantly, this rejects the Promise if the command fails.
 * Without reject(), the Node program would remain waiting forever.
 */
function runCommand(command, workingMessage, successMessage) {
  updateSpinner(workingMessage);

  return new Promise((resolve, reject) => {
    exec(
      command,
      {
        // Some Python/Whisper commands can produce a lot of output.
        maxBuffer: 20 * 1024 * 1024,
      },
      (error, stdout, stderr) => {
        if (error) {
          stopCurrentSpinner();

          const errorDetails =
            stderr?.trim() ||
            stdout?.trim() ||
            error.message ||
            "Unknown command error";

          reject(
            new Error(
              `Command failed:\n${command}\n\n${errorDetails}`,
            ),
          );

          return;
        }

        finishCurrentSpinner(successMessage);

        resolve({
          stdout,
          stderr,
        });
      },
    );
  });
}

async function moduleSelection() {
  options = await inquirer.prompt([
    {
      name: "selectedModules",
      type: "checkbox",
      message: chalk.greenBright("What modules do you want to run?"),
      choices: [
        { value: "Audio Transcription" },
        { value: "Speech metrics: Prosody" },
        {
          value: "Speech metrics: Valence, Arousal, Dominance",
        },
        { value: "Generate Caption File" },
        { value: "Generate Captioned Video" },
      ],
    },
    {
      name: "captionStyle",
      type: "list",
      message: chalk.greenBright(
        "Do you want scrolling or block captions?",
      ),
      choices: ["Scrolling captions", "Block captions"],
    },
    {
      name: "language",
      type: "list",
      message: chalk.greenBright(
        "What language do the characters speak?",
      ),
      choices: ["English", "Korean"],
    },
  ]);

  scrollingCaptions =
    options.captionStyle === "Scrolling captions";

  language = options.language;
}

async function moduleCalls() {
  for (const option of options.selectedModules) {
    switch (option) {
      case "Audio Transcription":
        await audioTranscription();
        break;

      case "Speech metrics: Prosody":
        await extractProsody();
        break;

      case "Speech metrics: Valence, Arousal, Dominance":
        await extractAffectiveDimensions();
        break;

      case "Generate Caption File":
        await generateCaptionFile();
        break;

      case "Generate Captioned Video":
        await generateCaptionedVideo();
        break;

      default:
        throw new Error(`Unknown module: ${option}`);
    }
  }
}

function outputMessage(message, prefix = null) {
  if (prefix === null) {
    return chalk.cyanBright.bold(`\n>>> ${message}`);
  }

  return `${chalk.bgGreenBright.black(
    ` ${prefix} `,
  )} ${chalk.bold(message)}`;
}

function getFilenameRoot(originalPath) {
  return path.parse(originalPath);
}

/**
 * Creates a filename based on an existing parsed path.
 *
 * Example:
 * damage.mp4 + "_affect" + ".json"
 * becomes:
 * damage_affect.json
 */
function newFile(pathObject, suffix, extension = null) {
  const { dir, name, ext } = pathObject;

  const newDir = dir || ".";

  return path.format({
    dir: newDir,
    name: name + suffix,
    ext: extension ?? ext,
  });
}

async function readFilename(promptMessage) {
  const answers = await inquirer.prompt({
    name: "path",
    type: "input",
    message: promptMessage,
  });

  const normalisedPath = path.normalize(
    answers.path.trim(),
  );

  return getFilenameRoot(normalisedPath);
}

function ensureSpeechInputsExist() {
  if (!pathsObject.rectifiedAudioFilePath) {
    throw new Error(
      "No prepared WAV file is available. Select “Audio Transcription” before selecting speech-metric modules.",
    );
  }

  const wavPath = path.format(
    pathsObject.rectifiedAudioFilePath,
  );

  if (!fs.existsSync(wavPath)) {
    throw new Error(
      `The prepared WAV file could not be found:\n${wavPath}`,
    );
  }

  if (!pathsObject.rawTranscriptionPath) {
    throw new Error(
      "No timestamped transcription is available. Select “Audio Transcription” before selecting speech-metric modules.",
    );
  }

  if (!fs.existsSync(pathsObject.rawTranscriptionPath)) {
    throw new Error(
      `The transcription file could not be found:\n${pathsObject.rawTranscriptionPath}`,
    );
  }
}

async function extractAudio(audioFilePath = "") {
  if (!pathsObject.audioFilePath) {
    if (audioFilePath) {
      pathsObject.audioFilePath =
        typeof audioFilePath === "string"
          ? path.parse(path.normalize(audioFilePath))
          : audioFilePath;
    } else {
      pathsObject.audioFilePath = await readFilename(
        "From what file should we pull the speech?",
      );
    }
  }

  const sourcePath = path.format(
    pathsObject.audioFilePath,
  );

  if (!fs.existsSync(sourcePath)) {
    throw new Error(`File not found:\n${sourcePath}`);
  }

  const rectifiedAudioPath = newFile(
    pathsObject.audioFilePath,
    "_temp",
    ".wav",
  );

  pathsObject.rectifiedAudioFilePath = path.parse(
    rectifiedAudioPath,
  );

  const command = [
    "ffmpeg",
    "-y",
    "-i",
    shellQuote(sourcePath),
    "-vn",
    "-ac",
    "1",
    shellQuote(rectifiedAudioPath),
  ].join(" ");

  await runCommand(
    command,
    outputMessage("Extracting audio...", "FFmpeg"),
    outputMessage(
      "The audio has been extracted!",
      "FFmpeg",
    ),
  );
}

async function audioTranscription(audioFilePath = "") {
  console.log(outputMessage("Audio Transcription"));

  await extractAudio(audioFilePath);

  const wavPath = path.format(
    pathsObject.rectifiedAudioFilePath,
  );

  const outputDirectory =
    pathsObject.rectifiedAudioFilePath.dir || ".";

  const transcriptionRoot = path.join(
    outputDirectory,
    pathsObject.rectifiedAudioFilePath.name,
  );

  /*
   * whisper_timestamped normally creates:
   *
   * damage_temp.wav.words.json
   *
   * We rename that to:
   *
   * damage_temp.json
   */
  const generatedWordsPath = path.join(
    outputDirectory,
    `${pathsObject.rectifiedAudioFilePath.base}.words.json`,
  );

  const finalTranscriptionPath =
    `${transcriptionRoot}.json`;

  const model = "large";

  const command = [
    "whisper_timestamped",
    shellQuote(wavPath),
    "--model",
    shellQuote(model),
    "--language",
    shellQuote(language),
    "--output_format",
    "json",
    "--vad",
    "True",
    "--output_dir",
    shellQuote(outputDirectory),
    "&&",
    "mv",
    shellQuote(generatedWordsPath),
    shellQuote(finalTranscriptionPath),
  ].join(" ");

  await runCommand(
    command,
    outputMessage(
      "Generating transcript...",
      "Whisper",
    ),
    outputMessage(
      "The transcript has been generated!",
      "Whisper",
    ),
  );

  pathsObject.rawTranscriptionPath =
    finalTranscriptionPath;
}

async function extractProsody() {
  console.log(
    outputMessage("Speech metrics: Prosody"),
  );

  ensureSpeechInputsExist();

  pathsObject.prosodyJSONPath = newFile(
    pathsObject.audioFilePath,
    "_prosody",
    ".json",
  );

  const command = [
    "python3",
    shellQuote("./prosodic_extraction.py"),
    shellQuote(
      path.format(pathsObject.rectifiedAudioFilePath),
    ),
    shellQuote(pathsObject.rawTranscriptionPath),
    shellQuote(pathsObject.prosodyJSONPath),
  ].join(" ");

  await runCommand(
    command,
    outputMessage(
      "Figuring out prosody...",
      "Python",
    ),
    outputMessage(
      "Prosody has been figured out!",
      "Python",
    ),
  );
}

async function extractAffectiveDimensions() {
  console.log(
    outputMessage(
      "Speech metrics: Valence, Arousal, Dominance",
    ),
  );

  ensureSpeechInputsExist();

  pathsObject.affectJSONPath = newFile(
    pathsObject.audioFilePath,
    "_affect",
    ".json",
  );

  const command = [
    "python3",
    shellQuote("./affect_extraction.py"),
    shellQuote(
      path.format(pathsObject.rectifiedAudioFilePath),
    ),
    shellQuote(pathsObject.rawTranscriptionPath),
    shellQuote(pathsObject.affectJSONPath),
  ].join(" ");

  await runCommand(
    command,
    outputMessage(
      "Figuring out emotions...",
      "Python",
    ),
    outputMessage(
      "The emotions have been figured out!",
      "Python",
    ),
  );
}

async function mergeProsodyAndAffect() {
  pathsObject.paralanguageJSONPath = newFile(
    pathsObject.audioFilePath,
    "_paralanguage",
    ".json",
  );

  const command = [
    "python3",
    shellQuote("./merge_prosody_and_affect.py"),
    shellQuote(pathsObject.prosodyJSONPath),
    shellQuote(pathsObject.affectJSONPath),
    shellQuote(pathsObject.paralanguageJSONPath),
  ].join(" ");

  await runCommand(
    command,
    outputMessage(
      "Merging prosody and emotions...",
      "Python",
    ),
    outputMessage(
      "Prosody and emotions have been merged!",
      "Python",
    ),
  );
}

async function generateCaptionFile() {
  console.log(
    outputMessage("Generate Caption File"),
  );

  if (
    pathsObject.prosodyJSONPath &&
    pathsObject.affectJSONPath
  ) {
    await mergeProsodyAndAffect();
  } else if (pathsObject.prosodyJSONPath) {
    pathsObject.paralanguageJSONPath =
      pathsObject.prosodyJSONPath;
  } else if (pathsObject.affectJSONPath) {
    pathsObject.paralanguageJSONPath =
      pathsObject.affectJSONPath;
  } else {
    throw new Error(
      "No source paralanguage file is available. Run Prosody, Affect, or both before generating the caption file.",
    );
  }

  pathsObject.finalWebVTT = newFile(
    pathsObject.audioFilePath,
    "_caption",
    ".vtt",
  );

  const commandParts = [
    "python3",
    shellQuote("./generate_caption_file.py"),
    shellQuote(pathsObject.paralanguageJSONPath),
    shellQuote(pathsObject.finalWebVTT),
  ];

  /*
   * The transcription argument is required for block
   * captions, but not for scrolling captions.
   */
  if (!scrollingCaptions) {
    if (!pathsObject.rawTranscriptionPath) {
      throw new Error(
        "Block captions require a transcription file.",
      );
    }

    commandParts.push(
      shellQuote(pathsObject.rawTranscriptionPath),
    );
  }

  const command = commandParts.join(" ");

  await runCommand(
    command,
    outputMessage(
      "Preparing caption file (WebVTT)...",
      "Python",
    ),
    outputMessage(
      "The WebVTT caption file has been created!",
      "Python",
    ),
  );
}

async function generateCaptionedVideo() {
  console.log(
    outputMessage("Generate Captioned Video"),
  );

  console.log(
    chalk.bgRedBright.whiteBright(
      " SORRY! NOT IMPLEMENTED! ",
    ),
  );
}

try {
  await moduleSelection();
  await moduleCalls();
} catch (error) {
  stopCurrentSpinner();

  console.error(
    `\n${chalk.bgRed.white(" ERROR ")} ${chalk.red(
      error.message,
    )}`,
  );

  process.exitCode = 1;
}