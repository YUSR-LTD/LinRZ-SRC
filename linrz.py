#!/usr/bin/env python3
"""
YUSR LinRZ - Universal Compression Tool with GUI
Supports: .zip, .rar, .7z, .tar.gz, .tar.bz2, .tar.xz, and more
"""

import os
import sys
import zipfile
import tarfile
import shutil
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False

try:
    import rarfile
    HAS_RAR = True
except ImportError:
    HAS_RAR = False


class CompressionEngine:
    """Compression and decompression engine"""
    
    SUPPORTED_FORMATS = {
        'compress': ['.zip', '.tar.gz', '.tar.bz2', '.tar.xz', '.7z'],
        'decompress': ['.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz']
    }
    
    def __init__(self, progress_callback=None):
        self.stats = {'files': 0, 'size': 0}
        self.progress_callback = progress_callback
    
    def _update_progress(self, message):
        if self.progress_callback:
            self.progress_callback(message)
    
    def compress(self, source_path, output_file, format_type='zip'):
        """Compress files or directories"""
        source = Path(source_path)
        self.stats = {'files': 0, 'size': 0}
        
        if not source.exists():
            raise FileNotFoundError(f"Source path not found: {source_path}")
        
        self._update_progress(f"Starting compression to {format_type.upper()}...")
        
        if format_type == 'zip':
            self._compress_zip(source, output_file)
        elif format_type in ['tar.gz', 'tgz']:
            self._compress_tar(source, output_file, 'gz')
        elif format_type == 'tar.bz2':
            self._compress_tar(source, output_file, 'bz2')
        elif format_type == 'tar.xz':
            self._compress_tar(source, output_file, 'xz')
        elif format_type == '7z':
            self._compress_7z(source, output_file)
        else:
            raise ValueError(f"Unsupported compression format: {format_type}")
        
        output_size = Path(output_file).stat().st_size
        compression_ratio = (1 - output_size / self.stats['size']) * 100 if self.stats['size'] > 0 else 0
        
        return {
            'files': self.stats['files'],
            'original_size': self.stats['size'],
            'compressed_size': output_size,
            'ratio': compression_ratio
        }
    
    def decompress(self, archive_path, output_dir=None):
        """Decompress archive files"""
        archive = Path(archive_path)
        self.stats = {'files': 0, 'size': 0}
        
        if not archive.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        
        if output_dir is None:
            output_dir = archive.stem
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self._update_progress(f"Starting extraction...")
        
        ext = ''.join(archive.suffixes).lower()
        
        if ext == '.zip':
            self._decompress_zip(archive, output_path)
        elif ext == '.rar':
            self._decompress_rar(archive, output_path)
        elif ext == '.7z':
            self._decompress_7z(archive, output_path)
        elif ext in ['.tar.gz', '.tgz', '.tar.bz2', '.tar.xz', '.tar']:
            self._decompress_tar(archive, output_path)
        else:
            raise ValueError(f"Unsupported archive format: {ext}")
        
        return {
            'files': self.stats['files'],
            'output_path': str(output_path.absolute())
        }
    
    def _compress_zip(self, source, output_file):
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            if source.is_file():
                zf.write(source, source.name)
                self.stats['files'] = 1
                self.stats['size'] = source.stat().st_size
                self._update_progress(f"Added: {source.name}")
            else:
                for file_path in source.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source.parent)
                        zf.write(file_path, arcname)
                        self.stats['files'] += 1
                        self.stats['size'] += file_path.stat().st_size
                        self._update_progress(f"Adding: {arcname}")
    
    def _compress_tar(self, source, output_file, compression):
        mode_map = {'gz': 'w:gz', 'bz2': 'w:bz2', 'xz': 'w:xz'}
        mode = mode_map.get(compression, 'w')
        
        with tarfile.open(output_file, mode) as tf:
            if source.is_file():
                tf.add(source, arcname=source.name)
                self.stats['files'] = 1
                self.stats['size'] = source.stat().st_size
                self._update_progress(f"Added: {source.name}")
            else:
                for file_path in source.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source.parent)
                        tf.add(file_path, arcname=arcname)
                        self.stats['files'] += 1
                        self.stats['size'] += file_path.stat().st_size
                        self._update_progress(f"Adding: {arcname}")
    
    def _compress_7z(self, source, output_file):
        if not HAS_7Z:
            raise ImportError("py7zr not installed. Install with: pip install py7zr")
        
        with py7zr.SevenZipFile(output_file, 'w') as zf:
            if source.is_file():
                zf.write(source, source.name)
                self.stats['files'] = 1
                self.stats['size'] = source.stat().st_size
                self._update_progress(f"Added: {source.name}")
            else:
                for file_path in source.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source.parent)
                        zf.write(file_path, arcname)
                        self.stats['files'] += 1
                        self.stats['size'] += file_path.stat().st_size
                        self._update_progress(f"Adding: {arcname}")
    
    def _decompress_zip(self, archive, output_path):
        with zipfile.ZipFile(archive, 'r') as zf:
            members = zf.namelist()
            self.stats['files'] = len(members)
            for member in members:
                self._update_progress(f"Extracting: {member}")
                zf.extract(member, output_path)
    
    def _decompress_rar(self, archive, output_path):
        if not HAS_RAR:
            raise ImportError("rarfile not installed. Install with: pip install rarfile")
        
        with rarfile.RarFile(archive) as rf:
            members = rf.namelist()
            self.stats['files'] = len(members)
            for member in members:
                self._update_progress(f"Extracting: {member}")
                rf.extract(member, output_path)
    
    def _decompress_7z(self, archive, output_path):
        if not HAS_7Z:
            raise ImportError("py7zr not installed. Install with: pip install py7zr")
        
        with py7zr.SevenZipFile(archive, 'r') as zf:
            members = zf.getnames()
            self.stats['files'] = len(members)
            zf.extractall(output_path)
            for member in members:
                self._update_progress(f"Extracting: {member}")
    
    def _decompress_tar(self, archive, output_path):
        with tarfile.open(archive, 'r:*') as tf:
            members = tf.getmembers()
            self.stats['files'] = len(members)
            for member in members:
                self._update_progress(f"Extracting: {member.name}")
                tf.extract(member, output_path)
    
    @staticmethod
    def format_size(size):
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


class YUSRLinRZGUI:
    """GUI Application for YUSR LinRZ"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("YUSR LinRZ - Universal Compressor")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        self.engine = CompressionEngine(self.update_progress)
        self.current_dir = os.path.expanduser("~")
        
        self.setup_ui()
        self.refresh_file_list()
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add to Archive...", command=self.compress_dialog)
        file_menu.add_command(label="Extract Archive...", command=self.extract_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Toolbar
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="Add", command=self.compress_dialog, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Extract", command=self.extract_dialog, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Test", command=self.test_archive, width=10).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        ttk.Button(toolbar, text="Up", command=self.go_up, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_file_list, width=10).pack(side=tk.LEFT, padx=2)
        
        # Path bar
        path_frame = ttk.Frame(self.root, padding="5")
        path_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(path_frame, text="Location:").pack(side=tk.LEFT, padx=5)
        self.path_var = tk.StringVar(value=self.current_dir)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        path_entry.bind('<Return>', lambda e: self.change_directory())
        
        ttk.Button(path_frame, text="Browse", command=self.browse_directory).pack(side=tk.LEFT, padx=2)
        
        # File list
        list_frame = ttk.Frame(self.root, padding="5")
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(list_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.file_tree = ttk.Treeview(list_frame, 
                                       columns=('Size', 'Modified', 'Type'),
                                       yscrollcommand=tree_scroll_y.set,
                                       xscrollcommand=tree_scroll_x.set,
                                       selectmode='extended')
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll_y.config(command=self.file_tree.yview)
        tree_scroll_x.config(command=self.file_tree.xview)
        
        # Configure columns
        self.file_tree.heading('#0', text='Name', anchor=tk.W)
        self.file_tree.heading('Size', text='Size', anchor=tk.E)
        self.file_tree.heading('Modified', text='Modified', anchor=tk.W)
        self.file_tree.heading('Type', text='Type', anchor=tk.W)
        
        self.file_tree.column('#0', width=300, minwidth=150)
        self.file_tree.column('Size', width=100, minwidth=80, anchor=tk.E)
        self.file_tree.column('Modified', width=150, minwidth=120)
        self.file_tree.column('Type', width=100, minwidth=80)
        
        # Double-click to navigate
        self.file_tree.bind('<Double-Button-1>', self.on_double_click)
        
        # Progress frame
        progress_frame = ttk.Frame(self.root, padding="5")
        progress_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, anchor=tk.W)
        self.progress_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status bar
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding="2")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="YUSR LinRZ v1.0 - Ready")
        ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def refresh_file_list(self):
        """Refresh the file listing"""
        self.file_tree.delete(*self.file_tree.get_children())
        
        try:
            path = Path(self.current_dir)
            self.path_var.set(str(path))
            
            items = []
            
            # Add parent directory
            if path.parent != path:
                items.append(('..',  {'type': 'folder', 'size': '', 'modified': ''}))
            
            # List directories and files
            for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    stat = item.stat()
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    
                    if item.is_dir():
                        items.append((item.name, {
                            'type': 'Folder',
                            'size': '',
                            'modified': modified
                        }))
                    else:
                        size = self.engine.format_size(stat.st_size)
                        file_type = item.suffix[1:].upper() if item.suffix else 'File'
                        items.append((item.name, {
                            'type': file_type,
                            'size': size,
                            'modified': modified
                        }))
                except (PermissionError, OSError):
                    continue
            
            # Insert items into tree
            for name, data in items:
                icon = '📁' if data['type'] in ['Folder', 'folder'] else '📄'
                self.file_tree.insert('', tk.END, text=f'{icon} {name}',
                                     values=(data['size'], data['modified'], data['type']))
            
            self.status_var.set(f"Items: {len(items)}")
            
        except PermissionError:
            messagebox.showerror("Error", "Permission denied to access this directory")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading directory: {e}")
    
    def on_double_click(self, event):
        """Handle double-click on tree item"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item = self.file_tree.item(selection[0])
        name = item['text'].split(' ', 1)[1] if ' ' in item['text'] else item['text']
        item_type = item['values'][2] if item['values'] else ''
        
        if name == '..':
            self.go_up()
        elif item_type == 'Folder':
            self.current_dir = str(Path(self.current_dir) / name)
            self.refresh_file_list()
        elif item_type.lower() in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz']:
            # Ask to extract archive
            if messagebox.askyesno("Extract", f"Extract {name}?"):
                archive_path = str(Path(self.current_dir) / name)
                self.extract_archive(archive_path)
    
    def go_up(self):
        """Navigate to parent directory"""
        path = Path(self.current_dir)
        if path.parent != path:
            self.current_dir = str(path.parent)
            self.refresh_file_list()
    
    def change_directory(self):
        """Change to directory entered in path bar"""
        new_path = Path(self.path_var.get())
        if new_path.exists() and new_path.is_dir():
            self.current_dir = str(new_path)
            self.refresh_file_list()
        else:
            messagebox.showerror("Error", "Invalid directory path")
            self.path_var.set(self.current_dir)
    
    def browse_directory(self):
        """Browse for a directory"""
        directory = filedialog.askdirectory(initialdir=self.current_dir)
        if directory:
            self.current_dir = directory
            self.refresh_file_list()
    
    def compress_dialog(self):
        """Show compress dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add to Archive")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Source selection
        source_frame = ttk.LabelFrame(dialog, text="Files to Compress", padding="10")
        source_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        source_var = tk.StringVar()
        ttk.Entry(source_frame, textvariable=source_var).pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(source_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add File", 
                  command=lambda: self.select_file(source_var)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Add Folder", 
                  command=lambda: self.select_folder(source_var)).pack(side=tk.LEFT, padx=2)
        
        # Output settings
        output_frame = ttk.LabelFrame(dialog, text="Archive Settings", padding="10")
        output_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(output_frame, text="Archive name:").pack(anchor=tk.W, pady=2)
        output_var = tk.StringVar(value="archive.zip")
        ttk.Entry(output_frame, textvariable=output_var).pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Format:").pack(anchor=tk.W, pady=2)
        format_var = tk.StringVar(value="zip")
        format_combo = ttk.Combobox(output_frame, textvariable=format_var, 
                                    values=['zip', 'tar.gz', 'tar.bz2', 'tar.xz', '7z'],
                                    state='readonly')
        format_combo.pack(fill=tk.X, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def do_compress():
            source = source_var.get()
            output = output_var.get()
            fmt = format_var.get()
            
            if not source or not output:
                messagebox.showerror("Error", "Please select source and output")
                return
            
            dialog.destroy()
            self.compress_files(source, output, fmt)
        
        ttk.Button(button_frame, text="OK", command=do_compress).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def extract_dialog(self):
        """Show extract dialog"""
        archive_path = filedialog.askopenfilename(
            title="Select Archive",
            filetypes=[
                ("All Archives", "*.zip;*.rar;*.7z;*.tar;*.tar.gz;*.tar.bz2;*.tar.xz;*.tgz"),
                ("ZIP files", "*.zip"),
                ("RAR files", "*.rar"),
                ("7Z files", "*.7z"),
                ("TAR files", "*.tar;*.tar.gz;*.tar.bz2;*.tar.xz;*.tgz"),
                ("All files", "*.*")
            ]
        )
        
        if archive_path:
            output_dir = filedialog.askdirectory(title="Select Output Directory",
                                                 initialdir=self.current_dir)
            if output_dir:
                self.extract_archive(archive_path, output_dir)
    
    def select_file(self, var):
        """Select file for compression"""
        filename = filedialog.askopenfilename(initialdir=self.current_dir)
        if filename:
            var.set(filename)
    
    def select_folder(self, var):
        """Select folder for compression"""
        folder = filedialog.askdirectory(initialdir=self.current_dir)
        if folder:
            var.set(folder)
    
    def compress_files(self, source, output, format_type):
        """Compress files in background thread"""
        def task():
            try:
                result = self.engine.compress(source, output, format_type)
                self.root.after(0, lambda: self.compression_complete(result, output))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.progress_var.set("Ready"))
        
        threading.Thread(target=task, daemon=True).start()
    
    def extract_archive(self, archive_path, output_dir=None):
        """Extract archive in background thread"""
        def task():
            try:
                result = self.engine.decompress(archive_path, output_dir)
                self.root.after(0, lambda: self.extraction_complete(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.progress_var.set("Ready"))
        
        threading.Thread(target=task, daemon=True).start()
    
    def compression_complete(self, result, output):
        """Handle compression completion"""
        msg = f"Compression complete!\n\n"
        msg += f"Files: {result['files']}\n"
        msg += f"Original size: {self.engine.format_size(result['original_size'])}\n"
        msg += f"Compressed size: {self.engine.format_size(result['compressed_size'])}\n"
        msg += f"Compression ratio: {result['ratio']:.1f}%\n"
        msg += f"\nArchive saved to:\n{output}"
        
        messagebox.showinfo("Success", msg)
        self.progress_var.set("Ready")
        self.refresh_file_list()
    
    def extraction_complete(self, result):
        """Handle extraction completion"""
        msg = f"Extraction complete!\n\n"
        msg += f"Files extracted: {result['files']}\n"
        msg += f"Output directory:\n{result['output_path']}"
        
        messagebox.showinfo("Success", msg)
        self.progress_var.set("Ready")
        self.refresh_file_list()
    
    def test_archive(self):
        """Test selected archive"""
        messagebox.showinfo("Test", "Archive testing feature coming soon!")
    
    def update_progress(self, message):
        """Update progress message"""
        self.root.after(0, lambda: self.progress_var.set(message))
    
    def show_about(self):
        """Show about dialog"""
        about_text = """YUSR LinRZ v1.0
Universal Compression Tool

Supports: ZIP, RAR, 7Z, TAR, TAR.GZ, TAR.BZ2, TAR.XZ

Created with Python and tkinter

© 2025"""
        messagebox.showinfo("About YUSR LinRZ", about_text)


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = YUSRLinRZGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
