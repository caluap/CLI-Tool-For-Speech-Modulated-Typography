#!/usr/bin/env node

import chalk from "chalk";
import inquirer from "inquirer";
// import { createSpinner } from "nanospinner";
import { exec } from "child_process";
import fs from "fs";
import path from "path";


const originalFile = {
  audioFilePath: "",
  rawTranscriptionPath: "",
  syncedTranscriptionPath: "",
  paralanguageJSONPath: "",
  finalWebVTT: "",
  typographyModulationMappingsPath: "",
};

let options;

const sleep = (ms = 2000) => new Promise((r) => setTimeout(r, ms));

async function moduleSelection() {
  options = await inquirer.prompt({
    name: "selectedModules",
    type: "checkbox",
    message: chalk.greenBright(` What modules do you want to run? `),
    choices: [
      { value: "Audio Transcription" },
      { value: "Force Sync" },
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
        break;
      case "Force Sync":
        await forceSync();
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
function outputMessage(s, prefix = "MODULE") {
  return `\n\n${chalk.bgGreenBright.black(` ${prefix} `)} ${chalk.bold(s)}`;
}

function getFilenameRoot(originalPath) {
  return path.parse(originalPath);
  // { root, dir, base, ext, name }
}

function newFile(pathObject, suffix, extension = null) {
  return path.format({
    dir: pathObject.dir,
    name: pathObject.name + suffix,
    ext: extension ? extension : pathObject.ext,
  });
}

function extractAudio(audioFilePath) {
  return new Promise(async (resolve, reject) => {
    console.log(outputMessage("Audio Extraction"));

    if (!originalFile.audioFilePath && audioFilePath === "") {
      const answers = await inquirer.prompt({
        name: "path",
        type: "input",
        message: "From what file should we pull the speech from?",
      });
      originalFile.audioFilePath = getFilenameRoot(
        path.normalize(answers.path),
      );
    } else if (audioFilePath !== "") {
      originalFile.audioFilePath = audioFilePath;
    }

    if (!fs.existsSync(path.format(originalFile.audioFilePath))) {
      console.log(`${chalk.bgRed.white(" ERROR: ")} File not found`);
      reject(new Error("File not found"));
      return;
    }

    const command = `ffmpeg -y -i "${path.format(
      originalFile.audioFilePath,
    )}" -vn -ac 1 -ar 16000 "${newFile(
      originalFile.audioFilePath,
      "_temp",
      ".wav",
    )}";`;

    console.log(outputMessage("Extracting audio", "FFMPEG"));
    console.log(chalk.bgBlue(command));

    try {
      await exec(command);
      console.log(chalk.bgBlue(`exec ran`));

      resolve(); // Resolve the Promise on successful extraction
    } catch (error) {
      console.error("Error occurred:", error);
      reject(error); // Reject the Promise on error
    }
  });
}

async function audioTranscription(audioFilePath = "") {
  console.log(outputMessage(`Audio Transcription`));
  // console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));

  await extractAudio(audioFilePath);
}
async function forceSync() {
  console.log(outputMessage(`Force-Sync Module`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function extractProsody() {
  console.log(outputMessage(`Speech metrics: Prosody`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function extractAffectiveDimensions() {
  console.log(outputMessage(`Speech metrics: Valence, Arousal, Dominance`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function generateCaptionFile() {
  console.log(outputMessage(`Speech metrics: Prosody`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function generateCaptionedVideo() {
  console.log(outputMessage(`Generate Captioned Video`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}

await moduleSelection();
await moduleCalls();
