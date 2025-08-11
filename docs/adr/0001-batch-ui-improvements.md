### ADR 0001: Batch UI improvements (Play, Edit, Auto-refresh, Default query)

Status: Accepted
Date: 2025-08-11

## Context

Users requested better feedback and interactivity in the batch enrichment workflow:

1. A default search query tuned to short-interval cards.
2. Clear feedback and behavior for the "Enrich All" button.
3. Ability to preview audio from the batch table.
4. Ability to edit the note field from the batch table.
5. Refresh the results after batch processing to reflect new state.

## Decision

- Set default search query to `prop:ivl<21` in both the batch dialog and the fallback in `ForvoEnricher`.
- Connect the "Enrich All" button to a background `CollectionOp` and show progress with immediate UI feedback.
- Add a Play ▶︎ button to each row to play `[sound:...]` audio from the `target_field` via `aqt.sound.av_player.play_file()`.
- Change Edit action to open Anki's standard Browser editor focused on the note via `dialogs.open("Browser", mw)` and `nid:<id>` search.
- After successful batch processing, automatically re-run the current search to rebuild the table view.
- Provide Play button visual feedback: toggles to ⏸ while playing, restores to ▶︎ when stopped or after a safety timeout.
- Live per-row status updates during "Enrich All": update Audio and Status cells as each note finishes processing.

## Consequences

- Improved usability and faster iteration when curating audio.
- Background operations remain safe via Anki’s `QueryOp`/`CollectionOp` pattern.
- Post-processing refresh ensures the table reflects current note state.
- Slightly more code in `ForvoBatchDialog` to manage per-row actions and refresh.

## Implementation references

- Files touched:
  - `src/anki_forvo_enrich/batch_dialog.py`
  - `src/anki_forvo_enrich/__init__.py`
  - `src/anki_forvo_enrich/config.json`
