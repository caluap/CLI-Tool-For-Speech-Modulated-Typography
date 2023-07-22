#!/usr/bin/env node

import chalk from "chalk";
import inquirer from "inquirer";
import { Spinner } from "cli-spinner";
import { exec } from "child_process";
import fs from "fs";
import path from "path";

let spinner = null;

const whisperPath = `/Users/calua/repositorios/whisper/whisper.cpp`;

const pathsObject = {
  audioFilePath: "",
  rectifiedAudioFilePath: "",
  rawTranscriptionPath: "",
  preparedTranscriptionPath: "",
  prosodyJSONPath: "",
  affectJSONPath: "",
  paralanguageJSONPath: "",
  finalWebVTT: "",
  typographyModulationMappingsPath: "",
};

let options;

const sleep = (ms = 2000) => new Promise((r) => setTimeout(r, ms));

function updateSpinner(message) {
  if (spinner !== null && spinner.isSpinning()) {
    spinner.stop();
    process.stdout.write("\n");
  }
  spinner = new Spinner(" " + message);
  spinner.setSpinnerString(18);
  spinner.start();
}

function finishCurrentSpinner(message) {
  spinner.stop(true);
  console.log(`${chalk.greenBright("ok")} ${message}`);
}

async function moduleSelection() {
  options = await inquirer.prompt({
    name: "selectedModules",
    type: "checkbox",
    message: chalk.greenBright(` What modules do you want to run? `),
    choices: [
      { value: "Audio Transcription" },
      { value: "Speech metrics: Prosody" },
      { value: "Speech metrics: Valence, Arousal, Dominance" },
      { value: "Generate Caption File" },
      { value: "Generate Captioned Video" },
    ],
  });
}

async function moduleCalls() {
  for (const option of options.selectedModules) {
    switch (option) {
      case "Audio Transcription":
        await audioTranscription();
        await fixTranscriptionPunctuation();
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
    }
  }
}

function outputMessage(s, prefix = null) {
  if (prefix === null) {
    return chalk.cyanBright.bold(`\n>>> ${s}`);
  }
  return `${chalk.bgGreenBright.black(` ${prefix} `)} ${chalk.bold(s)}`;
}

function getFilenameRoot(originalPath) {
  return path.parse(originalPath);
  // { root, dir, base, ext, name }
}

function newFile(pathObject, suffix, extension = null) {
  const { dir, name, ext } = pathObject;
  const newDir = dir || "."; // Use the current directory as a default value if dir is empty
  return path.format({
    dir: newDir,
    name: name + suffix,
    ext: extension ? extension : ext,
  });
}

function extractAudio(audioFilePath) {
  return new Promise(async (resolve, reject) => {
    if (!pathsObject.audioFilePath && audioFilePath === "") {
      const answers = await inquirer.prompt({
        name: "path",
        type: "input",
        message: "From what file should we pull the speech from?",
      });
      pathsObject.audioFilePath = getFilenameRoot(path.normalize(answers.path));
    } else if (audioFilePath !== "") {
      pathsObject.audioFilePath = audioFilePath;
    }

    if (!fs.existsSync(path.format(pathsObject.audioFilePath))) {
      console.log(`${chalk.bgRed.white(" ERROR: ")} File not found`);
      reject(new Error("File not found"));
      return;
    }

    pathsObject.rectifiedAudioFilePath = path.parse(
      newFile(pathsObject.audioFilePath, "_temp", ".wav"),
    );

    const command = `ffmpeg -y -i "${path.format(
      pathsObject.audioFilePath,
    )}" -vn -ac 1 -ar 16000 "${path.format(
      pathsObject.rectifiedAudioFilePath,
    )}";`;

    updateSpinner(outputMessage("Extracting audio...", "FFmpeg"));

    try {
      exec(command, (error, stdout, stderr) => {
        // This function is the callback that will be executed after the command finishes.
        if (error) {
          // Handle any errors that occurred during the command execution.
          console.error("Error executing command:", error);
        } else {
          // The command completed successfully.
          finishCurrentSpinner(
            outputMessage("The audio has been extracted!", "FFmpeg"),
          );
          resolve(); // Resolve the Promise on successful extraction
        }
      });
    } catch (error) {
      console.error("Error occurred:", error);
      reject(error); // Reject the Promise on error
    }
  });
}

async function audioTranscription(audioFilePath = "") {
  console.log(outputMessage(`Audio Transcription`));

  return new Promise(async (resolve, reject) => {
    await extractAudio(audioFilePath);

    const transcriptionPath = path.normalize(
      pathsObject.rectifiedAudioFilePath.dir +
        "/" +
        pathsObject.rectifiedAudioFilePath.name,
    );

    const command = `${whisperPath}/main -m ${whisperPath}/models/ggml-large.bin -f ${path.format(
      pathsObject.rectifiedAudioFilePath,
    )} --max-len 1 -oj -ovtt -of ${transcriptionPath}`;

    updateSpinner(outputMessage("Generating transcript...", "Whisper"));

    try {
      exec(command, (error, stdout, stderr) => {
        // This function is the callback that will be executed after the command finishes.
        if (error) {
          // Handle any errors that occurred during the command execution.
          console.error("Error executing command:", error);
        } else {
          // The command completed successfully.
          finishCurrentSpinner(
            outputMessage("The transcript has been generated!", "Whisper"),
          );
          pathsObject.rawTranscriptionPath = transcriptionPath + ".json";
          resolve(); // Resolve the Promise on successful extraction
        }
      });
    } catch (error) {
      console.error("Error occurred:", error);
      reject(error); // Reject the Promise on error
    }
  });
}

async function fixTranscriptionPunctuation() {
  return new Promise(async (resolve, reject) => {
    pathsObject.preparedTranscriptionPath = newFile(
      pathsObject.audioFilePath,
      "_transcription",
      ".json",
    );
    const command = `python3 ./fix_transcription_punctuation.py ${pathsObject.rawTranscriptionPath} ${pathsObject.preparedTranscriptionPath}`;
    updateSpinner(outputMessage("Fixing transcription...", "Python"));
    try {
      exec(command, (error, stdout, stderr) => {
        // This function is the callback that will be executed after the command finishes.
        if (error) {
          // Handle any errors that occurred during the command execution.
          console.error("Error executing command:", error);
        } else {
          // The command completed successfully.
          finishCurrentSpinner(
            outputMessage("The transcription has been fixed!", "Python"),
          );
          resolve(); // Resolve the Promise on successful extraction
        }
      });
    } catch (error) {
      console.error("Error occurred:", error);
      reject(error); // Reject the Promise on error
    }
  });
}

async function extractProsody() {
  console.log(outputMessage(`Speech metrics: Prosody`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function extractAffectiveDimensions() {
  console.log(outputMessage(`Speech metrics: Valence, Arousal, Dominance`));

  return new Promise(async (resolve, reject) => {
    pathsObject.affectJSONPath = newFile(
      pathsObject.audioFilePath,
      "_affect",
      ".json",
    );
    const command = `python3 ./affect_extraction.py ${path.format(
      pathsObject.rectifiedAudioFilePath,
    )} ${pathsObject.preparedTranscriptionPath} ${pathsObject.affectJSONPath}`;
    updateSpinner(outputMessage("Figuring out emotions...", "Python"));
    try {
      exec(command, (error, stdout, stderr) => {
        // This function is the callback that will be executed after the command finishes.
        if (error) {
          // Handle any errors that occurred during the command execution.
          console.error("Error executing command:", error);
        } else {
          // The command completed successfully.
          finishCurrentSpinner(
            outputMessage("The emotions have been figured out!", "Python"),
          );
          resolve(); // Resolve the Promise on successful extraction
        }
      });
    } catch (error) {
      console.error("Error occurred:", error);
      reject(error); // Reject the Promise on error
    }
  });
}

async function mergeProsodyAndAffect() {
  return new Promise(async (resolve, reject) => {
    pathsObject.paralanguageJSONPath = newFile(
      pathsObject.audioFilePath,
      "_paralanguage",
      ".json",
    );
    const command = `python3 ./merge_prosody_and_affect.py ${pathsObject.prosodyJSONPath} ${pathsObject.affectJSONPath} ${pathsObject.paralanguageJSONPath}`;
    updateSpinner(outputMessage("Merging prosody and emotions...", "Python"));
    try {
      exec(command, (error, stdout, stderr) => {
        // This function is the callback that will be executed after the command finishes.
        if (error) {
          // Handle any errors that occurred during the command execution.
          console.error("Error executing command:", error);
        } else {
          // The command completed successfully.
          finishCurrentSpinner(
            outputMessage("Prosody and emotions have been merged!", "Python"),
          );
          resolve(); // Resolve the Promise on successful extraction
        }
      });
    } catch (error) {
      console.error("Error occurred:", error);
      reject(error); // Reject the Promise on error
    }
  });
}

async function generateCaptionFile() {
  console.log(outputMessage(`Generate Caption File`));
  if (pathsObject.prosodyJSONPath !== "" && pathsObject.affectJSONPath !== "") {
    await mergeProsodyAndAffect();
  }
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function generateCaptionedVideo() {
  console.log(outputMessage(`Generate Captioned Video`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}

await moduleSelection();
await moduleCalls();
