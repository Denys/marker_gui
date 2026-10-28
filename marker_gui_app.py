"""
Marker Studio — PDF to Markdown Conversion Engine with Conversion Queue
Engineered for clean, distraction-free document conversion using marker-pdf.
Designed with quiet, utilitarian precision (no generic templates or AI-slop).
Multi-language support: English (default) & Italiano.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import psutil

from PyQt6.QtCore import (
    QObject,
    QPoint,
    QRect,
    QSize,
    QThread,
    QTimer,
    QUrl,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPen,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output"
MARKER_EXE = Path(__file__).parent / ".venv" / "Scripts" / "marker_single.exe"


# =============================================================================
# Internationalization / Translations Dictionary (EN default, IT supported)
# =============================================================================

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "MARKER STUDIO",
        "app_subtitle": "Sequential batch pipeline: PDF to Markdown + LaTeX formulas + Figures",
        "badge_idle": "QUEUE IDLE",
        "badge_processing": "PROCESSING QUEUE...",
        "badge_paused": "QUEUE PAUSED",
        "badge_stopped": "QUEUE STOPPED",
        "badge_completed": "ALL COMPLETED",

        "drop_title_default": "Drag & drop one or more PDFs here (or a whole folder)",
        "drop_hint_default": "Documents will be automatically added to the sequential conversion queue",
        "drop_title_count": "{count} document(s) in queue",
        "drop_hint_last": "Last added: {name}",

        "lbl_output_dir": "Output Directory:",
        "placeholder_output": "Directory where converted documents will be saved",
        "btn_browse": "Browse...",

        "lbl_engine": "Formula Engine:",
        "engine_local_gpu": "🚀 Local GPU (RTX 3070) — Offline, LaTeX Formulas via Surya GGUF",
        "engine_gemini_cloud": "☁️ Cloud AI (Gemini Flash) — Maximum LaTeX Accuracy via Google AI Studio",
        "engine_fast_text": "⚡ Fast Text-Only (--disable_ocr) — Fast for books/articles without formulas",
        "engine_tooltip": "Choose how mathematical equations and document layout will be processed.",

        "lbl_pages": "Pages (optional):",
        "placeholder_pages": "All (e.g. 0-5, 10)",
        "chk_remember": "Remember last paths and settings",

        "lbl_queue_title": "CONVERSION QUEUE",
        "lbl_queue_count": "({count} files)",
        "btn_add_files": "+ Add PDFs...",
        "btn_add_folder": "+ Add Folder...",
        "btn_clear_completed": "Clear Completed",
        "btn_clear_completed_tooltip": "Remove all successfully converted documents from list",
        "btn_clear_all": "Clear All",

        "th_index": "#",
        "th_name": "PDF Document",
        "th_status": "Status",
        "th_duration": "Duration",
        "th_actions": "Actions",

        "status_in_queue": "IN QUEUE",
        "status_running": "RUNNING",
        "status_paused": "PAUSED",
        "status_completed": "COMPLETED",
        "status_error": "ERROR",
        "status_cancelled": "CANCELLED",

        "btn_open_md": "📝 Markdown",
        "btn_open_folder": "📁 Folder",
        "btn_remove_item": "✕ Remove",
        "tooltip_remove_single": "Remove this item from list",

        "lbl_progress_title": "QUEUE PROGRESS",
        "progress_waiting": "Waiting...",
        "progress_paused": "Processing suspended (Paused)",
        "progress_resuming": "Resuming processing...",
        "progress_interrupted": "Queue stopped",
        "progress_all_done": "All documents completed",
        "stage_starting": "Starting OCR...",

        "lbl_console_title": "LIVE EXECUTION LOG",
        "btn_clear_log": "Clear Log",

        "btn_start_queue": "Start Conversion Queue",
        "btn_pause_queue": "⏸️ Pause Queue",
        "btn_resume_queue": "▶️ Resume Queue",
        "btn_stop_queue": "⏹️ Stop Queue",
        "btn_open_out_folder": "📁 Output Folder",

        "stage_layout": "Page Layout",
        "stage_ocr": "Page OCR",
        "stage_math": "LaTeX Formulas",
        "stage_gemini": "Gemini AI",
        "stage_tables": "Tables",
        "stage_lines": "Lines & Text",
        "stage_proc": "Processing",

        "log_welcome": "[i] Marker Studio started with automated batch queue.",
        "log_out_dir": "[i] Active output directory: {dir}",
        "log_added_files": "[+] Added {count} document(s) to queue.",
        "log_no_pdfs": "[!] No PDF files found in: {dir}",
        "log_out_updated": "[+] New output directory: {dir}",
        "log_queue_cleared": "[i] Queue cleared.",
        "log_stop_first": "[!] Stop the conversion queue first.",
        "log_empty_queue": "[!] Queue is empty. Add at least one PDF file or folder.",
        "log_start_queue": "[*] STARTING QUEUE: {count} file(s) in sequential conversion.",
        "log_paused": "[⏸️] Queue paused. Current process is suspended.",
        "log_resumed": "[▶️] Queue resumed. Processing continues.",
        "log_removed_completed": "[i] Removed {count} completed document(s) from queue.",
        "log_removed_item": "[-] Removed from queue: {name}",
        "log_cancelled_by_user": "[!] Conversion cancelled by user.",
        "log_success": "[✓] Completed successfully in {elapsed:.1f}s",
        "log_error_code": "[✗] Process error: exit code {code}",
        "log_error_exec": "[!] Execution error: {err}",
        "log_queue_finished": "[✓] QUEUE FINISHED: {completed} completed successfully, {failed} error(s) out of {total} total.",
        "dialog_add_files": "Select one or more PDF files to add to queue",
        "dialog_add_folder": "Select folder containing PDF files",
        "dialog_out_folder": "Select destination folder",
    },
    "it": {
        "app_title": "MARKER STUDIO",
        "app_subtitle": "Pipeline batch sequenziale: conversione PDF in Note Markdown + Formule LaTeX + Figure",
        "badge_idle": "CODA INATTIVA",
        "badge_processing": "ELABORAZIONE CODA...",
        "badge_paused": "CODA IN PAUSA",
        "badge_stopped": "CODA INTERROTTA",
        "badge_completed": "TUTTI COMPLETATI",

        "drop_title_default": "Trascina qui uno o più PDF (o un'intera cartella)",
        "drop_hint_default": "I documenti verranno aggiunti automaticamente alla coda di elaborazione sequenziale",
        "drop_title_count": "{count} documento/i in coda",
        "drop_hint_last": "Ultimo aggiunto: {name}",

        "lbl_output_dir": "Cartella Destinazione:",
        "placeholder_output": "Cartella dove salvare tutti i documenti convertiti",
        "btn_browse": "Sfoglia...",

        "lbl_engine": "Motore Formule:",
        "engine_local_gpu": "🚀 Locale GPU (RTX 3070) — Offline, Formule LaTeX via Surya GGUF",
        "engine_gemini_cloud": "☁️ Cloud AI (Gemini Flash) — Massima accuratezza LaTeX via Google AI Studio",
        "engine_fast_text": "⚡ Solo Testo Veloce (--disable_ocr) — Rapido per libri/articoli senza formule",
        "engine_tooltip": "Seleziona come elaborare le formule matematiche e il layout del documento.",

        "lbl_pages": "Pagine (opzionale):",
        "placeholder_pages": "Tutte (es: 0-5, 10)",
        "chk_remember": "Ricorda ultimi percorsi e preferenze utilizzate",

        "lbl_queue_title": "CODA DI CONVERSIONE",
        "lbl_queue_count": "({count} file)",
        "btn_add_files": "+ Aggiungi PDF...",
        "btn_add_folder": "+ Aggiungi Cartella...",
        "btn_clear_completed": "Pulisci Completati",
        "btn_clear_completed_tooltip": "Rimuove dalla lista tutti i documenti già convertiti con successo",
        "btn_clear_all": "Svuota Tutto",

        "th_index": "#",
        "th_name": "Documento PDF",
        "th_status": "Stato",
        "th_duration": "Durata",
        "th_actions": "Azioni",

        "status_in_queue": "IN CODA",
        "status_running": "IN CORSO",
        "status_paused": "IN PAUSA",
        "status_completed": "COMPLETATO",
        "status_error": "ERRORE",
        "status_cancelled": "ANNULLATO",

        "btn_open_md": "📝 Markdown",
        "btn_open_folder": "📁 Cartella",
        "btn_remove_item": "✕ Rimuovi",
        "tooltip_remove_single": "Rimuovi questo elemento dalla lista",

        "lbl_progress_title": "AVANZAMENTO CODA",
        "progress_waiting": "In attesa...",
        "progress_paused": "Elaborazione sospesa (Pausa)",
        "progress_resuming": "Ripresa elaborazione...",
        "progress_interrupted": "Coda interrotta",
        "progress_all_done": "Tutti i documenti completati",
        "stage_starting": "Avvio OCR...",

        "lbl_console_title": "LOG DI ESECUZIONE LIVE",
        "btn_clear_log": "Pulisci Log",

        "btn_start_queue": "Avvia Coda di Conversione",
        "btn_pause_queue": "⏸️ Pausa Coda",
        "btn_resume_queue": "▶️ Riprendi Coda",
        "btn_stop_queue": "⏹️ Interrompi Coda",
        "btn_open_out_folder": "📁 Cartella Output",

        "stage_layout": "Layout Pagine",
        "stage_ocr": "Riconoscimento Pagine",
        "stage_math": "Formule LaTeX",
        "stage_gemini": "Gemini AI",
        "stage_tables": "Tabelle",
        "stage_lines": "Linee e Testo",
        "stage_proc": "Elaborazione",

        "log_welcome": "[i] Marker Studio avviato con coda automatica.",
        "log_out_dir": "[i] Cartella di destinazione attiva: {dir}",
        "log_added_files": "[+] Aggiunti {count} documento/i alla coda.",
        "log_no_pdfs": "[!] Nessun file PDF trovato in: {dir}",
        "log_out_updated": "[+] Nuova cartella di destinazione: {dir}",
        "log_queue_cleared": "[i] Coda svuotata.",
        "log_stop_first": "[!] Arresta prima la coda di elaborazione.",
        "log_empty_queue": "[!] Coda vuota. Aggiungi almeno un file PDF o una cartella.",
        "log_start_queue": "[*] AVVIO CODA: {count} file in elaborazione sequenziale.",
        "log_paused": "[⏸️] Coda messa in pausa. L'elaborazione del processo corrente è sospesa.",
        "log_resumed": "[▶️] Coda ripresa. L'elaborazione continua.",
        "log_removed_completed": "[i] Rimossi {count} documento/i completati dalla coda.",
        "log_removed_item": "[-] Rimosso dalla coda: {name}",
        "log_cancelled_by_user": "[!] Conversione annullata dall'utente.",
        "log_success": "[✓] Completato con successo in {elapsed:.1f}s",
        "log_error_code": "[✗] Errore processo: codice di uscita {code}",
        "log_error_exec": "[!] Errore di esecuzione: {err}",
        "log_queue_finished": "[✓] CODA TERMINATA: {completed} completati con successo, {failed} errori su {total} totali.",
        "dialog_add_files": "Seleziona uno o più file PDF da aggiungere alla coda",
        "dialog_add_folder": "Seleziona cartella contenente i PDF",
        "dialog_out_folder": "Seleziona cartella di destinazione",
    },
}


def load_config() -> dict:
    default_cfg = {
        "language": "en",
        "last_input_dir": str(Path.home()),
        "last_output_dir": str(DEFAULT_OUTPUT_DIR),
        "engine_mode": "local_gpu",
        "page_range": "",
        "recent_files": [],
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_cfg.update(loaded)
                return default_cfg
        except Exception:
            pass
    return default_cfg


def save_config(config: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


@dataclass
class QueueItem:
    pdf_path: str
    status: str = "QUEUED"  # QUEUED, RUNNING, PAUSED, COMPLETED, ERROR, CANCELLED
    page_count: str = "-"
    duration: float = 0.0
    output_dir: str = ""
    output_md: str = ""
    error_msg: str = ""


class ConversionWorker(QThread):
    output_line = pyqtSignal(str)
    item_progress = pyqtSignal(int, str)  # percent (0-100), stage_desc
    finished_item = pyqtSignal(bool, str, str, float)  # success, out_dir, md_file, elapsed_seconds

    def __init__(
        self,
        pdf_path: str,
        output_dir: str,
        engine_mode: str,
        page_range: str,
        lang: str = "en",
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.engine_mode = engine_mode
        self.page_range = page_range.strip()
        self.lang = lang
        self._is_cancelled = False
        self.process: Optional[subprocess.Popen] = None

    def pause(self) -> bool:
        if self.process and self.process.poll() is None:
            try:
                proc = psutil.Process(self.process.pid)
                for child in proc.children(recursive=True):
                    try:
                        child.suspend()
                    except Exception:
                        pass
                proc.suspend()
                return True
            except Exception:
                pass
        return False

    def resume(self) -> bool:
        if self.process and self.process.poll() is None:
            try:
                proc = psutil.Process(self.process.pid)
                for child in proc.children(recursive=True):
                    try:
                        child.resume()
                    except Exception:
                        pass
                proc.resume()
                return True
            except Exception:
                pass
        return False

    def run(self) -> None:
        cmd = [
            str(MARKER_EXE),
            self.pdf_path,
            "--output_dir",
            self.output_dir,
        ]

        if self.page_range:
            cmd.extend(["--page_range", self.page_range])

        env = os.environ.copy()
        base_dir = Path(__file__).parent
        bin_dir = base_dir / "bin"
        llama_server_exe = bin_dir / "llama-server.exe"

        tr = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])

        if self.engine_mode == "local_gpu":
            if llama_server_exe.exists():
                env["LLAMA_CPP_BINARY"] = str(llama_server_exe)
                env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
                env["SURYA_INFERENCE_BACKEND"] = "llamacpp"
            cmd.extend(["--mode", "fast", "--ocr_inline_math"])
            msg = "[*] Formula Engine: Local GPU RTX 3070 (Fast Mode + LaTeX Math OCR)" if self.lang == "en" else "[*] Motore Formule: Locale GPU RTX 3070 (Modalità Veloce + OCR Formule LaTeX)"
            self.output_line.emit(msg)
        elif self.engine_mode == "gemini_cloud":
            gemini_key = env.get("GEMINI_API_KEY", "").strip()
            if not gemini_key:
                warn_msg = (
                    "[!] WARNING: GEMINI_API_KEY environment variable not set. Please set GEMINI_API_KEY to use Gemini Cloud mode."
                    if self.lang == "en"
                    else "[!] ATTENZIONE: Variabile d'ambiente GEMINI_API_KEY non impostata. Imposta GEMINI_API_KEY per usare Gemini Cloud."
                )
                self.output_line.emit(warn_msg)
            cmd.extend([
                "--disable_ocr",
                "--use_llm",
                "--llm_service", "marker.services.gemini.GoogleGeminiService",
                "--GoogleGeminiService_gemini_api_key", gemini_key,
                "--GoogleGeminiService_gemini_model_name", "gemini-2.5-flash",
                "--LLMEquationProcessor_redo_inline_math",
            ])
            msg = "[*] Formula Engine: Cloud AI (Gemini Flash via Google AI Studio)" if self.lang == "en" else "[*] Motore Formule: Cloud AI (Gemini Flash via Google AI Studio)"
            self.output_line.emit(msg)
        else:  # "fast_text"
            cmd.append("--disable_ocr")
            msg = "[*] Formula Engine: Fast Text-Only (--disable_ocr)" if self.lang == "en" else "[*] Motore Formule: Solo Testo Veloce (--disable_ocr)"
            self.output_line.emit(msg)

        start_time = time.time()

        PROGRESS_RE = re.compile(
            r'(?:(\w+)\s+(?:running|process|runner))?.*?(\d{1,3})%\|.*?\|\s*(\d+)/(\d+)',
            re.IGNORECASE,
        )
        STAGE_MAP = {
            "layoutbuilder": tr.get("stage_layout", "Layout"),
            "ocrbuilder": tr.get("stage_ocr", "OCR"),
            "equationprocessor": tr.get("stage_math", "LaTeX Formulas"),
            "llm": tr.get("stage_gemini", "Gemini AI"),
            "tableprocessor": tr.get("stage_tables", "Tables"),
            "linebuilder": tr.get("stage_lines", "Lines & Text"),
        }

        try:
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            buf = []
            while True:
                if self._is_cancelled:
                    break
                c = self.process.stdout.read(1)
                if not c:
                    break
                if c == '\r' or c == '\n':
                    if buf:
                        line_clean = ''.join(buf).strip()
                        buf = []
                        if line_clean:
                            m = PROGRESS_RE.search(line_clean)
                            if m:
                                raw_stage, pct_str, cur_s, tot_s = m.groups()
                                stage_name = STAGE_MAP.get((raw_stage or "").lower(), raw_stage or tr.get("stage_proc", "Processing"))
                                pct_val = int(pct_str)
                                self.item_progress.emit(pct_val, f"{stage_name}: {cur_s}/{tot_s} ({pct_val}%)")
                            else:
                                self.output_line.emit(line_clean)
                else:
                    buf.append(c)

            if buf:
                line_clean = ''.join(buf).strip()
                if line_clean:
                    self.output_line.emit(line_clean)

            self.process.wait()
            elapsed = time.time() - start_time

            if self._is_cancelled:
                self.output_line.emit(tr.get("log_cancelled_by_user", "[!] Conversion cancelled by user."))
                self.finished_item.emit(False, "", "", elapsed)
                return

            if self.process.returncode == 0:
                self.output_line.emit(
                    tr.get("log_success", "[✓] Completed successfully in {elapsed:.1f}s").format(elapsed=elapsed)
                )

                # Locate generated Markdown file
                pdf_stem = Path(self.pdf_path).stem
                expected_dir = Path(self.output_dir) / pdf_stem
                expected_md = expected_dir / f"{pdf_stem}.md"

                if not expected_md.exists():
                    expected_md = Path(self.output_dir) / f"{pdf_stem}.md"
                    expected_dir = Path(self.output_dir)

                self.finished_item.emit(
                    True,
                    str(expected_dir) if expected_dir.exists() else self.output_dir,
                    str(expected_md) if expected_md.exists() else "",
                    elapsed,
                )
            else:
                self.output_line.emit(
                    tr.get("log_error_code", "[✗] Process error: exit code {code}").format(code=self.process.returncode)
                )
                self.finished_item.emit(False, "", "", elapsed)

        except Exception as ex:
            elapsed = time.time() - start_time
            self.output_line.emit(tr.get("log_error_exec", "[!] Execution error: {err}").format(err=ex))
            self.finished_item.emit(False, "", "", elapsed)

    def cancel(self) -> None:
        self._is_cancelled = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass


class DropZoneWidget(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.is_hovered = False
        self.setObjectName("dropZone")
        self.setFixedHeight(105)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        self.icon_label = QLabel("📥")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 24px; color: #8b949e;")

        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #c9d1d9;")

        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("font-size: 11.5px; color: #6e7681;")

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.hint_label)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                p = url.toLocalFile()
                if p.lower().endswith(".pdf") or os.path.isdir(p):
                    event.acceptProposedAction()
                    self.is_hovered = True
                    self.update()
                    return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.is_hovered = False
        self.update()

    def dropEvent(self, event: QDropEvent) -> None:
        self.is_hovered = False
        self.update()
        found_paths = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if os.path.isfile(local_path) and local_path.lower().endswith(".pdf"):
                found_paths.append(local_path)
            elif os.path.isdir(local_path):
                for root, _, files in os.walk(local_path):
                    for f in files:
                        if f.lower().endswith(".pdf"):
                            found_paths.append(os.path.join(root, f))

        if found_paths:
            self.files_dropped.emit(found_paths)
            event.acceptProposedAction()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            window = self.window()
            if hasattr(window, "browse_add_files"):
                window.browse_add_files()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        border_color = QColor("#388bfd") if self.is_hovered else QColor("#30363d")
        bg_color = QColor(56, 139, 253, 22) if self.is_hovered else QColor(22, 27, 34, 180)

        pen = QPen(border_color, 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(bg_color)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 8, 8)


class MarkerStudioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.lang = self.config.get("language", "en")
        self.queue: List[QueueItem] = []
        self.current_worker: Optional[ConversionWorker] = None
        self.current_queue_index = -1
        self.is_queue_running = False
        self.is_queue_paused = False

        self.item_timer = QTimer(self)
        self.item_seconds = 0
        self.item_timer.timeout.connect(self._update_item_timer)

        self.init_ui()
        self.apply_theme()
        self.restore_last_state()
        self.retranslate_ui()

    def t(self, key: str, **kwargs) -> str:
        text = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(
            key, TRANSLATIONS["en"].get(key, key)
        )
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def init_ui(self) -> None:
        self.setWindowTitle("Marker Studio - PDF to Markdown Engine")
        self.resize(960, 780)
        self.setMinimumSize(820, 620)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # 1. Header Bar
        header = QHBoxLayout()
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.app_title = QLabel("MARKER STUDIO")
        self.app_title.setStyleSheet("font-size: 15px; font-weight: 700; letter-spacing: 0.5px; color: #f0f6fc;")
        self.app_sub = QLabel("")
        self.app_sub.setStyleSheet("font-size: 12px; color: #8b949e;")
        title_col.addWidget(self.app_title)
        title_col.addWidget(self.app_sub)
        header.addLayout(title_col)

        header.addStretch()

        # Language Selector
        self.cmb_lang = QComboBox()
        self.cmb_lang.addItem("🇬🇧 English", "en")
        self.cmb_lang.addItem("🇮🇹 Italiano", "it")
        self.cmb_lang.setFixedWidth(115)
        self.cmb_lang.setFixedHeight(28)
        self.cmb_lang.setStyleSheet(
            "QComboBox { font-size: 11.5px; font-weight: 600; padding: 2px 8px; border: 1px solid #30363d; background: #161b22; color: #c9d1d9; border-radius: 5px; }"
            "QComboBox:hover { border-color: #58a6ff; }"
        )
        # Select current config language
        lang_idx = self.cmb_lang.findData(self.lang)
        if lang_idx >= 0:
            self.cmb_lang.setCurrentIndex(lang_idx)
        self.cmb_lang.currentIndexChanged.connect(self.on_language_changed)
        header.addWidget(self.cmb_lang)

        self.status_badge = QLabel("")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setStyleSheet(
            "padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; "
            "background: #21262d; color: #8b949e; border: 1px solid #30363d;"
        )
        header.addWidget(self.status_badge)

        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("font-family: Consolas, monospace; font-size: 12px; color: #8b949e;")
        header.addWidget(self.timer_label)

        main_layout.addLayout(header)

        # 2. Drag & Drop Area
        self.drop_zone = DropZoneWidget(self)
        self.drop_zone.files_dropped.connect(self.add_files_to_queue)
        main_layout.addWidget(self.drop_zone)

        # 3. Path & Common Options Frame
        paths_box = QFrame()
        paths_box.setObjectName("sectionFrame")
        paths_layout = QVBoxLayout(paths_box)
        paths_layout.setContentsMargins(14, 10, 14, 10)
        paths_layout.setSpacing(8)

        # Row 1: Destination folder
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.lbl_out = QLabel("")
        self.lbl_out.setFixedWidth(145)
        self.lbl_out.setStyleSheet("font-size: 12.5px; font-weight: 600; color: #8b949e;")

        self.txt_output = QLineEdit()

        self.btn_browse_out = QPushButton("")
        self.btn_browse_out.setFixedWidth(85)
        self.btn_browse_out.clicked.connect(self.browse_output_dir)

        out_row.addWidget(self.lbl_out)
        out_row.addWidget(self.txt_output)
        out_row.addWidget(self.btn_browse_out)
        paths_layout.addLayout(out_row)

        # Row 2: Formula Engine Selector
        engine_row = QHBoxLayout()
        engine_row.setSpacing(8)

        self.lbl_engine = QLabel("")
        self.lbl_engine.setFixedWidth(145)
        self.lbl_engine.setStyleSheet("font-size: 12.5px; font-weight: 600; color: #8b949e;")

        self.cmb_engine = QComboBox()
        self.cmb_engine.addItem("", "local_gpu")
        self.cmb_engine.addItem("", "gemini_cloud")
        self.cmb_engine.addItem("", "fast_text")

        engine_row.addWidget(self.lbl_engine)
        engine_row.addWidget(self.cmb_engine, 1)
        paths_layout.addLayout(engine_row)

        # Row 3: Page Range & Preferences
        opts_row = QHBoxLayout()
        opts_row.setSpacing(12)

        self.lbl_pages = QLabel("")
        self.lbl_pages.setFixedWidth(145)
        self.lbl_pages.setStyleSheet("font-size: 12px; color: #8b949e;")

        self.txt_pages = QLineEdit()
        self.txt_pages.setFixedWidth(180)

        self.chk_remember = QCheckBox("")
        self.chk_remember.setChecked(True)

        opts_row.addWidget(self.lbl_pages)
        opts_row.addWidget(self.txt_pages)
        opts_row.addSpacing(16)
        opts_row.addWidget(self.chk_remember)
        opts_row.addStretch()

        paths_layout.addLayout(opts_row)
        main_layout.addWidget(paths_box)

        # 4. Splitter: Top Queue Table / Bottom Execution Log
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # Top section: Queue Widget
        queue_container = QWidget()
        q_layout = QVBoxLayout(queue_container)
        q_layout.setContentsMargins(0, 0, 0, 0)
        q_layout.setSpacing(6)

        # Queue Toolbar
        q_toolbar = QHBoxLayout()
        q_toolbar.setSpacing(8)

        self.lbl_queue_title = QLabel("")
        self.lbl_queue_title.setStyleSheet("font-size: 11.5px; font-weight: 700; color: #8b949e; letter-spacing: 0.5px;")
        q_toolbar.addWidget(self.lbl_queue_title)

        self.lbl_queue_counts = QLabel("(0)")
        self.lbl_queue_counts.setStyleSheet("font-size: 11.5px; color: #6e7681;")
        q_toolbar.addWidget(self.lbl_queue_counts)

        q_toolbar.addStretch()

        self.btn_add_files = QPushButton("")
        self.btn_add_files.setFixedHeight(28)
        self.btn_add_files.clicked.connect(self.browse_add_files)

        self.btn_add_folder = QPushButton("")
        self.btn_add_folder.setFixedHeight(28)
        self.btn_add_folder.clicked.connect(self.browse_add_folder)

        self.btn_clear_completed = QPushButton("")
        self.btn_clear_completed.setObjectName("btnSubtle")
        self.btn_clear_completed.setFixedHeight(28)
        self.btn_clear_completed.clicked.connect(self.clear_completed)

        self.btn_clear_queue = QPushButton("")
        self.btn_clear_queue.setObjectName("btnSubtle")
        self.btn_clear_queue.setFixedHeight(28)
        self.btn_clear_queue.clicked.connect(self.clear_queue)

        q_toolbar.addWidget(self.btn_add_files)
        q_toolbar.addWidget(self.btn_add_folder)
        q_toolbar.addWidget(self.btn_clear_completed)
        q_toolbar.addWidget(self.btn_clear_queue)
        q_layout.addLayout(q_toolbar)

        # Queue Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 38)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 122)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 75)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 222)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        q_layout.addWidget(self.table)

        # Progress Container
        prog_container = QVBoxLayout()
        prog_container.setSpacing(4)
        prog_container.setContentsMargins(0, 4, 0, 2)

        prog_header = QHBoxLayout()
        self.lbl_prog_title = QLabel("")
        self.lbl_prog_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #8b949e; letter-spacing: 0.5px;")

        self.lbl_prog_detail = QLabel("")
        self.lbl_prog_detail.setStyleSheet("font-size: 11.5px; color: #8b949e;")

        prog_header.addWidget(self.lbl_prog_title)
        prog_header.addStretch()
        prog_header.addWidget(self.lbl_prog_detail)
        prog_container.addLayout(prog_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setValue(0)
        prog_container.addWidget(self.progress_bar)

        q_layout.addLayout(prog_container)

        splitter.addWidget(queue_container)

        # Bottom section: Console Log
        console_container = QWidget()
        c_layout = QVBoxLayout(console_container)
        c_layout.setContentsMargins(0, 4, 0, 0)
        c_layout.setSpacing(6)

        c_toolbar = QHBoxLayout()
        self.lbl_console = QLabel("")
        self.lbl_console.setStyleSheet("font-size: 11px; font-weight: 700; color: #8b949e; letter-spacing: 0.5px;")
        c_toolbar.addWidget(self.lbl_console)
        c_toolbar.addStretch()

        self.btn_clear_log = QPushButton("")
        self.btn_clear_log.setObjectName("btnSubtle")
        self.btn_clear_log.setFixedHeight(22)
        self.btn_clear_log.clicked.connect(lambda: self.console.clear())
        c_toolbar.addWidget(self.btn_clear_log)
        c_layout.addLayout(c_toolbar)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("consoleBox")
        self.console.setFont(QFont("Consolas", 10))
        c_layout.addWidget(self.console)

        splitter.addWidget(console_container)
        splitter.setSizes([320, 200])

        main_layout.addWidget(splitter, 1)

        # 5. Bottom Action Bar
        exec_bar = QHBoxLayout()
        exec_bar.setSpacing(10)

        self.btn_start_queue = QPushButton("")
        self.btn_start_queue.setObjectName("btnStart")
        self.btn_start_queue.setFixedHeight(40)
        self.btn_start_queue.setStyleSheet(
            "font-weight: 700; font-size: 13.5px; letter-spacing: 0.3px; "
            "background-color: #238636; color: #ffffff; border: 1px solid #2ea043; border-radius: 6px; padding: 0 20px;"
        )
        self.btn_start_queue.clicked.connect(self.start_queue)

        self.btn_pause_queue = QPushButton("")
        self.btn_pause_queue.setFixedHeight(40)
        self.btn_pause_queue.setEnabled(False)
        self.btn_pause_queue.clicked.connect(self.toggle_pause_queue)

        self.btn_stop_queue = QPushButton("")
        self.btn_stop_queue.setFixedHeight(40)
        self.btn_stop_queue.setEnabled(False)
        self.btn_stop_queue.clicked.connect(self.stop_queue)

        self.btn_open_all_folder = QPushButton("")
        self.btn_open_all_folder.setFixedHeight(40)
        self.btn_open_all_folder.clicked.connect(self.open_output_folder)

        exec_bar.addWidget(self.btn_start_queue, 2)
        exec_bar.addWidget(self.btn_pause_queue, 1)
        exec_bar.addWidget(self.btn_stop_queue, 1)
        exec_bar.addWidget(self.btn_open_all_folder, 1)

        main_layout.addLayout(exec_bar)

        # Keyboard Shortcut: Ctrl+Enter starts queue
        QShortcut(QKeySequence("Ctrl+Return"), self, self.start_queue)

    def on_language_changed(self, index: int) -> None:
        new_lang = self.cmb_lang.itemData(index)
        if new_lang and new_lang != self.lang:
            self.lang = new_lang
            self.config["language"] = self.lang
            save_config(self.config)
            self.retranslate_ui()
            self.log(f"[i] Language switched to: {'English' if self.lang == 'en' else 'Italiano'}")

    def retranslate_ui(self) -> None:
        self.app_title.setText(self.t("app_title"))
        self.app_sub.setText(self.t("app_subtitle"))

        if not self.queue:
            self.drop_zone.title_label.setText(self.t("drop_title_default"))
            self.drop_zone.hint_label.setText(self.t("drop_hint_default"))
        else:
            self.drop_zone.title_label.setText(self.t("drop_title_count", count=len(self.queue)))

        self.lbl_out.setText(self.t("lbl_output_dir"))
        self.txt_output.setPlaceholderText(self.t("placeholder_output"))
        self.btn_browse_out.setText(self.t("btn_browse"))

        self.lbl_engine.setText(self.t("lbl_engine"))
        cur_eng_idx = self.cmb_engine.currentIndex()
        self.cmb_engine.setItemText(0, self.t("engine_local_gpu"))
        self.cmb_engine.setItemText(1, self.t("engine_gemini_cloud"))
        self.cmb_engine.setItemText(2, self.t("engine_fast_text"))
        self.cmb_engine.setToolTip(self.t("engine_tooltip"))
        if cur_eng_idx >= 0:
            self.cmb_engine.setCurrentIndex(cur_eng_idx)

        self.lbl_pages.setText(self.t("lbl_pages"))
        self.txt_pages.setPlaceholderText(self.t("placeholder_pages"))
        self.chk_remember.setText(self.t("chk_remember"))

        self.lbl_queue_title.setText(self.t("lbl_queue_title"))
        self.lbl_queue_counts.setText(self.t("lbl_queue_count", count=len(self.queue)))
        self.btn_add_files.setText(self.t("btn_add_files"))
        self.btn_add_folder.setText(self.t("btn_add_folder"))
        self.btn_clear_completed.setText(self.t("btn_clear_completed"))
        self.btn_clear_completed.setToolTip(self.t("btn_clear_completed_tooltip"))
        self.btn_clear_queue.setText(self.t("btn_clear_all"))

        self.table.setHorizontalHeaderLabels([
            self.t("th_index"),
            self.t("th_name"),
            self.t("th_status"),
            self.t("th_duration"),
            self.t("th_actions"),
        ])

        self.lbl_prog_title.setText(self.t("lbl_progress_title"))
        if not self.is_queue_running:
            if all(q.status == "COMPLETED" for q in self.queue) and self.queue:
                self.lbl_prog_detail.setText(self.t("progress_all_done"))
            else:
                self.lbl_prog_detail.setText(self.t("progress_waiting"))
        elif self.is_queue_paused:
            self.lbl_prog_detail.setText(self.t("progress_paused"))

        self.lbl_console.setText(self.t("lbl_console_title"))
        self.btn_clear_log.setText(self.t("btn_clear_log"))

        self.btn_start_queue.setText(self.t("btn_start_queue"))
        if self.is_queue_paused:
            self.btn_pause_queue.setText(self.t("btn_resume_queue"))
        else:
            self.btn_pause_queue.setText(self.t("btn_pause_queue"))
        self.btn_stop_queue.setText(self.t("btn_stop_queue"))
        self.btn_open_all_folder.setText(self.t("btn_open_out_folder"))

        # Update status badge
        if not self.is_queue_running:
            if all(q.status == "COMPLETED" for q in self.queue) and self.queue:
                self.status_badge.setText(self.t("badge_completed"))
            elif any(q.status == "CANCELLED" for q in self.queue):
                self.status_badge.setText(self.t("badge_stopped"))
            else:
                self.status_badge.setText(self.t("badge_idle"))
        elif self.is_queue_paused:
            self.status_badge.setText(self.t("badge_paused"))
        else:
            self.status_badge.setText(self.t("badge_processing"))

        self.refresh_table()

    def format_item_status(self, raw_status: str) -> str:
        s = raw_status.upper()
        if "IN CORSO" in s or "RUNNING" in s or "PROCESSING" in s:
            pct_match = re.search(r'\((.*?)\)', raw_status)
            suffix = f" ({pct_match.group(1)})" if pct_match else ""
            return self.t("status_running") + suffix
        elif s in ("COMPLETATO", "COMPLETED"):
            return self.t("status_completed")
        elif s in ("IN PAUSA", "PAUSED"):
            return self.t("status_paused")
        elif s in ("ERRORE", "ERROR"):
            return self.t("status_error")
        elif s in ("ANNULLATO", "CANCELLED"):
            return self.t("status_cancelled")
        else:
            return self.t("status_in_queue")

    def apply_theme(self) -> None:
        qss = """
        QMainWindow, QWidget {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 12.5px;
        }

        #sectionFrame {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
        }

        QLineEdit {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 5px;
            color: #f0f6fc;
            padding: 6px 10px;
            selection-background-color: #1f6feb;
            font-family: Consolas, "Segoe UI", monospace;
            font-size: 12px;
        }

        QLineEdit:focus {
            border: 1px solid #58a6ff;
        }

        QComboBox {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 5px;
            color: #f0f6fc;
            padding: 5px 10px;
            font-size: 12px;
        }

        QComboBox:focus, QComboBox:hover {
            border: 1px solid #58a6ff;
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 26px;
            border-left: 1px solid #30363d;
            background-color: #161b22;
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }

        QComboBox QAbstractItemView {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #f0f6fc;
            selection-background-color: #1f6feb;
            padding: 4px;
        }

        QPushButton {
            background-color: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
            border-radius: 5px;
            padding: 6px 14px;
            font-weight: 600;
        }

        QPushButton:hover {
            background-color: #30363d;
            border-color: #8b949e;
            color: #f0f6fc;
        }

        QPushButton:pressed {
            background-color: #161b22;
        }

        QPushButton:disabled {
            background-color: #161b22;
            color: #484f58;
            border-color: #21262d;
        }

        #btnStart:hover {
            background-color: #2ea043;
            border-color: #3fb950;
        }

        #btnSubtle {
            background: transparent;
            border: none;
            color: #8b949e;
            font-size: 11px;
            padding: 2px 8px;
        }

        #btnSubtle:hover {
            color: #f0f6fc;
            text-decoration: underline;
        }

        QCheckBox {
            color: #8b949e;
            font-size: 12px;
            spacing: 6px;
        }

        QCheckBox:hover {
            color: #c9d1d9;
        }

        QCheckBox::indicator {
            width: 15px;
            height: 15px;
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 3px;
        }

        QCheckBox::indicator:checked {
            background-color: #1f6feb;
            border-color: #58a6ff;
        }

        QTableWidget {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            gridline-color: transparent;
        }

        QTableWidget::item {
            padding: 6px 8px;
            border-bottom: 1px solid #21262d;
        }

        QTableWidget::item:selected {
            background-color: #1f242c;
            color: #f0f6fc;
        }

        QHeaderView::section {
            background-color: #161b22;
            color: #8b949e;
            font-weight: 600;
            font-size: 11px;
            padding: 6px 8px;
            border: none;
            border-bottom: 1px solid #30363d;
        }

        QProgressBar {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 4px;
            color: #f0f6fc;
            font-size: 10px;
            font-weight: 700;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #238636;
            border-radius: 3px;
        }

        #consoleBox {
            background-color: #090d12;
            border: 1px solid #21262d;
            border-radius: 6px;
            color: #8b949e;
            padding: 8px;
            line-height: 1.4;
        }

        QSplitter::handle {
            background-color: #21262d;
            height: 2px;
        }

        QScrollBar:vertical {
            background: #0d1117;
            width: 10px;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background: #30363d;
            min-height: 20px;
            border-radius: 4px;
        }

        QScrollBar::handle:vertical:hover {
            background: #484f58;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        """
        self.setStyleSheet(qss)

    def restore_last_state(self) -> None:
        out_dir = self.config.get("last_output_dir", str(DEFAULT_OUTPUT_DIR))
        self.txt_output.setText(out_dir)
        engine_mode = self.config.get("engine_mode", "local_gpu")
        idx = self.cmb_engine.findData(engine_mode)
        if idx >= 0:
            self.cmb_engine.setCurrentIndex(idx)
        self.log(self.t("log_welcome"))
        self.log(self.t("log_out_dir", dir=out_dir))

    def log(self, text: str) -> None:
        self.console.appendPlainText(text)
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    # --- Queue Management ---

    def add_files_to_queue(self, paths: List[str]) -> None:
        added_count = 0
        existing_paths = {item.pdf_path for item in self.queue}

        for p in paths:
            clean_p = str(Path(p).resolve())
            if clean_p not in existing_paths and clean_p.lower().endswith(".pdf") and os.path.isfile(clean_p):
                self.queue.append(QueueItem(pdf_path=clean_p, status="QUEUED"))
                existing_paths.add(clean_p)
                added_count += 1

        if added_count > 0:
            last_p = paths[-1]
            self.config["last_input_dir"] = str(Path(last_p).parent)
            save_config(self.config)

            self.refresh_table()
            self.log(self.t("log_added_files", count=added_count))
            self.drop_zone.title_label.setText(self.t("drop_title_count", count=len(self.queue)))
            self.drop_zone.hint_label.setText(self.t("drop_hint_last", name=Path(paths[-1]).name))
            self.drop_zone.icon_label.setText("📋")

    def browse_add_files(self) -> None:
        initial_dir = self.config.get("last_input_dir", str(Path.home()))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.t("dialog_add_files"),
            initial_dir,
            "PDF Files (*.pdf);;All Files (*.*)",
        )
        if files:
            self.add_files_to_queue(files)

    def browse_add_folder(self) -> None:
        initial_dir = self.config.get("last_input_dir", str(Path.home()))
        selected_dir = QFileDialog.getExistingDirectory(
            self, self.t("dialog_add_folder"), initial_dir
        )
        if selected_dir:
            pdfs = []
            for root, _, files in os.walk(selected_dir):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        pdfs.append(os.path.join(root, f))
            if pdfs:
                self.add_files_to_queue(pdfs)
            else:
                self.log(self.t("log_no_pdfs", dir=selected_dir))

    def browse_output_dir(self) -> None:
        initial_dir = self.txt_output.text().strip() or self.config.get(
            "last_output_dir", str(DEFAULT_OUTPUT_DIR)
        )
        selected_dir = QFileDialog.getExistingDirectory(
            self, self.t("dialog_out_folder"), initial_dir
        )
        if selected_dir:
            self.txt_output.setText(selected_dir)
            self.config["last_output_dir"] = selected_dir
            save_config(self.config)
            self.log(self.t("log_out_updated", dir=selected_dir))

    def clear_completed(self) -> None:
        old_len = len(self.queue)
        self.queue = [item for item in self.queue if item.status not in ("COMPLETED", "COMPLETATO")]
        removed = old_len - len(self.queue)
        self.refresh_table()
        self.log(self.t("log_removed_completed", count=removed))

    def clear_queue(self) -> None:
        if self.is_queue_running:
            self.log(self.t("log_stop_first"))
            return
        self.queue.clear()
        self.refresh_table()
        self.progress_bar.setValue(0)
        self.lbl_prog_detail.setText(self.t("progress_waiting"))
        self.drop_zone.title_label.setText(self.t("drop_title_default"))
        self.drop_zone.hint_label.setText(self.t("drop_hint_default"))
        self.drop_zone.icon_label.setText("📥")
        self.log(self.t("log_queue_cleared"))

    def refresh_table(self) -> None:
        self.table.setRowCount(len(self.queue))
        self.lbl_queue_counts.setText(self.t("lbl_queue_count", count=len(self.queue)))

        for row, item in enumerate(self.queue):
            # 0. Index
            idx_item = QTableWidgetItem(f"{row + 1}")
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            idx_item.setForeground(QColor("#8b949e"))
            self.table.setItem(row, 0, idx_item)

            # 1. File Name and Path
            name = Path(item.pdf_path).name
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(item.pdf_path)
            name_item.setFont(QFont("Consolas", 10))
            self.table.setItem(row, 1, name_item)

            # 2. Status Badge Widget
            status_widget = QWidget()
            s_layout = QHBoxLayout(status_widget)
            s_layout.setContentsMargins(4, 2, 4, 2)
            s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            disp_status = self.format_item_status(item.status)
            badge = QLabel(disp_status)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedWidth(112)
            badge.setFixedHeight(24)

            s_upper = item.status.upper()
            if s_upper in ("COMPLETED", "COMPLETATO"):
                badge.setStyleSheet("padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #193822; color: #56d364; border: 1px solid #2ea043;")
            elif "RUNNING" in s_upper or "IN CORSO" in s_upper or "PROCESSING" in s_upper:
                badge.setStyleSheet("padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #382405; color: #d29922; border: 1px solid #bb8009;")
            elif s_upper in ("PAUSED", "IN PAUSA"):
                badge.setStyleSheet("padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #2d2200; color: #e3b341; border: 1px solid #9e6a03;")
            elif s_upper in ("ERROR", "ERRORE"):
                badge.setStyleSheet("padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #3c1e22; color: #f85149; border: 1px solid #da3633;")
            elif s_upper in ("CANCELLED", "ANNULLATO"):
                badge.setStyleSheet("padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #21262d; color: #8b949e; border: 1px solid #30363d;")
            else:
                badge.setStyleSheet("padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #21262d; color: #8b949e; border: 1px solid #30363d;")

            s_layout.addWidget(badge)
            self.table.setCellWidget(row, 2, status_widget)

            # 3. Duration
            dur_text = f"{item.duration:.1f}s" if item.duration > 0 else "-"
            dur_item = QTableWidgetItem(dur_text)
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dur_item.setForeground(QColor("#8b949e"))
            dur_item.setFont(QFont("Consolas", 10))
            self.table.setItem(row, 3, dur_item)

            # 4. Action Buttons Widget
            actions_widget = QWidget()
            act_layout = QHBoxLayout(actions_widget)
            act_layout.setContentsMargins(4, 2, 4, 2)
            act_layout.setSpacing(4)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if s_upper in ("COMPLETED", "COMPLETATO"):
                btn_open_md = QPushButton(self.t("btn_open_md"))
                btn_open_md.setFixedHeight(24)
                btn_open_md.setFixedWidth(88)
                btn_open_md.setStyleSheet("font-size: 10.5px; padding: 2px 4px;")
                btn_open_md.clicked.connect(lambda _, p=item.output_md: self._open_file(p))

                btn_open_folder = QPushButton(self.t("btn_open_folder"))
                btn_open_folder.setFixedHeight(24)
                btn_open_folder.setFixedWidth(80)
                btn_open_folder.setStyleSheet("font-size: 10.5px; padding: 2px 4px;")
                btn_open_folder.clicked.connect(lambda _, p=item.output_dir: self._open_file(p))

                btn_del_item = QPushButton("✕")
                btn_del_item.setFixedHeight(24)
                btn_del_item.setFixedWidth(28)
                btn_del_item.setStyleSheet("font-size: 11px; font-weight: 700; color: #8b949e; background: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 0;")
                btn_del_item.setToolTip(self.t("tooltip_remove_single"))
                btn_del_item.clicked.connect(lambda _, r=row: self.remove_queue_item(r))

                act_layout.addWidget(btn_open_md)
                act_layout.addWidget(btn_open_folder)
                act_layout.addWidget(btn_del_item)
            else:
                btn_remove = QPushButton(self.t("btn_remove_item"))
                btn_remove.setFixedHeight(24)
                btn_remove.setFixedWidth(95)
                btn_remove.setStyleSheet("font-size: 11px; color: #8b949e; padding: 2px 10px;")
                btn_remove.setEnabled(not self.is_queue_running or row != self.current_queue_index)
                btn_remove.clicked.connect(lambda _, r=row: self.remove_queue_item(r))
                act_layout.addWidget(btn_remove)

            self.table.setCellWidget(row, 4, actions_widget)

    def _update_table_status_cell(self, row: int) -> None:
        if 0 <= row < len(self.queue):
            item = self.queue[row]
            widget = self.table.cellWidget(row, 2)
            if widget:
                badge = widget.findChild(QLabel)
                if badge:
                    disp = self.format_item_status(item.status)
                    badge.setText(disp)
                    s_upper = item.status.upper()
                    if "RUNNING" in s_upper or "IN CORSO" in s_upper or "PROCESSING" in s_upper:
                        badge.setStyleSheet("padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #382405; color: #d29922; border: 1px solid #bb8009;")
                    elif s_upper in ("PAUSED", "IN PAUSA"):
                        badge.setStyleSheet("padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: #2d2200; color: #e3b341; border: 1px solid #9e6a03;")

    def remove_queue_item(self, row: int) -> None:
        if 0 <= row < len(self.queue):
            removed = self.queue.pop(row)
            self.refresh_table()
            self.log(self.t("log_removed_item", name=Path(removed.pdf_path).name))

    def _open_file(self, target_path: str) -> None:
        if target_path and Path(target_path).exists():
            os.startfile(target_path)

    # --- Queue Execution Engine ---

    def start_queue(self) -> None:
        if self.is_queue_running:
            return

        if not self.queue:
            self.log(self.t("log_empty_queue"))
            return

        out_dir = self.txt_output.text().strip().strip('"')
        if not out_dir:
            out_dir = str(DEFAULT_OUTPUT_DIR)
            self.txt_output.setText(out_dir)

        Path(out_dir).mkdir(parents=True, exist_ok=True)

        if self.chk_remember.isChecked():
            self.config["last_output_dir"] = out_dir
            self.config["engine_mode"] = self.cmb_engine.currentData() or "local_gpu"
            save_config(self.config)

        self.is_queue_running = True
        self.is_queue_paused = False
        self.btn_start_queue.setEnabled(False)
        self.btn_stop_queue.setEnabled(True)
        self.btn_pause_queue.setEnabled(True)
        self.btn_pause_queue.setText(self.t("btn_pause_queue"))
        self.btn_pause_queue.setStyleSheet("")

        self.status_badge.setText(self.t("badge_processing"))
        self.status_badge.setStyleSheet(
            "padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; "
            "background: #382405; color: #d29922; border: 1px solid #bb8009;"
        )

        self.log("\n" + "=" * 65)
        self.log(self.t("log_start_queue", count=len(self.queue)))
        self.process_next_in_queue()

    def toggle_pause_queue(self) -> None:
        if not self.is_queue_running:
            return

        if not self.is_queue_paused:
            # Suspend
            if self.current_worker and self.current_worker.pause():
                self.is_queue_paused = True
                self.item_timer.stop()
                self.btn_pause_queue.setText(self.t("btn_resume_queue"))
                self.btn_pause_queue.setStyleSheet(
                    "background-color: #1f6feb; color: #ffffff; border: 1px solid #388bfd; font-weight: 700;"
                )
                self.status_badge.setText(self.t("badge_paused"))
                self.status_badge.setStyleSheet(
                    "padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; "
                    "background: #2d2200; color: #e3b341; border: 1px solid #9e6a03;"
                )
                if 0 <= self.current_queue_index < len(self.queue):
                    self.queue[self.current_queue_index].status = "PAUSED"
                    self._update_table_status_cell(self.current_queue_index)
                self.lbl_prog_detail.setText(self.t("progress_paused"))
                self.log(self.t("log_paused"))
        else:
            # Resume
            if self.current_worker and self.current_worker.resume():
                self.is_queue_paused = False
                self.item_timer.start(1000)
                self.btn_pause_queue.setText(self.t("btn_pause_queue"))
                self.btn_pause_queue.setStyleSheet("")
                self.status_badge.setText(self.t("badge_processing"))
                self.status_badge.setStyleSheet(
                    "padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; "
                    "background: #382405; color: #d29922; border: 1px solid #bb8009;"
                )
                if 0 <= self.current_queue_index < len(self.queue):
                    self.queue[self.current_queue_index].status = "RUNNING"
                    self._update_table_status_cell(self.current_queue_index)
                self.lbl_prog_detail.setText(self.t("progress_resuming"))
                self.log(self.t("log_resumed"))

    def on_item_progress(self, file_pct: int, stage_desc: str) -> None:
        if not self.queue:
            return

        completed_count = sum(1 for q in self.queue if q.status in ("COMPLETED", "ERROR", "CANCELLED", "COMPLETATO", "ERRORE", "ANNULLATO"))
        tot_files = max(1, len(self.queue))
        overall_pct = int(((completed_count + (file_pct / 100.0)) / tot_files) * 100)
        self.progress_bar.setValue(min(99, overall_pct))

        curr_num = self.current_queue_index + 1
        file_name = Path(self.queue[self.current_queue_index].pdf_path).name if 0 <= self.current_queue_index < len(self.queue) else ""
        short_name = (file_name[:28] + '..') if len(file_name) > 30 else file_name
        self.lbl_prog_detail.setText(f"File {curr_num}/{tot_files} ({short_name}): {stage_desc}")

        if 0 <= self.current_queue_index < len(self.queue):
            if not self.is_queue_paused:
                self.queue[self.current_queue_index].status = f"RUNNING ({file_pct}%)"
                self._update_table_status_cell(self.current_queue_index)

    def process_next_in_queue(self) -> None:
        if not self.is_queue_running:
            return

        # Find next pending item
        next_idx = -1
        for idx, item in enumerate(self.queue):
            if item.status in ("QUEUED", "IN CODA"):
                next_idx = idx
                break

        if next_idx == -1:
            self.on_queue_all_finished()
            return

        self.current_queue_index = next_idx
        item = self.queue[next_idx]
        item.status = "RUNNING"
        self.refresh_table()

        # Update progress bar
        completed_count = sum(1 for q in self.queue if q.status in ("COMPLETED", "ERROR", "CANCELLED", "COMPLETATO", "ERRORE", "ANNULLATO"))
        progress_pct = int((completed_count / len(self.queue)) * 100)
        self.progress_bar.setValue(progress_pct)
        file_name = Path(item.pdf_path).name
        short_name = (file_name[:28] + '..') if len(file_name) > 30 else file_name
        self.lbl_prog_detail.setText(f"File {next_idx + 1}/{len(self.queue)} ({short_name}): {self.t('stage_starting')}")

        # Start item timer
        self.item_seconds = 0
        self.timer_label.setText("00:00")
        self.item_timer.start(1000)

        pdf_name = Path(item.pdf_path).name
        self.log(f"\n[>>] [{next_idx + 1}/{len(self.queue)}] " + (f"Starting conversion: {pdf_name}" if self.lang == "en" else f"Inizio conversione: {pdf_name}"))

        out_dir = self.txt_output.text().strip().strip('"')
        selected_engine = self.cmb_engine.currentData() or "local_gpu"
        self.current_worker = ConversionWorker(
            pdf_path=item.pdf_path,
            output_dir=out_dir,
            engine_mode=selected_engine,
            page_range=self.txt_pages.text(),
            lang=self.lang,
        )
        self.current_worker.output_line.connect(self.log)
        self.current_worker.item_progress.connect(self.on_item_progress)
        self.current_worker.finished_item.connect(self.on_item_finished)
        self.current_worker.start()

    def on_item_finished(self, success: bool, out_dir: str, md_file: str, elapsed: float) -> None:
        self.item_timer.stop()

        if 0 <= self.current_queue_index < len(self.queue):
            item = self.queue[self.current_queue_index]
            item.duration = elapsed
            if success:
                item.status = "COMPLETED"
                item.output_dir = out_dir
                item.output_md = md_file
            else:
                item.status = "ERROR" if not self.current_worker._is_cancelled else "CANCELLED"

        self.refresh_table()

        completed_count = sum(1 for q in self.queue if q.status in ("COMPLETED", "ERROR", "CANCELLED", "COMPLETATO", "ERRORE", "ANNULLATO"))
        progress_pct = int((completed_count / len(self.queue)) * 100)
        self.progress_bar.setValue(progress_pct)

        # Proceed to next file in queue
        if self.is_queue_running:
            self.process_next_in_queue()

    def stop_queue(self) -> None:
        self.is_queue_running = False
        self.is_queue_paused = False
        self.log(self.t("log_queue_stopped"))
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()

        self.btn_start_queue.setEnabled(True)
        self.btn_stop_queue.setEnabled(False)
        self.btn_pause_queue.setEnabled(False)
        self.btn_pause_queue.setText(self.t("btn_pause_queue"))
        self.btn_pause_queue.setStyleSheet("")

        self.status_badge.setText(self.t("badge_stopped"))
        self.status_badge.setStyleSheet(
            "padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; "
            "background: #3c1e22; color: #f85149; border: 1px solid #da3633;"
        )
        self.lbl_prog_detail.setText(self.t("progress_interrupted"))

    def on_queue_all_finished(self) -> None:
        self.is_queue_running = False
        self.is_queue_paused = False
        self.btn_start_queue.setEnabled(True)
        self.btn_stop_queue.setEnabled(False)
        self.btn_pause_queue.setEnabled(False)
        self.btn_pause_queue.setText(self.t("btn_pause_queue"))
        self.btn_pause_queue.setStyleSheet("")
        self.progress_bar.setValue(100)
        self.lbl_prog_detail.setText(self.t("progress_all_done"))

        completed = sum(1 for q in self.queue if q.status in ("COMPLETED", "COMPLETATO"))
        failed = sum(1 for q in self.queue if q.status in ("ERROR", "ERRORE"))

        self.status_badge.setText(self.t("badge_completed"))
        self.status_badge.setStyleSheet(
            "padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; "
            "background: #193822; color: #56d364; border: 1px solid #2ea043;"
        )

        self.log("\n" + "=" * 65)
        self.log(self.t("log_queue_finished", completed=completed, failed=failed, total=len(self.queue)))

    def _update_item_timer(self) -> None:
        self.item_seconds += 1
        mins = self.item_seconds // 60
        secs = self.item_seconds % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")

    def open_output_folder(self) -> None:
        target = self.txt_output.text().strip()
        if target and Path(target).exists():
            os.startfile(target)

    def closeEvent(self, event) -> None:
        if self.chk_remember.isChecked():
            self.config["last_output_dir"] = self.txt_output.text().strip()
            self.config["engine_mode"] = self.cmb_engine.currentData() or "local_gpu"
            self.config["language"] = self.lang
            save_config(self.config)
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
        super().closeEvent(event)


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("antigravity.markerstudio.v2")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("MarkerStudio")

    icon_path = Path(__file__).parent / "app_icon.ico"
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)

    window = MarkerStudioWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))

    if len(sys.argv) > 1:
        incoming_files = [arg for arg in sys.argv[1:] if Path(arg).is_file() and arg.lower().endswith(".pdf")]
        if incoming_files:
            window.add_files_to_queue(incoming_files)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
