# Anki Forvo Enrich

Enrich your Anki flashcards with pronunciations from Forvo.

## Configuration

You can configure the tool using either command-line arguments or environment variables. To use environment variables:

1. Copy the example environment file:

```bash
wget https://raw.githubusercontent.com/H1D/anki-forvo-enrich/main/.env.example -O .env
```

2. Edit `.env` with your settings.

### Configuration Options

| Argument/Option  | Environment Variable | Description                         | Default                     | Required |
| ---------------- | -------------------- | ----------------------------------- | --------------------------- | -------- |
| `<path-to-file>` | -                    | Path to Anki flashcards export file | -                           | Yes      |
| `[lang]`         | `LANGUAGE`           | ISO 639-1 language code             | -                           | Yes      |
| `-k, --key`      | `FORVO_API_KEY`      | Forvo API key                       | -                           | Yes      |
| `-u, --user`     | `ANKI_USER`          | Anki user name                      | "User 1"                    | No       |
| `-a, --articles` | `ARTICLES`           | Comma-separated list of articles    | -                           | No       |
| -                | `FORVO_API_BASE`     | Forvo API base URL                  | "https://apifree.forvo.com" | No       |

Command-line arguments take precedence over environment variables.

## Usage

Basic usage with command-line arguments:

```bash
npx anki-forvo-enrich <path-to-file> <lang> -k <your-api-key>
```

Using environment variables (after setting up .env):

```bash
npx anki-forvo-enrich <path-to-file>
```

## Examples

1. Using command-line arguments:

```bash
npx anki-forvo-enrich dutch_cards.txt nl -k your-api-key -a "de,het,een"
```

2. Using environment variables:

```bash
# After setting up .env with your configuration:
npx anki-forvo-enrich dutch_cards.txt
```

## Notes

- The tool expects Anki flashcard files in "Notes as Plain text" format (no HTML, no tags included)
- Audio files are automatically saved to your Anki media collection folder
- The tool will skip downloading if an audio file already exists for a word

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

   <img width="600" alt="Screenshot" src="https://github.com/H1D/anki-forvo-enrich/assets/697625/aa931d68-5f6d-44a3-bafa-5356dbcf9da4">

2. Run the script using the following command:

   ```bash
   npx your-script-name \<path-to-file\> \<lang\> --articles \<list\> --key \<forvo-api-key\>
   ```

Replace:

- `<path-to-file>` with the path to your exported Anki file.
- `<lang>` with the ISO 639-1 language code.
- `<list>` with a comma-separated list of articles for the language (optional).
- `<forvo-api-key>` with your Forvo API key.

Example:

```bash
npx your-script-name /tmp/Spanish.txt es --articles "el,la" --key your-api-key
```

3. Now audio file are downloaded and notes are updated to include audio. Use Anki `File -> Import` to import notes back. First time you do this I recommend to try it on deck copy. Make sure settings are correct:
   <img width="600" alt="Image" src="https://github.com/user-attachments/assets/df120a9b-3a68-40b0-a865-2bcb11e5cc5b" />

## Notes

- Forvo API Key: The Forvo API key is mandatory. It costs $2/month with a minimum subscription duration of 6 months. Learn more about pricing on the Forvo API plans page (https://api.forvo.com/plans-and-pricing/).

## Libs Used

- axios: For making HTTP requests.
- cheerio: For parsing HTML and extracting data.
- fast-csv: For reading and writing deck files.
- fs: For handling file system operations.
- path: For handling file paths.
- ISO-639-1: For validating ISO 639-1 language codes.
- os: For handling OS-specific operations.
- chalk: For colored console output.
- commander: For command-line interface options.
