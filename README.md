Here’s the corrected full Markdown text:

## What it is

This script fetches pronunciation audio for words in Anki flashcards from forvo.com. It processes Anki flashcard export files in plain text format and adds pronunciation audio links to each flashcard. Anki will automatically play those audio.

## Prerequisites

- [Node.js](https://nodejs.org/en) installed on your system.
- [Anki app](https://apps.ankiweb.net/) installed on your system.
- Your cards' front side must include only the word you want to fetch pronunciation for. Articles are **allowed** (see usage for details).
- A [Forvo API key](https://api.forvo.com/plans-and-pricing/) is required. The key costs $2/month, with a minimum duration of 6 months.

## Usage

1. Export your Anki flashcards using the following options:

   - Ensure all card **fronts** are in the **target language** (the one for which you want to fetch pronunciations).
   - Select "Notes as in Plain text" format.
   - Uncheck all boxes except for "Include unique identifier."

   <img width="779" alt="Screenshot" src="https://github.com/H1D/anki-forvo-enrich/assets/697625/aa931d68-5f6d-44a3-bafa-5356dbcf9da4">

2. Run the script using the following command:

   ```bash
   npx your-script-name <path-to-file> <lang> --articles <list> --key <forvo-api-key>
   ```

Replace:
• <path-to-file> with the path to your exported Anki file.
• <lang> with the ISO 639-1 language code.
• <list> with a comma-separated list of articles for <lang> (optional).
• <forvo-api-key> with your Forvo API key.

Example:

```bash
npx your-script-name /tmp/Spanish.txt es --articles "el,la" --key your-api-key
```

If no articles are provided, the script will attempt to fetch pronunciations while ignoring articles if necessary. 3. After processing, a new file with pronunciation links will be generated in the same directory as your original file. See script output for details. 4. Import the new file back into Anki using the “Import” feature. You can either use a new deck or import into an existing deck (existing cards will be updated).

Notes
• Forvo API Key: The Forvo API key is mandatory. It costs $2/month with a minimum subscription duration of 6 months. Learn more about pricing on the Forvo API plans page.
• Directory Structure: The script automatically checks for the required directory to save audio files based on your Anki setup. If the directory does not exist, you will need to create it manually.

Libs Used
• axios: For making HTTP requests.
• cheerio: For parsing HTML and extracting data.
• fast-csv: For reading and writing deck files.
• fs: For handling file system operations.
• path: For handling file paths.
• ISO-639-1: For validating ISO 639-1 language codes.
• os: For handling OS-specific operations.
• chalk: For colored console output.
• commander: For command-line interface options.

You can copy this Markdown and use it without issues. Let me know if you need further adjustments!
