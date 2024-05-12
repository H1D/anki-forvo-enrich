const axios = require("axios");
const cheerio = require("cheerio");
const csv = require("csv-parser");
const fs = require("fs");
const path = require("path");
const createCsvWriter = require("csv-writer").createObjectCsvWriter;
const ISO6391 = require("iso-639-1");
const os = require("os");
const chalk = require("chalk");

function red(strings, ...values) {
  let str = strings[0];
  for (let i = 0; i < values.length; i++) {
    str += values[i] + strings[i + 1];
  }
  console.log(chalk.red(str));
}

function blue(strings, ...values) {
  let str = strings[0];
  for (let i = 0; i < values.length; i++) {
    str += values[i] + strings[i + 1];
  }
  console.log(chalk.blue(str));
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
    console.error(red`Unsupported platform`);
    process.exit(1);
}

console.info(blue`Dir for audio files: ${AUDIO_DIR}`);

async function fetchPronunciation(word, retryCount = 0) {
  try {
    const url = `https://forvo.com/word/${encodeURIComponent(word)}/#${lang}`;
    console.log(`Fetching pronunciation from: ${url}`);
    const response = await axios.get(url);
    const $ = cheerio.load(response.data);
    const audioLink = $(".play").attr("onclick"); // Simplified extraction
    const mp3Regex = /Play\(\d+,'[^']+','([^']+)/;
    const matches = mp3Regex.exec(audioLink);
    if (matches && matches[1]) {
      const decodedString = Buffer.from(matches[1], "base64").toString("utf-8");
      const audioUrl = `https://audio00.forvo.com/ogg/${decodedString}`;
      console.log(`Found audio URL: ${audioUrl}`);
      return downloadAudio(audioUrl, word);
    }
  } catch (error) {
    if (error?.response?.status === 404) {
      console.info(blue`Can't find pronunciation for "${word}"`);
      return;
    }
    if (retryCount < 5) {
      // Maximum of 5 retries
      await new Promise((resolve) =>
        setTimeout(resolve, 1000 * (retryCount + 1))
      ); // Delay increases with each retry
      return fetchPronunciation(word, retryCount + 1);
    } else {
      console.error(red`Error fetching pronunciation for "${word}": ${error}`);
    }
  }
}

function downloadAudio(url, word) {
  const audioPath = path.resolve(AUDIO_DIR, `./${word}.mp3`);
  return axios({
    method: "get",
    url: url,
    responseType: "stream",
  }).then((response) => {
    console.log(`Downloading audio for ${word} to ${audioPath}`);
    response.data.pipe(fs.createWriteStream(audioPath));
    return `${word};[sound:${word}.mp3]`;
  });
}

function readCSV(filePath) {
  const OUT_FILE_PATH = path.resolve(
    path.dirname(filePath),
    `${path.basename(filePath, ".csv")}_pronunciations.csv`
  );

  const csvWriter = createCsvWriter({
    path: OUT_FILE_PATH,
    header: [
      { id: "word", title: "WORD" },
      { id: "translation", title: "TRANSLATION" },
    ],
    append: true, //avoid adding header
  });

  fs.createReadStream(filePath)
    .pipe(csv({ headers: false }))
    .on("data", (data) => results.push(data))
    .on("end", async () => {
      console.info(blue`CSV file successfully processed`);
      console.log(results);
      const records = await Promise.all(
        results.filter(Boolean).map(async (data) => {
          const audioEntry = await fetchPronunciation(data[0]);
          return {
            word: audioEntry ?? data[0],
            translation: data[1],
          };
        })
      );

      console.info(blue`Writing to ${OUT_FILE_PATH}`);
      csvWriter.writeRecords(records).then(() => {
        console.log("...Done");
      });
    });
}

// Main execution
const filePath = process.argv[2];
let lang = process.argv[3]; // No default value

if (!filePath) {
  console.error(red`Please provide a file path as an argument`);
  process.exit(1);
}

if (lang && !ISO6391.validate(lang)) {
  console.error(
    red`Unsupported language. Please provide a valid ISO 639-1 language code.`
  );
  process.exit(1);
}

const results = [];
try {
  if (fs.existsSync(OUT_FILE_PATH)) {
    fs.unlinkSync(OUT_FILE_PATH);
  }
} catch (err) {
  console.error(err);
}
readCSV(filePath, lang);
