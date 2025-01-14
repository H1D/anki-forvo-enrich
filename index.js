#!/usr/bin/env node

import axios from "axios";
import fastcsv from "fast-csv";
import fs from "fs";
import path from "path";
import ISO6391 from "iso-639-1";
import os from "os";
import chalk from "chalk";
import { Command } from "commander";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const packageJson = JSON.parse(
  fs.readFileSync(path.join(__dirname, "package.json"), "utf8")
);

const FORVO_API_BASE = "https://apifree.forvo.com";

const program = new Command();

program
  .name("npx " + packageJson.name)
  .description(packageJson.description)
  .version(packageJson.version)
  .argument(
    "<path-to-file>",
    'Path to Anki flashcards export file. (Use "Notes as in Plain text" format. No HTML, no tags included. )'
  )
  .argument("<lang>", "ISO 639-1 language code")
  .option("-a, --articles <list>", "Comma separated list of article in <lang>")
  .option("-u, --user <name>", "Anki user name", "User 1")
  .option("-k, --key <key>", "Forvo API key")
  .action((filePath, lang, options) => {
    if (!ISO6391.validate(lang)) {
      console.error(
        chalk.red(
          `Unsupported language. Please provide a valid ISO 639-1 language code.`
        )
      );
      program.help();
    }

    let articles = [];
    if (options.articles) {
      articles = options.articles.split(",").map((a) => a.trim());
    }

    let AUDIO_DIR;
    switch (os.platform()) {
      case "darwin":
        AUDIO_DIR = path.resolve(
          os.homedir(),
          `Library/Application Support/Anki2/${options.user}/collection.media/`
        );
        break;
      case "win32":
        AUDIO_DIR = path.resolve(
          os.homedir(),
          `AppData/Roaming/Anki2/${options.user}/collection.media/`
        );
        break;
      case "linux":
        AUDIO_DIR = path.resolve(
          os.homedir(),
          `.local/share/Anki2/${options.user}/collection.media/`
        );
        break;
      default:
        console.error(chalk.red(`Unsupported platform`));
        process.exit(1);
    }

    // Check if the user directory exists
    if (!fs.existsSync(AUDIO_DIR)) {
      console.error(
        chalk.red(
          `The directory for user "${options.user}" does not exist: ${AUDIO_DIR}`
        )
      );
      console.error(chalk.yellow("Use -u <user> to specify a different user."));
      process.exit(1); // Exit if the directory does not exist
    }

    console.info(chalk.blue(`Dir for audio files: ${AUDIO_DIR}`));

    async function fetchPronunciation(word, retryCount = 0) {
      try {
        console.log(`\n---${word}---`);
        const apiUrl = `${FORVO_API_BASE}/key/${
          options.key
        }/format/json/action/word-pronunciations/word/${encodeURIComponent(
          word
        )}/language/${lang}`;
        console.log(`API request URL: ${apiUrl}`);

        console.log("Making API request...");
        const response = await axios.get(apiUrl);
        console.log(`API response status: ${response.status}`);

        const data = response.data;
        if (data.items) {
          console.log(`Found ${data.items.length} pronunciations`);
        } else {
          console.log("No items in API response");
          console.log("API response:", JSON.stringify(data, null, 2));
        }

        if (!data.items || data.items.length === 0) {
          // Clean the word from punctuation and try different variations
          let cleanWord = word.replace(/[.,!?;:]/g, "").trim();

          if (articles.length) {
            const articleRegex = new RegExp(`\\b${articles.join("|")}\\b`, "i");
            const articleMatch = articleRegex.exec(cleanWord);
            if (articleMatch) {
              const article = articleMatch[0];
              console.log(`Retrying without article: ${article}`);
              return fetchPronunciation(
                cleanWord.replace(article, "").trim(),
                retryCount
              );
            }
          }

          // If word has punctuation, try without it
          if (word !== cleanWord) {
            console.log(`Retrying without punctuation: ${cleanWord}`);
            return fetchPronunciation(cleanWord, retryCount);
          }

          console.info(chalk.blue(`Can't find pronunciation for "${word}"`));
          return;
        }

        // Get the best rated pronunciation
        const bestPronunciation = data.items.sort((a, b) => b.rate - a.rate)[0];
        console.log(
          `Best pronunciation: Rate=${bestPronunciation.rate}, User=${bestPronunciation.username}, Country=${bestPronunciation.country}`
        );

        const audioUrl = bestPronunciation.pathmp3;
        if (audioUrl) {
          console.log(`Found audio URL: ${audioUrl}`);
          return await downloadAudio(audioUrl, word);
        }

        console.info(chalk.blue(`Can't extract audio URL for "${word}"`));
        return;
      } catch (error) {
        console.error(chalk.red("Error details:"));
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          console.error(chalk.red(`Status: ${error.response.status}`));
          console.error(
            chalk.red(
              `Headers: ${JSON.stringify(error.response.headers, null, 2)}`
            )
          );
          console.error(
            chalk.red(`Data: ${JSON.stringify(error.response.data, null, 2)}`)
          );

          // Check for API limit
          if (
            error.response.status === 400 &&
            Array.isArray(error.response.data) &&
            error.response.data[0] === "Limit/day reached."
          ) {
            console.error(
              chalk.red.bold("\n========================================")
            );
            console.error(chalk.red.bold("🚫 Daily API limit reached!"));
            console.error(
              chalk.red.bold(
                "Please try again tomorrow or use a different API key."
              )
            );
            console.error(
              chalk.red.bold(
                "You can provide a different key using the --key option."
              )
            );
            console.error(
              chalk.red.bold("========================================\n")
            );
            process.exit(1);
          }
        } else if (error.request) {
          // The request was made but no response was received
          console.error(chalk.red("No response received from server"));
          console.error(chalk.red(error.request));
        } else {
          // Something happened in setting up the request that triggered an Error
          console.error(chalk.red(`Error message: ${error.message}`));
        }

        if (retryCount < 5) {
          const delay = 1000 * (retryCount + 1);
          console.log(
            chalk.yellow(
              `Retrying in ${delay}ms (attempt ${retryCount + 1}/5)...`
            )
          );
          await new Promise((resolve) => setTimeout(resolve, delay));
          return fetchPronunciation(word, retryCount + 1);
        } else {
          console.error(chalk.red(`Max retries reached for "${word}"`));
        }
      }
    }

    async function downloadAudio(url, word) {
      const fileExtension = path.extname(new URL(url).pathname);
      const baseFilename = `${word}_${lang}`;

      // Check for both .ogg and .mp3 files
      const oggPath = path.resolve(AUDIO_DIR, `./${baseFilename}.ogg`);
      const mp3Path = path.resolve(AUDIO_DIR, `./${baseFilename}.mp3`);

      console.log("Checking for existing files:");
      console.log(`- OGG path: ${oggPath}`);
      console.log(`- MP3 path: ${mp3Path}`);

      // If either file exists, use it
      if (fs.existsSync(oggPath)) {
        console.log(chalk.green(`Using existing OGG file: ${oggPath}`));
        return `[sound:${baseFilename}.ogg]`;
      }
      if (fs.existsSync(mp3Path)) {
        console.log(chalk.green(`Using existing MP3 file: ${mp3Path}`));
        return `[sound:${baseFilename}.mp3]`;
      }

      const filename = `${baseFilename}${fileExtension}`;
      const audioPath = path.resolve(AUDIO_DIR, `./${filename}`);
      console.log(`No existing files found. Will download to: ${audioPath}`);

      console.log("Starting download...");
      const response = await axios({
        method: "get",
        url: url,
        responseType: "stream",
      });
      console.log(`Download response status: ${response.status}`);

      console.log(`Writing audio file to ${audioPath}`);
      await new Promise((resolve, reject) => {
        const writer = fs.createWriteStream(audioPath);
        response.data.pipe(writer);
        writer.on("finish", () => {
          console.log(chalk.green("File write completed successfully"));
          resolve();
        });
        writer.on("error", (err) => {
          console.error(chalk.red(`Error writing file: ${err.message}`));
          reject(err);
        });
      });

      console.log(chalk.green(`Successfully saved audio for "${word}"`));
      return `[sound:${filename}]`;
    }

    function readTSV(filePath) {
      const OUT_FILE_PATH = path.resolve(
        path.dirname(filePath),
        `${path.basename(filePath, ".tsv")}_pronunciations.tsv`
      );

      try {
        if (fs.existsSync(OUT_FILE_PATH)) {
          fs.unlinkSync(OUT_FILE_PATH);
        }
      } catch (err) {
        console.error(err);
      }

      return new Promise((resolve, reject) => {
        const results = [];
        fs.createReadStream(filePath)
          .pipe(fastcsv.parse({ headers: false, delimiter: "\t" }))
          .on("data", ([guid, front, back]) => {
            if (!guid || !front || !back) return; // Skip metadata lines
            results.push([guid, front, back]);
          })
          .on("end", async () => {
            try {
              let records = [];
              let missedWords = [];
              for (const data of results.filter(Boolean)) {
                const [guid, front, back] = data;
                const audioEntry = await fetchPronunciation(front);
                if (!audioEntry) missedWords.push(front);
                records.push({
                  guid,
                  front: front + (audioEntry ?? ""),
                  back: back,
                });
              }

              console.info(`Processed ${records.length} words.`);
              // log missed words
              missedWords.length &&
                console.info(
                  `${missedWords.length} words could not be found in Forvo:\n`,
                  `${chalk.red(missedWords.join("\n"))}`
                );
              console.info(
                chalk.blue(`Writing to ${chalk.bold(OUT_FILE_PATH)}`)
              );
              const writeStream = fs.createWriteStream(OUT_FILE_PATH, {
                flags: "a",
              });
              writeStream.write("#separator:tab\n#html:true\n#guid column:1\n"); // Prepend the lines
              fastcsv
                .write(records, {
                  headers: false,
                  delimiter: "\t",
                })
                .pipe(writeStream)
                .on("finish", () => {
                  console.log("...Done");
                  resolve();
                })
                .on("error", reject);
            } catch (error) {
              reject(error);
            }
          })
          .on("error", reject);
      });
    }

    readTSV(filePath);
  });

program.configureOutput({
  outputError: (str, write) => write(chalk.red(str)),
});
program.showHelpAfterError();
program.parse(process.argv);
