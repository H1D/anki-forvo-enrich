# Anki Forvo Enrich

An Anki addon that enriches your flashcards with pronunciations from Forvo.

## Features

- Automatically fetch pronunciations from Forvo for your flashcards
- Configurable target field for adding pronunciations
- Saves API key and language preferences
- Skip cards that already have audio
- Detailed logging for troubleshooting

## Installation

1. Download the addon from AnkiWeb (link to be added)
2. In Anki, go to Tools > Add-ons > Install from file
3. Select the downloaded .ankiaddon file
4. Restart Anki

## Usage

1. Get a Forvo API key from [Forvo API](https://api.forvo.com/)
2. In Anki, go to Tools > Enrich Notes with Forvo
3. Enter your Forvo API key (will be saved for future use)
4. Enter the language code (e.g., 'en' for English, 'es' for Spanish)
5. Enter a search query to find notes to enrich (default: "tag:forvo")

The addon will process your notes and add pronunciations from Forvo.

## Configuration

You can configure the addon by editing the config.json file:

```json
{
  "api_key": "", // Your Forvo API key
  "language": "", // Default language code
  "default_search_query": "tag:forvo", // Default search query
  "target_field": "Front", // Field to add pronunciations to
  "skip_if_has_audio": true // Skip notes that already have audio
}
```

## Troubleshooting

Check the addon's log file (anki_forvo_enrich.log) for detailed error messages and debugging information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Thanks to Forvo for providing the pronunciation API
- Thanks to the Anki team for creating an amazing flashcard platform
