Code and docs written by ChatGPT. Proofread and edits by human.

## What it is

This script fetches pronunciation audio for words in Anki flashcards from forvo.com. It processes Anki flashcard export files in plain text format and adds pronunciation audio links to each flashcard.

## Prerequisites

- Node.js installed on your system.
- Anki installed on your system.
- You cards front include only the word you want to fetch pronunciation for. Articles **allowed** (see usage for details).

## Usage

1. Export your Anki flashcards. Use following options:
   - "Notes as in Plain text" format
   - all checkboxes unchecked (except for "Include unique identifier")
1. Run the script using the following command:

   ```bash
   npx your-script-name <path-to-file> <lang> --articles <list>
   ```

   Replace `<path-to-file>` with the path to your exported Anki file and `<lang>` with the ISO 639-1 language code. Articles are optional comma separated list of article for `<lang>`. If no article is provided, the script will attempt to fetch pronunciations ignoring articles if needed.

1. After processing, a new file with pronunciation links will be generated in the same directory as your original file. See script output for details.
1. Import this new file back into Anki using the "Import" feature. You can either use new deck or import into existing deck, existing cards will be updated.

## Libs Used

- [axios](https://www.npmjs.com/package/axios): For making HTTP requests.
- [cheerio](https://www.npmjs.com/package/cheerio): For parsing HTML and extracting data.
- [fast-csv](https://www.npmjs.com/package/fast-csv): For reading and writing deck files.
- [fs](https://nodejs.org/api/fs.html): For handling file system operations.
- [path](https://nodejs.org/api/path.html): For handling file paths.
- [ISO-639-1](https://www.npmjs.com/package/iso-639-1): For validating ISO 639-1 language codes.
- [os](https://nodejs.org/api/os.html): For handling OS-specific operations.
- [chalk](https://www.npmjs.com/package/chalk): For colored console output.
- [commander](https://www.npmjs.com/package/commander): For command-line interface options.
