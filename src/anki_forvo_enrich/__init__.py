"""
Anki Forvo Enrich Addon - Enrich your Anki cards with pronunciations from Forvo
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, cast, Protocol, Union
import traceback
import sys
import re
from bs4 import BeautifulSoup
import time

from aqt import mw
from aqt.qt import *
from aqt.qt import QAction
from aqt.utils import getText, showInfo, showWarning
from aqt.operations import CollectionOp, QueryOp, OpChanges
import requests
from anki.collection import Collection, NoteId
from anki.notes import Note

# Use Anki's logger
from aqt.utils import TR
from anki.utils import is_win, is_mac
import anki.lang
from anki.hooks import addHook
import aqt.utils

# Get Anki's logger
from anki.utils import dev_mode
from typing import Protocol, cast, List, Dict, Any, Optional, Sequence, TypeVar, Tuple, Callable
import logging

from .batch_dialog import ForvoBatchDialog
from .config import load_config, save_config

T = TypeVar('T', bound='Logger')

class Logger(Protocol):
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...

class AnkiLogger:
    def info(self, msg: str) -> None: aqt.utils.tooltip(msg)
    def warning(self, msg: str) -> None: aqt.utils.showWarning(msg)
    def error(self, msg: str) -> None: aqt.utils.showCritical(msg)

if dev_mode:
    logger: Union[logging.Logger, Logger] = logging.getLogger("anki.forvo")
else:
    logger = cast(Logger, AnkiLogger())

# Constants
FORVO_API_BASE: str = "https://apifree.forvo.com"
CONFIG_FILE: str = "config.json"

# Global variables for process control
is_processing: bool = False
should_stop: bool = False
last_operation_message: str = ""

def debug_print(msg: str) -> None:
    """Print debug message"""
    try:
        print(f"[Forvo Debug] {msg}")
    except:
        pass  # Ignore printing errors

def show_error(msg: str, e: Optional[Exception] = None) -> None:
    """Show error message to user and print traceback"""
    error_msg = f"{msg}\n\n{str(e)}" if e else msg
    debug_print(f"Error: {error_msg}")
    if e:
        debug_print(f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}")
    try:
        showWarning(error_msg)
    except:
        debug_print("Failed to show warning dialog")

def strip_html(text: str) -> str:
    """Remove HTML tags from text"""
    return BeautifulSoup(text, 'html.parser').get_text()

def get_word_versions(word: str, articles: Optional[List[str]] = None) -> List[str]:
    """Generate different versions of the word to try for pronunciation"""
    # First strip HTML
    word = strip_html(word)
    versions = set([word])
    
    # Add version without punctuation
    clean_word = word.strip().replace(".", "").replace(",", "").replace("!", "").replace("?", "").replace(";", "").replace(":", "")
    versions.add(clean_word)
    
    # Add version without articles if present
    if articles:
        for article in articles:
            if clean_word.lower().startswith(article.lower() + " "):
                versions.add(clean_word[len(article):].strip())
            if clean_word.lower().endswith(" " + article.lower()):
                versions.add(clean_word[:-len(article)].strip())
    
    return list(filter(None, versions))  # Remove empty strings

def fetch_pronunciation(word: str, lang: str, api_key: str, retry_count: int = 0) -> Optional[str]:
    """
    Fetch pronunciation from Forvo API
    Returns audio URL if successful, None otherwise
    """
    try:
        # Get config for articles
        config = load_config()
        articles = config.get('articles', {}).get(lang, [])
        
        # Try each version of the word
        for version in get_word_versions(word, articles):
            if should_stop:
                debug_print("Stopping as requested")
                return None
                
            debug_print(f"Trying version: {version}")
            
            # Check if audio file already exists
            filename = f"{version}_{lang}.mp3"
            media_dir = mw.col.media.dir()
            file_path = os.path.join(media_dir, filename)
            
            if os.path.exists(file_path):
                debug_print(f"Using existing audio file: {filename}")
                return f"[sound:{filename}]"
            
            # Try Forvo API
            url = f"{FORVO_API_BASE}/key/{api_key}/format/json/action/word-pronunciations/word/{version}/language/{lang}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                if 'items' in data and data['items']:
                    # Get the pronunciation with highest rating
                    best_pronunciation = sorted(data['items'], key=lambda k: k['rate'], reverse=True)[0]
                    audio_url = best_pronunciation['pathmp3']
                    
                    # Download and save the audio
                    audio_tag = download_audio(audio_url, filename)
                    if audio_tag:
                        return audio_tag
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    if retry_count == 0:  # Only retry once
                        debug_print("Rate limited, retrying once after 2 seconds...")
                        time.sleep(2)
                        return fetch_pronunciation(word, lang, api_key, 1)
                    else:
                        debug_print("Daily API limit reached!")
                        raise Exception("Daily Forvo API limit reached. Please try again tomorrow or use a different API key.")
                raise
        
        return None
    except Exception as e:
        show_error(f"Error fetching pronunciation for {word}", e)
        return None

def download_audio(url: str, filename: str) -> Optional[str]:
    """
    Download audio file and add it to Anki media collection
    Returns [sound:filename] tag if successful, None otherwise
    """
    try:
        # Don't try to download if the URL is already a sound tag
        if url.startswith('[sound:'):
            return url
            
        response = requests.get(url)
        response.raise_for_status()
        
        # Save to Anki media collection
        media_dir = mw.col.media.dir()
        file_path = os.path.join(media_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        return f"[sound:{filename}]"
    except Exception as e:
        show_error(f"Error downloading audio from {url}", e)
        return None

class ForvoEnricher:
    def __init__(self) -> None:
        self.is_processing: bool = False
        self.should_stop: bool = False
        self.last_operation_message: str = ""

    def update_progress(self, label: str, value: Optional[int] = None, max: Optional[int] = None) -> None:
        """Update progress dialog safely from any thread"""
        mw.taskman.run_on_main(
            lambda: mw.progress.update(
                label=label,
                value=value,
                max=max
            )
        )

    def enrich_single_note(self, col: Collection, note_id: NoteId, api_key: str, lang: str, target_field: str = "Front") -> Tuple[bool, str]:
        """
        Enrich a single note with Forvo audio. Returns (success, message).
        """
        try:
            note = col.get_note(note_id)
            word = note[target_field] if target_field in note else ""
            if not word:
                return False, "No word in field"
            if '[sound:' in word:
                return False, "Already has audio"
            audio_url = fetch_pronunciation(word, lang, api_key)
            if not audio_url:
                return False, "No pronunciation found"
            note[target_field] = f"{strip_html(word)} {audio_url}"
            col.update_note(note)
            return True, "Enriched"
        except Exception as e:
            debug_print(f"Error enriching note {note_id}: {str(e)}")
            return False, f"Error: {str(e)}"

    def process_notes(self, col: Collection, note_ids: List[NoteId], api_key: str, lang: str, progress_callback: Optional[Callable[[NoteId, int, bool, str], None]] = None) -> OpChanges:
        """Process notes in the collection"""
        try:
            self.is_processing = True
            self.should_stop = False
            total_notes = len(note_ids)
            debug_print(f"Starting to process {total_notes} notes")
            processed = 0
            errors = 0
            target_field = load_config().get('target_field', 'Front')
            for i, note_id in enumerate(note_ids):
                if self.should_stop:
                    debug_print("Process stopped by user")
                    break
                success, msg = self.enrich_single_note(col, note_id, api_key, lang, target_field)
                if success:
                    processed += 1
                else:
                    errors += 1
                self.update_progress(
                    f"Processed {processed} of {total_notes} notes, with {errors} errors.",
                    value=i + 1,
                    max=total_notes
                )
                if progress_callback:
                    # marshal UI updates to the main thread
                    mw.taskman.run_on_main(lambda nid=note_id, idx=i, ok=success, message=msg: progress_callback(nid, idx, ok, message))
            debug_print(f"Finished processing. Success: {processed}, Errors: {errors}")
            status = "stopped by user" if self.should_stop else "completed"
            self.last_operation_message = f"Process {status}. Added Forvo pronunciations to {processed}/{total_notes} notes. Errors: {errors}"
            self.is_processing = False
            self.should_stop = False
            return OpChanges()
        except Exception as e:
            self.is_processing = False
            self.should_stop = False
            debug_print(f"Fatal error during note processing: {str(e)}")
            raise

    def enrich_notes(self) -> None:
        """Main function to enrich notes with Forvo pronunciations"""
        if self.is_processing:
            showWarning("Already processing notes. Please wait or restart Anki if stuck.")
            return
            
        try:
            debug_print("Starting enrich_notes")
            config = load_config()
            
            # Only ask for API key if not in config or explicitly needed
            api_key = config.get('api_key', '')
            if not api_key:
                api_key_result = getText(
                    "Enter your Forvo API key:",
                    default=''
                )
                if not api_key_result or not api_key_result[0].strip():
                    debug_print("No API key provided")
                    return
                api_key = api_key_result[0]
                # Save API key for future use
                config['api_key'] = api_key
                save_config(config)
            
            # Only ask for language if not in config
            lang = config.get('language', '')
            if not lang:
                lang_result = getText(
                    "Enter the ISO 639-1 language code (e.g., 'en'):",
                    default=''
                )
                if not lang_result or not lang_result[0].strip():
                    debug_print("No language code provided")
                    return
                lang = lang_result[0]
                # Save language for future use
                config['language'] = lang
                save_config(config)
            
            # Use default search query from config, fall back to shorter interval property
            query = config.get('default_search_query', 'prop:ivl<21')
            debug_print(f"Using search query: {query}")

            # Start progress with indeterminate state
            mw.progress.start(immediate=True)
            mw.progress.update(label="Searching for notes...", value=None)

            # Setup cancel callback
            def on_cancel() -> bool:
                self.should_stop = True
                debug_print("User requested stop")
                return True
            
            # Use a property setter if available, otherwise keep the direct assignment
            try:
                mw.progress.set_want_cancel(on_cancel)  # type: ignore
            except AttributeError:
                mw.progress.want_cancel = on_cancel  # type: ignore

            debug_print(f"Starting note search with query: {query}")
            def on_search(col: Collection) -> List[NoteId]:
                debug_print("Executing search")
                return [NoteId(nid) for nid in col.find_notes(query)]

            def on_search_done(note_ids: List[NoteId]) -> None:
                debug_print(f"Search complete. Found {len(note_ids) if note_ids else 0} notes")
                if not note_ids:
                    mw.progress.finish()
                    showInfo("No notes found matching the search query.")
                    return
                
                # Update progress for processing phase
                self.update_progress("Processing notes...", value=0, max=len(note_ids))
                
                debug_print("Starting background processing")
                
                def on_process_success(changes: OpChanges) -> None:
                    mw.progress.finish()
                    showInfo(self.last_operation_message)
                
                def on_process_error(exc: Exception) -> None:
                    debug_print(f"Operation failed: {str(exc)}")
                    mw.progress.finish()
                    showWarning(f"Error during processing: {str(exc)}")
                
                # Use CollectionOp for proper handling of collection operations
                op = CollectionOp(
                    parent=mw,
                    op=lambda col: self.process_notes(col, note_ids, api_key, lang)
                )
                op.success(on_process_success)
                op.failure(on_process_error)
                op.run_in_background()

            # Use QueryOp for searching notes
            op = QueryOp(
                parent=mw,
                op=on_search,
                success=on_search_done
            )
            def on_failure(exc: Exception) -> None:
                mw.progress.finish()
                debug_print(f"Search failed: {str(exc)}")
            op.failure(on_failure)
            op.run_in_background()

        except Exception as e:
            debug_print(f"Fatal error in enrich_notes: {str(e)}")
            show_error("Error in enrich_notes", e)
            mw.progress.finish()

# Create a single instance of the enricher
enricher = ForvoEnricher()

def setup_menu() -> None:
    """Setup the addon menu"""
    # Create action with parent mw to ensure it's not garbage collected
    action = QAction("Forvo Enrich", mw)
    # Open batch dialog modeless, so the Browser/editor remains usable
    def open_batch_dialog() -> None:
        try:
            existing = getattr(mw, "_forvo_batch_dialog", None)
            if existing and existing.isVisible():
                existing.raise_()
                existing.activateWindow()
                return
        except Exception:
            pass
        dlg = ForvoBatchDialog(mw)
        try:
            dlg.setWindowModality(Qt.NonModal)  # type: ignore
            dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)  # type: ignore
        except Exception:
            pass
        mw._forvo_batch_dialog = dlg  # type: ignore[attr-defined]
        dlg.show()
    action.triggered.connect(open_batch_dialog)
    # Add the action directly, don't create a new one
    mw.form.menuTools.addAction(action)  # type: ignore

# Initialize the addon
setup_menu() 