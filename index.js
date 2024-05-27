#!/usr/bin/env node

const axios = require("axios");
const cheerio = require("cheerio");
const fastcsv = require("fast-csv");
const fs = require("fs");
const path = require("path");
const ISO6391 = require("iso-639-1");
const os = require("os");
const chalk = require("chalk");
const { Command } = require("commander");
const packageJson = require("./package.json");

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
          "Library/Application Support/Anki2/User 1/collection.media/"
        );
        break;
      case "win32":
        AUDIO_DIR = path.resolve(
          os.homedir(),
          "AppData/Roaming/Anki2/User 1/collection.media/"
        );
        break;
      case "linux":
        AUDIO_DIR = path.resolve(
          os.homedir(),
          ".local/share/Anki2/User 1/collection.media/"
        );
        break;
      default:
        console.error(chalk.red(`Unsupported platform`));
        process.exit(1);
    }

    console.info(chalk.blue(`Dir for audio files: ${AUDIO_DIR}`));

    async function fetchPronunciation(word, retryCount = 0) {
      try {
        const url = `https://forvo.com/word/${encodeURIComponent(
          word
        )}/#${lang}`;
        console.log(`---${word}---`);
        console.log(`Looking for pronunciations: ${url}`);
        const response = await axios.get(url);
        const $ = cheerio.load(response.data);
        const audioLink = $(`#language-container-${lang} .play`).attr(
          "onclick"
        ); // Simplified extraction
        const mp3Regex = /Play\(\d+,'[^']+','([^']+)/;
        const matches = mp3Regex.exec(audioLink);
        if (matches && matches[1]) {
          const decodedString = Buffer.from(matches[1], "base64").toString(
            "utf-8"
          );
          const audioUrl = `https://audio00.forvo.com/ogg/${decodedString}`;
          console.log(`Found audio URL: ${audioUrl}`);
          return downloadAudio(audioUrl, word);
        }
      } catch (error) {
        if (error?.response?.status === 404) {
          if (articles.length) {
            const articleRegex = new RegExp(`\\b${articles.join("|")}\\b`, "i");
            const articleMatch = articleRegex.exec(word);
            if (articleMatch) {
              const article = articleMatch[0];
              console.log(`Retrying without article: ${article}`);
              return fetchPronunciation(
                word.replace(article, "").trim(),
                retryCount
              );
            }
          }

          console.info(chalk.blue(`Can't find pronunciation for "${word}"`));
          return;
        }
        if (retryCount < 5) {
          // Maximum of 5 retries
          await new Promise((resolve) =>
            setTimeout(resolve, 1000 * (retryCount + 1))
          ); // Delay increases with each retry
          return fetchPronunciation(word, retryCount + 1);
        } else {
          console.error(
            chalk.red(`Error fetching pronunciation for "${word}": ${error}`)
          );
        }
      }
    }

    function downloadAudio(url, word) {
      const fileExtension = path.extname(new URL(url).pathname);
      const filename = `${word}_${lang}${fileExtension}`;
      const audioPath = path.resolve(AUDIO_DIR, `./${filename}`);
      return axios({
        method: "get",
        url: url,
        responseType: "stream",
      }).then((response) => {
        console.log(`Downloading audio for "${word}" to ${audioPath}`);
        response.data.pipe(fs.createWriteStream(audioPath));
        return `[sound:${filename}]`;
      });
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

      fs.createReadStream(filePath)
        .pipe(fastcsv.parse({ headers: false, delimiter: "\t" }))
        .on("data", ([guid, front, back]) => {
          if (!guid || !front || !back) return; // Skip metadata lines
          results.push([guid, front, back]);
        })
        .on("end", async () => {
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
          console.info(chalk.blue(`Writing to ${chalk.bold(OUT_FILE_PATH)}`));
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
            });
        });
    }

    const results = [];
    readTSV(filePath);
  });

program.configureOutput({
  outputError: (str, write) => write(chalk.red(str)),
});
program.showHelpAfterError();
program.parse(process.argv);
