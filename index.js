#!/usr/bin/env node

import chalk from "chalk";
import inquirer from "inquirer";
import { createSpinner } from "nanospinner";

let options;

const sleep = (ms = 2000) => new Promise((r) => setTimeout(r, ms));

async function welcome() {
  console.log(`${chalk.bgBlueBright("hey yo")}`);

  await sleep(500);

  console.log(`
    ${chalk.bgBlue("Hello World")}
    Hi
    Goodbye
  `);
}

async function askName() {
  const answers = await inquirer.prompt({
    name: "player_name",
    type: "input",
    message: "What is your name?",
    default() {
      return "Player";
    },
  });

  playerName = answers.player_name;
}

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

async function handleAnswer(isCorrect) {
  const spinner = createSpinner("Checking answer...").start();
  await sleep();

  if (isCorrect) {
    spinner.success({ text: `Nice work ${playerName}` });
  } else {
    spinner.error({ text: `You died ${playerName}` });
    process.exit(1);
  }
}

function outputModule(s) {
  return `\n\n${chalk.bgGreenBright.black(" MODULE ")} ${chalk.bold(s)}`;
}

async function audioTranscription() {
  console.log(outputModule(`Audio Transcription`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function forceSync() {
  console.log(outputModule(`Force-Sync Module`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function extractProsody() {
  console.log(outputModule(`Speech metrics: Prosody`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function extractAffectiveDimensions() {
  console.log(outputModule(`Speech metrics: Valence, Arousal, Dominance`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function generateCaptionFile() {
  console.log(outputModule(`Speech metrics: Prosody`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}
async function generateCaptionedVideo() {
  console.log(outputModule(`Generate Captioned Video`));
  console.log(chalk.bgRedBright.whiteBright(` SORRY! NOT IMPLEMENTED! `));
}

await moduleSelection();
await moduleCalls();
