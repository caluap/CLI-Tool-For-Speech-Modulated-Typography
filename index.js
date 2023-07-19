#!/usr/bin/env node

import chalk from "chalk";
import inquirer from "inquirer";
import { createSpinner } from "nanospinner";

let playerName;

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

async function question1() {
  const answers = await inquirer.prompt({
    name: "question_1",
    type: "list",
    message: "Javascript was created in 10 days then released on\n",
    choices: [
      "May 23rd, 1995",
      "Nov 24th, 1995",
      "Dec 4th, 1995",
      "Dec 17th, 1996",
    ],
  });

  return handleAnswer(answers.question_1 == "Dec 4th, 1995");
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

await welcome();
await askName();
await question1();
