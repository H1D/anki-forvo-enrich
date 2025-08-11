"""
Dialog UI for batch Forvo enrichment in Anki.
"""
import os
import re
from aqt import mw
from aqt import dialogs
from aqt.qt import QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTableWidget, QHeaderView, QTableWidgetItem, QTextEdit, QTimer, Qt
from aqt.utils import showInfo, qconnect
from aqt.operations import QueryOp
from aqt.sound import av_player
from aqt import sound as aqt_sound
from .config import load_config

class ForvoBatchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.target_field = self.config.get('target_field', 'Front')
        self._play_buttons_by_nid = {}
        self._currently_playing_nid = None
        self.setWindowTitle("Forvo Batch Enrich")
        self.resize(800, 600)
        try:
            # Make dialog modeless
            self.setWindowModality(Qt.NonModal)  # type: ignore
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)  # type: ignore
        except Exception:
            pass
        self.setup_ui()
        # Auto-run search on open
        QTimer.singleShot(0, self.search_notes)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Search query input and buttons
        query_layout = QHBoxLayout()
        query_layout.setSpacing(5)
        # Default to due-in-20-days property query if not configured
        self.query_input = QLineEdit(self.config.get('default_search_query', 'prop:ivl<21'))
        self.search_btn = QPushButton("Search")
        self.enrich_all_btn = QPushButton("Enrich All")
        self.enrich_all_btn.setEnabled(False)
        query_layout.addWidget(self.query_input)
        query_layout.addWidget(self.search_btn)
        query_layout.addWidget(self.enrich_all_btn)
        layout.addLayout(query_layout)

        # Results count label
        self.results_label = QLabel("No cards found")
        layout.addWidget(self.results_label)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)  # Word, Audio, Actions, Status
        self.results_table.setHorizontalHeaderLabels(["Word", "Audio", "Actions", "Status"])
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.results_table.setColumnWidth(1, 80)
        self.results_table.setColumnWidth(2, 220)
        self.results_table.setColumnWidth(3, 160)
        layout.addWidget(self.results_table)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

        self.setLayout(layout)

        # Connect signals
        qconnect(self.search_btn.clicked, self.search_notes)
        qconnect(self.enrich_all_btn.clicked, self.start_enrichment)

    def _ensure_api_and_lang(self):
        """Ensure API key and language are available in config; prompt if missing."""
        from aqt.utils import getText
        cfg = load_config()
        api_key = cfg.get('api_key', '')
        if not api_key:
            res = getText("Enter your Forvo API key:", default='')
            if not res or not res[0].strip():
                return None, None
            api_key = res[0].strip()
            cfg['api_key'] = api_key
        lang = cfg.get('language', '')
        if not lang:
            res = getText("Enter the ISO 639-1 language code (e.g., 'en'):", default='')
            if not res or not res[0].strip():
                return None, None
            lang = res[0].strip()
            cfg['language'] = lang
        # Persist any updates
        try:
            from .config import save_config
            save_config(cfg)
        except Exception:
            pass
        return api_key, lang

    def start_enrichment(self):
        """Enrich all currently listed notes with progress and feedback."""
        from aqt.utils import showInfo, showWarning
        from aqt.operations import CollectionOp
        from . import enricher
        # Must have search results
        note_ids = getattr(self, 'current_note_ids', [])
        if not note_ids:
            showWarning("No notes to enrich. Run a search first.")
            return
        # Ensure required settings
        api_key, lang = self._ensure_api_and_lang()
        if not api_key or not lang:
            return
        # Disable controls and show progress
        self.enrich_all_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.results_label.setText("Processing notes...")
        from aqt import mw as _mw
        _mw.progress.start(immediate=True)
        _mw.progress.update(label="Processing notes...", value=0, max=len(note_ids))

        def on_success(_changes):
            _mw.progress.finish()
            showInfo(getattr(enricher, 'last_operation_message', "Enrichment completed."))
            self.search_btn.setEnabled(True)
            # Keep Enrich All disabled until next search to avoid reusing stale ids
            self.enrich_all_btn.setEnabled(False)
            # Refresh results to reflect new audio/status
            self.results_label.setText("Refreshing results...")
            self.search_notes()

        def on_failure(exc: Exception):
            _mw.progress.finish()
            showWarning(f"Error during processing: {str(exc)}")
            self.search_btn.setEnabled(True)
            self.enrich_all_btn.setEnabled(True)
            self.results_label.setText("Error during processing")

        # progress callback to update table rows as notes finish
        row_index_by_nid = {nid: idx for idx, nid in enumerate(note_ids)}
        def progress_callback(nid, idx, ok, message):
            row = row_index_by_nid.get(nid)
            if row is None:
                return
            # Update audio and status cells
            target_field = self.target_field
            note = mw.col.get_note(nid)
            text = note[target_field] if target_field in note else ""
            has_audio = '[sound:' in text
            self.results_table.setItem(row, 1, QTableWidgetItem("Yes" if has_audio else "No"))
            self.results_table.setItem(row, 3, QTableWidgetItem(message))

        op = CollectionOp(
            parent=mw,
            op=lambda col: enricher.process_notes(col, note_ids, api_key, lang, progress_callback)
        )
        op.success(on_success)
        op.failure(on_failure)
        op.run_in_background()

    def enrich_single_note(self, nid, row):
        from . import enricher
        config = load_config()
        api_key = config.get('api_key', '')
        lang = config.get('language', '')
        target_field = config.get('target_field', 'Front')
        col = mw.col
        success, msg = enricher.enrich_single_note(col, nid, api_key, lang, target_field)
        note = col.get_note(nid)
        word = note[target_field] if target_field in note else ""
        has_audio = '[sound:' in word
        self.results_table.setItem(row, 0, QTableWidgetItem(word))
        self.results_table.setItem(row, 1, QTableWidgetItem("Yes" if has_audio else "No"))
        self.results_table.setItem(row, 3, QTableWidgetItem(msg))

    def _reset_play_button(self, nid):
        btn = self._play_buttons_by_nid.get(nid)
        if btn:
            btn.setText("▶︎")
            btn.setEnabled(True)

    def play_note_audio(self, nid, btn=None):
        target_field = self.target_field
        note = mw.col.get_note(nid)
        text = note[target_field] if target_field in note else ""
        # Match [sound:filename] and capture filename
        m = re.search(r"\[sound:([^\]]+)\]", text)
        if not m:
            showInfo("No audio on this note.")
            return
        filename = m.group(1)
        media_dir = mw.col.media.dir()
        file_path = os.path.join(media_dir, filename)
        # Toggle behavior: stop if same nid is playing
        if self._currently_playing_nid == nid:
            try:
                av_player.stop_and_clear_queue()
            except Exception:
                pass
            self._reset_play_button(nid)
            self._currently_playing_nid = None
            return
        # Otherwise, start playback
        if not os.path.exists(file_path):
            showInfo(f"Audio file not found: {filename}")
            return

        # Reset previously playing button
        if self._currently_playing_nid is not None:
            self._reset_play_button(self._currently_playing_nid)

        # Track the button for this nid
        if btn is None:
            btn = self._play_buttons_by_nid.get(nid)
        if btn:
            btn.setText("⏸")
            btn.setEnabled(True)
        self._currently_playing_nid = nid
        av_player.play_file(file_path)

        # Best-effort revert after a short duration (typical Forvo clips are short)
        def revert_if_still_current():
            if self._currently_playing_nid == nid:
                self._reset_play_button(nid)
                self._currently_playing_nid = None
        QTimer.singleShot(8000, revert_if_still_current)

    def open_in_browser_editor(self, nid):
        """Open Anki's Browser focused on the given note id to use the standard editor."""
        try:
            b = dialogs.open("Browser", mw)
            # Raise & focus the Browser
            b.activateWindow()
            b.raise_()
            # Set search to target the specific note and trigger search
            try:
                b.form.searchEdit.lineEdit().setText(f"nid:{nid}")
                b.onSearchActivated()
            except Exception:
                # Fallback for older APIs
                if hasattr(b, "search"):
                    b.search(f"nid:{nid}")
        except Exception:
            # As a last resort, notify user
            showInfo("Could not open Browser editor for this note.")

    def search_notes(self):
        query = self.query_input.text()
        self.results_label.setText("Searching...")
        def do_search(col):
            return col.find_notes(query)
        def on_done(note_ids):
            self.results_table.setRowCount(0)
            if not note_ids:
                self.results_label.setText("No cards found")
                self.enrich_all_btn.setEnabled(False)
                return
            self.results_label.setText(f"Found {len(note_ids)} cards")
            self.enrich_all_btn.setEnabled(True)
            # Store note ids for Enrich All
            self.current_note_ids = note_ids
            for idx, nid in enumerate(note_ids):
                note = mw.col.get_note(nid)
                word = note[self.target_field] if self.target_field in note else ""
                has_audio = '[sound:' in word
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                self.results_table.setItem(row, 0, QTableWidgetItem(word))
                self.results_table.setItem(row, 1, QTableWidgetItem("Yes" if has_audio else "No"))
                # Actions widget with Play, Enrich, Edit
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                play_btn = QPushButton("▶︎")
                play_btn.setToolTip("Play audio")
                self._play_buttons_by_nid[nid] = play_btn
                play_btn.clicked.connect(lambda _, nid=nid, b=play_btn: self.play_note_audio(nid, b))
                enrich_btn = QPushButton("Enrich")
                enrich_btn.clicked.connect(lambda _, nid=nid, row=row: self.enrich_single_note(nid, row))
                edit_btn = QPushButton("Edit")
                edit_btn.setToolTip("Open in Browser editor")
                edit_btn.clicked.connect(lambda _, nid=nid: self.open_in_browser_editor(nid))
                actions_layout.addWidget(play_btn)
                actions_layout.addWidget(enrich_btn)
                actions_layout.addWidget(edit_btn)
                self.results_table.setCellWidget(row, 2, actions_widget)
                # Leave initial status empty; it will update during processing
                self.results_table.setItem(row, 3, QTableWidgetItem(""))
        op = QueryOp(parent=mw, op=do_search, success=on_done)
        op.run_in_background() 