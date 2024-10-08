Code and docs written by ChatGPT. Proofread and edits by human.

## What it is

This script fetches pronunciation audio for words in Anki flashcards from forvo.com. It processes Anki flashcard export files in plain text format and adds pronunciation audio links to each flashcard. Anki will automatically play those audio.

## Prerequisites

- [Node.js](https://nodejs.org/en) installed on your system.
- [Anki app](https://apps.ankiweb.net/) installed on your system.
- You cards front include only the word you want to fetch pronunciation for. Articles are **allowed** (see usage for details).

## Usage

1. Export your Anki flashcards. Use following options:

   - make sure all card **front** should be in **target language** (the one we want to fetch pronunciation for)
   - "Notes as in Plain text" format
   - all checkboxes unchecked (except for "Include unique identifier")<img width="779" alt="Screenshot" src="https://github.com/H1D/anki-forvo-enrich/assets/697625/aa931d68-5f6d-44a3-bafa-5356dbcf9da4">

1. Run the script using the following command:

   ```bash
   npx anki-forvo-enrich <path-to-file> <lang> --articles <list>
   ```

   Replace `<path-to-file>` with the path to your exported Anki file and `<lang>` with the [ISO 639-1 language code](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) (en/es/nl...). Articles are optional **comma separated** list of article for `<lang>`. If no article is provided, the script will attempt to fetch pronunciations ignoring articles if needed.
   
   **Example:** `npx anki-forvo-enrich /tmp/Spanish.txt es --articles "el,la"`

1. After processing, a new file with pronunciation links will be generated in the same directory as your original file. See script output for details.
1. Import this new file back into Anki using the "Import" feature. You can either use new deck or import into existing deck, existing cards will be updated.

<img width="297" alt="Screenshot" src="https://github.com/H1D/anki-forvo-enrich/assets/697625/f7e2c157-c5a0-4198-8109-71ef7612c4cc"><br/>

<img width="460" alt="Screenshot" src="https://github.com/H1D/anki-forvo-enrich/assets/697625/6a871448-6708-477f-9f83-43b448170d3a">

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
