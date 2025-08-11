### Anki Forvo Enrich — Technical Overview

This document provides an overview of the add-on’s architecture, key modules, execution flow, and integration points with Anki and Qt.

## High-level architecture

- **UI layer**: `src/anki_forvo_enrich/batch_dialog.py`

  - Defines `ForvoBatchDialog` (Qt dialog) for batch operations.
  - Provides search input, results table, and actions (Play, Enrich, Edit, Enrich All).

- **Core logic**: `src/anki_forvo_enrich/__init__.py`

  - Defines `ForvoEnricher` that implements background search and batch processing using Anki operations.
  - Creates the Tools menu entry to open the batch dialog.

- **Configuration**: `src/anki_forvo_enrich/config.py`, `src/anki_forvo_enrich/config.json`
  - Loads/saves add-on config via Anki’s add-on manager.
  - Holds defaults like `default_search_query`, `target_field`, `language`, and optional `articles`.

## Key modules and responsibilities

- `ForvoBatchDialog`

  - Search using Anki’s query syntax (default `prop:ivl<21`, configurable via `default_search_query`).
  - Displays results in a `QTableWidget` with columns: Word, Audio, Actions, Status.
  - Per-row actions:
    - Play ▶︎: plays audio found in `target_field`’s `[sound:...]` tag via `aqt.sound.av_player.play_file()`.
    - Enrich: enriches a single note from the table.
    - Edit: opens a small text editor modal to update the `target_field` and persists the note.
  - Enrich All: processes all currently listed notes; disables controls during processing, shows progress, and refreshes the table when done.

- `ForvoEnricher`

  - Ensures `api_key` and `language` are available (prompts user if missing and persists).
  - Uses `QueryOp` for non-collection work (finding notes) and `CollectionOp` for collection mutations (processing notes).
  - Updates Anki progress via `mw.progress` with cancellation callback support.
  - Adds audio by downloading a best-rated pronunciation from Forvo and appending a `[sound:filename]` tag to `target_field`.

- Forvo interaction
  - API base: `https://apifree.forvo.com`.
  - Selects the highest-rated pronunciation when multiple results are available.
  - Audio is saved into the collection media directory; resulting tag is `[sound:<filename>]`.

## Execution flow

1. User opens Tools → Forvo Enrich, which launches `ForvoBatchDialog`.
2. User searches notes. The dialog calls `Collection.find_notes(query)` in a background `QueryOp` and populates the table on success.
3. User can enrich single notes or click Enrich All:
   - Enrich All triggers a `CollectionOp` that iterates notes, enriching each and updating progress.
   - On completion, a message is shown and the dialog re-runs the search to reflect latest state.

## Configuration keys

- `api_key` (string): Forvo API key. Prompted if empty.
- `language` (string): ISO 639-1 language code (e.g., `en`). Prompted if empty.
- `default_search_query` (string): default Anki search query shown in the batch dialog.
- `target_field` (string): note field to enrich and inspect for audio.
- `skip_if_has_audio` (bool): if enabled, notes with existing audio are skipped during enrichment.
- `articles` (object): mapping from language code to list of articles to strip when querying Forvo.

Example (`src/anki_forvo_enrich/config.json`):

```json
{
  "api_key": "",
  "language": "nl",
  "default_search_query": "prop:ivl<21",
  "target_field": "Front",
  "skip_if_has_audio": true,
  "articles": {
    "nl": ["de", "het", "een"],
    "fr": ["le", "la", "les", "un", "une", "des"],
    "de": ["der", "die", "das", "ein", "eine"]
  }
}
```

## Notable Qt/Anki integration points

- `aqt.operations.QueryOp` and `aqt.operations.CollectionOp` for background tasks and collection writes.
- `aqt.utils.qconnect` used to connect Qt signals.
- `aqt.sound.av_player.play_file(path)` to play local media files.
- `mw.col.find_notes(query)` and `mw.col.get_note(nid)` for note access.
- `mw.col.media.dir()` to resolve media directory for audio files.

## Error handling and UX

- Long-running operations display a progress bar and optionally a cancel button.
- Exceptions during network or file I/O display warnings and set a Status message for the row.
- After Enrich All completes, the table refreshes to reflect new audio and statuses.

## Development notes

- The code relies on Anki’s runtime modules (`aqt`, `anki`). Lint/mypy errors about missing stubs are expected outside Anki.
- Use a project-specific virtualenv for Python development.
- For reference docs see:
  - Anki add-on guide: [`https://addon-docs.ankiweb.net`](https://addon-docs.ankiweb.net)
  - Qt for Python (PySide/PyQt) docs: [`https://doc.qt.io/`](https://doc.qt.io/)
