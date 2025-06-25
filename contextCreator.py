import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QTextBrowser, QStyle, QMessageBox, QCheckBox
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QClipboard

# --- Constants from original script ---
ART = r"""
   ____            _            _      ____                _
  / ___|___  _ __ | |_ _____  _| |_   / ___|_ __ ___  __ _| |_ ___  _ __
 | |   / _ \| '_ \| __/ _ \ \/ / __| | |   | '__/ _ \/ _` | __/ _ \| '__|
 | |__| (_) | | | | ||  __/>  <| |_  | |___| | |  __/ (_| | || (_) | |
  \____\___/|_| |_|\__\___/_/\_\\__|  \____|_|  \___|\__,_|\__\___/|_|

"""
# Default exclusion lists
DEFAULT_EXCLUDED_FOLDERS = {
    'node_modules', 'dist', 'build', '.git', '.vscode', '.idea', '__pycache__',
    'venv', 'env', '.venv', 'target', '.cache', 'logs', 'coverage', '.nyc_output',
    '.movement'
}
DEFAULT_EXCLUDED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'composer.lock',
    'poetry.lock', '.DS_Store'
}
DEFAULT_EXCLUDED_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico',
    '.mp3', '.wav', '.ogg', '.flac', '.m4a', '.mp4', '.mov', '.avi', '.mkv',
    '.webm', '.zip', '.tar', '.gz', '.rar', '.7z', '.pdf', '.docx', '.xlsx',
    '.ppt', '.pptx', '.pyc', '.pyo', '.o', '.a', '.so', '.lib', '.dll',
    '.exe', '.class', '.jar', '.log', '.sqlite', '.sqlite3', '.db'
}

# --- Worker for background processing ---

class Worker(QObject):
    """
    Runs the context creation task in a separate thread to keep the GUI responsive.
    """
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)
    file_count = pyqtSignal(int)
    task_completed = pyqtSignal(str)  # New signal for completion with file path

    def __init__(self, root_dir, output_file, excluded_folders, excluded_files, excluded_extensions):
        super().__init__()
        self.root_dir = root_dir
        self.output_file = output_file
        self.excluded_folders = excluded_folders
        self.excluded_files = excluded_files
        self.excluded_extensions = excluded_extensions
        self.is_running = True

    def _is_path_excluded(self, path):
        base_name = os.path.basename(path)
        if base_name in self.excluded_folders or base_name in self.excluded_files:
            return True
        if os.path.isfile(path):
            _, ext = os.path.splitext(base_name)
            if ext.lower() in self.excluded_extensions:
                return True
        return False

    def _generate_tree(self, dir_path, prefix=""):
        try:
            items = sorted([item for item in os.listdir(dir_path) if not self._is_path_excluded(os.path.join(dir_path, item))])
        except FileNotFoundError:
            return ""
        tree_str = ""
        pointers = ['├── '] * (len(items) - 1) + ['└── ']
        for pointer, item in zip(pointers, items):
            path = os.path.join(dir_path, item)
            tree_str += f"{prefix}{pointer}{item}\n"
            if os.path.isdir(path):
                extension = '│   ' if pointer == '├── ' else '    '
                tree_str += self._generate_tree(path, prefix + extension)
        return tree_str

    def _get_files_to_process(self):
        files_to_process = []
        for dirpath, dirnames, filenames in os.walk(self.root_dir, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in self.excluded_folders]
            for filename in filenames:
                if filename in self.excluded_files: continue
                _, ext = os.path.splitext(filename)
                if ext.lower() in self.excluded_extensions: continue
                files_to_process.append(os.path.join(dirpath, filename))
        return files_to_process

    def run(self):
        """The main task logic."""
        try:
            abs_root_dir = os.path.abspath(self.root_dir)
            project_name = os.path.basename(abs_root_dir)
            
            self.status_update.emit(f'🔍 Scanning for relevant files in <b>{project_name}</b>...')
            files_to_process = self._get_files_to_process()
            
            if not files_to_process:
                self.status_update.emit(f'⚠️ <font color="orange">Warning: No files found to process after exclusions.</font>')
                self.finished.emit()
                return

            self.file_count.emit(len(files_to_process))
            self.status_update.emit(f'Found {len(files_to_process)} files to process.')

            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Project Context for: {project_name}\n\n## Project Structure\n\n")
                f.write(f"```\n{project_name}/\n{self._generate_tree(self.root_dir)}```\n\n## File Contents\n\n")
                
                sorted_files = sorted(files_to_process)
                for i, file_path in enumerate(sorted_files):
                    if not self.is_running:
                        self.status_update.emit('🛑 <font color="orange">Process stopped by user.</font>')
                        break

                    relative_path = os.path.relpath(file_path, self.root_dir)
                    self.status_update.emit(f'📝 Writing: 📄 {relative_path}')
                    
                    f.write(f"--- START OF FILE: {relative_path} ---\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file_content:
                            content = file_content.read()
                            _, extension = os.path.splitext(file_path)
                            lang_hint = extension[1:] if extension else 'text'
                            f.write(f"```{lang_hint}\n{content.strip()}\n```\n")
                            f.write(f"--- END OF FILE: {relative_path} ---\n\n")
                    except Exception as e:
                        f.write(f"Could not read file. Error: {e}\n\n")
                    
                    self.progress.emit(int(((i + 1) / len(sorted_files)) * 100))

            if self.is_running:
                self.status_update.emit(f'✅ <font color="green"><b>SUCCESS:</b></font> Project context saved to <b>{self.output_file}</b>')
                self.task_completed.emit(self.output_file)  # Emit completion signal with file path

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def stop(self):
        self.is_running = False

# --- Main GUI Window ---

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Project Context Generator")
        self.setGeometry(100, 100, 800, 750)
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        # Worker thread management
        self.thread = None
        self.worker = None

        self.init_ui()

    def init_ui(self):
        # Central widget and main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # --- Title with ASCII Art and Icon ---
        title_layout = QHBoxLayout()

        art_label = QLabel(ART)
        art_label.setFont(QFont("Courier New", 8))
        art_label.setStyleSheet("color: magenta;")
        title_layout.addWidget(art_label)

        title_layout.addStretch() # This pushes the icon to the far right

        icon_label = QLabel("🤖")
        icon_label.setFont(QFont("Segoe UI Emoji", 48))
        title_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(title_layout)

        # --- Input/Output Selection ---
        io_layout = QVBoxLayout()
        io_layout.addWidget(QLabel("<b>1. Select Project Directory:</b>"))
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit(os.getcwd())
        dir_browse_btn = QPushButton("Browse...")
        dir_browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(dir_browse_btn)
        io_layout.addLayout(dir_layout)

        io_layout.addWidget(QLabel("<b>2. Select Output File:</b>"))
        output_layout = QHBoxLayout()
        
        downloads_path = Path.home() / "Downloads"
        if not downloads_path.is_dir():
            downloads_path = Path.home()
        default_output_file = str(downloads_path / "project_context.md")

        self.output_input = QLineEdit(default_output_file)
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(self.browse_output_file)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(output_browse_btn)
        io_layout.addLayout(output_layout)
        
        main_layout.addLayout(io_layout)

        # --- New Options Section ---
        options_layout = QVBoxLayout()
        options_layout.addWidget(QLabel("<b>Options:</b>"))
        
        options_row = QHBoxLayout()
        self.copy_to_clipboard_cb = QCheckBox("📋 Copy file contents to clipboard when done")
        self.copy_to_clipboard_cb.setChecked(True)  # Default to checked
        
        self.show_notification_cb = QCheckBox("🔔 Show notification when complete")
        self.show_notification_cb.setChecked(True)  # Default to checked
        
        options_row.addWidget(self.copy_to_clipboard_cb)
        options_row.addWidget(self.show_notification_cb)
        options_row.addStretch()
        
        options_layout.addLayout(options_row)
        main_layout.addLayout(options_layout)

        # --- Exclusions Configuration ---
        main_layout.addWidget(QLabel("<b>3. Configure Exclusions (one per line):</b>"))
        exclusions_layout = QHBoxLayout()
        
        self.excluded_folders_edit = self.create_exclusion_box("Excluded Folders", DEFAULT_EXCLUDED_FOLDERS)
        self.excluded_files_edit = self.create_exclusion_box("Excluded Files", DEFAULT_EXCLUDED_FILES)
        self.excluded_extensions_edit = self.create_exclusion_box("Excluded Extensions", DEFAULT_EXCLUDED_EXTENSIONS)
        
        exclusions_layout.addWidget(self.excluded_folders_edit)
        exclusions_layout.addWidget(self.excluded_files_edit)
        exclusions_layout.addWidget(self.excluded_extensions_edit)
        
        main_layout.addLayout(exclusions_layout)

        # --- Action Buttons ---
        action_layout = QHBoxLayout()
        self.generate_btn = QPushButton("🚀 Generate Context")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("font-weight: bold; font-size: 16px; background-color: #4CAF50; color: white;")
        self.generate_btn.clicked.connect(self.start_generation)
        
        self.stop_btn = QPushButton("🛑 Stop")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setStyleSheet("font-weight: bold; font-size: 16px; background-color: #f44336; color: white;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_generation)

        action_layout.addWidget(self.generate_btn)
        action_layout.addWidget(self.stop_btn)
        main_layout.addLayout(action_layout)

        # --- Progress Bar and Status Log ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_log = QTextBrowser()
        self.status_log.setReadOnly(True)
        self.status_log.setOpenExternalLinks(True)
        self.status_log.append('Welcome! Configure the paths and click "Generate Context".')
        main_layout.addWidget(self.status_log)

    def create_exclusion_box(self, title, items):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(f"<i>{title}</i>"))
        text_edit = QTextEdit()
        text_edit.setPlainText("\n".join(sorted(list(items))))
        layout.addWidget(text_edit)
        widget.findChild(QTextEdit).setObjectName(title.replace(" ", ""))
        return widget

    def browse_directory(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Project Directory", self.dir_input.text())
        if dir_name:
            self.dir_input.setText(dir_name)

    def browse_output_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Output File", self.output_input.text(), "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)")
        if file_name:
            self.output_input.setText(file_name)

    def set_controls_enabled(self, enabled):
        self.dir_input.setEnabled(enabled)
        self.output_input.setEnabled(enabled)
        self.generate_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)
        self.copy_to_clipboard_cb.setEnabled(enabled)
        self.show_notification_cb.setEnabled(enabled)
        for box in [self.excluded_folders_edit, self.excluded_files_edit, self.excluded_extensions_edit]:
            box.findChild(QTextEdit).setEnabled(enabled)

    def copy_to_clipboard(self, file_path):
        """Copy the entire file contents to clipboard"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_contents = f.read()
            
            clipboard = QApplication.clipboard()
            clipboard.setText(file_contents)
            
            # Calculate file size for display
            file_size = len(file_contents)
            if file_size < 1024:
                size_str = f"{file_size} characters"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size // 1024:.1f}K characters"
            else:
                size_str = f"{file_size // (1024 * 1024):.1f}M characters"
            
            self.log_status(f'📋 <font color="blue"><b>File contents copied to clipboard!</b> ({size_str}) Ready to paste into Claude/ChatGPT!</font>')
            
        except Exception as e:
            self.log_status(f'❌ <font color="red">Failed to copy file contents: {e}</font>')
            # Fallback to copying just the path
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
            self.log_status(f'📋 <font color="orange">Copied file path instead: {file_path}</font>')

    def show_completion_notification(self, file_path):
        """Show a completion notification"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Context Generation Complete! 🎉")
        msg.setText("Project context has been successfully generated!")
        msg.setInformativeText(f"File saved to:\n{file_path}")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Add custom buttons
        open_file_btn = msg.addButton("📂 Open File", QMessageBox.ButtonRole.ActionRole)
        open_folder_btn = msg.addButton("📁 Open Folder", QMessageBox.ButtonRole.ActionRole)
        
        msg.exec()
        
        # Handle button clicks
        if msg.clickedButton() == open_file_btn:
            self.open_file(file_path)
        elif msg.clickedButton() == open_folder_btn:
            self.open_folder(file_path)

    def open_file(self, file_path):
        """Open the generated file with default application"""
        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{file_path}'")
            else:  # Linux
                os.system(f"xdg-open '{file_path}'")
        except Exception as e:
            self.log_status(f'❌ <font color="red">Could not open file: {e}</font>')

    def open_folder(self, file_path):
        """Open the folder containing the generated file"""
        try:
            folder_path = os.path.dirname(file_path)
            if sys.platform == "win32":
                os.startfile(folder_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{folder_path}'")
            else:  # Linux
                os.system(f"xdg-open '{folder_path}'")
        except Exception as e:
            self.log_status(f'❌ <font color="red">Could not open folder: {e}</font>')

    def handle_task_completion(self, file_path):
        """Handle completion of the context generation task"""
        # Copy to clipboard if enabled
        if self.copy_to_clipboard_cb.isChecked():
            self.copy_to_clipboard(file_path)
        
        # Show notification if enabled
        if self.show_notification_cb.isChecked():
            # Use QTimer to delay the notification slightly so it appears after the final status update
            QTimer.singleShot(500, lambda: self.show_completion_notification(file_path))

    def start_generation(self):
        root_dir = self.dir_input.text()
        output_file = self.output_input.text()

        if not os.path.isdir(root_dir):
            self.log_status(f'❌ <font color="red"><b>ERROR:</b></font> Directory not found: {root_dir}', error=True)
            return
        
        excluded_folders = set(self.excluded_folders_edit.findChild(QTextEdit).toPlainText().split())
        excluded_files = set(self.excluded_files_edit.findChild(QTextEdit).toPlainText().split())
        excluded_extensions = set(self.excluded_extensions_edit.findChild(QTextEdit).toPlainText().split())

        self.set_controls_enabled(False)
        self.status_log.clear()
        self.progress_bar.setValue(0)
        self.log_status("🚀 Starting context generation...")

        self.thread = QThread()
        self.worker = Worker(root_dir, output_file, excluded_folders, excluded_files, excluded_extensions)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.set_controls_enabled(True))

        self.worker.status_update.connect(self.log_status)
        self.worker.progress.connect(lambda p: self.progress_bar.setValue(p))
        self.worker.error.connect(lambda msg: self.log_status(f'❌ <font color="red"><b>ERROR:</b></font> {msg}', error=True))
        self.worker.task_completed.connect(self.handle_task_completion)  # Connect new completion handler
        
        self.thread.start()

    def stop_generation(self):
        if self.worker:
            self.worker.stop()
        self.set_controls_enabled(True)

    def log_status(self, message, error=False):
        self.status_log.append(message)
        if error:
            pass
            
    def closeEvent(self, event):
        self.stop_generation()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())