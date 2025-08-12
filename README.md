# Anki Forvo Enrich (Anki add-on, Python)

Enrich your Anki flashcards with pronunciations from Forvo, directly inside Anki.

## Project layout

- Source code: `src/anki_forvo_enrich/`
- Config file used by the add-on: `src/anki_forvo_enrich/config.json`

## Requirements

- Anki desktop installed
- Python 3.9+ (Anki bundles Python but a virtualenv is used for development)
- A Forvo API key

Install development dependencies into a per-project venv:

```bash
cd anki-forvo-enrich
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Development

- Run static checks:

```bash
bash setup.sh
```

This will install deps (if not installed) and run `mypy` against `src/anki_forvo_enrich/`.

## Installation (into Anki)

1. Create a directory in your Anki add-ons folder, e.g. `anki-forvo-enrich`.
2. Copy the contents of `src/anki_forvo_enrich/` into that folder.
3. Restart Anki.

Anki will load the add-on via `__init__.py`. A menu entry "Forvo Enrich" will appear under Tools.

## Usage

1. In Anki, go to Tools > Forvo Enrich
2. Enter your Forvo API key and language when prompted (saved in the add-on config)
3. Use the batch dialog to search notes and enrich them

## Configuration

The add-on stores configuration managed by Anki (`mw.addonManager`) and reads defaults from `src/anki_forvo_enrich/config.json`.

Key options:

- `api_key`: Forvo API key
- `language`: default ISO 639-1 language code
- `default_search_query`: search used to find notes to enrich
- `target_field`: field to append audio to
- `skip_if_has_audio`: skip notes that already contain audio
- `articles`: per-language articles that will be stripped when querying Forvo

## Notes

- This repository now only contains the Python Anki add-on. The previous Node/CLI workflow and `addon/` staging folder have been removed.
- Logs and build artifacts are ignored via `.gitignore`.
