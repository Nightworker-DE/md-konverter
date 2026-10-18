#!/usr/bin/env python3
import sys
import os
import markdown
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio

# Das HTML-Template mit modernem Kopier-Icon
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REPLACE_TITLE</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #1f2328;
            background: #ffffff;
        }
        h1, h2, h3, h4 { color: #1f2328; font-weight: 600; margin-top: 32px; margin-bottom: 16px; }
        h3 { font-size: 1.25em; border-bottom: 1px solid #d8dee4; padding-bottom: .3em; }
        p { margin-top: 0; margin-bottom: 16px; color: #3f3f46; }
        ul, ol { padding-left: 2em; margin-bottom: 16px; }
        li { margin-top: 0.25em; }

        .code-wrapper {
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            margin: 20px 0;
            overflow: hidden;
            background: #f6f8fa;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .code-header {
            background: #f6f8fa;
            padding: 10px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e1e4e8;
            font-size: 13px;
            color: #57606a;
            font-weight: 500;
        }
        .copy-btn {
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #57606a;
            border-radius: 4px;
            transition: all 0.2s;
        }
        .copy-btn:hover {
            background: #e4e6eb;
            color: #24292f;
        }
        .copy-btn svg {
            width: 16px;
            height: 16px;
        }
        pre { margin: 0 !important; padding: 16px !important; background: #ffffff !important; overflow-x: auto; }
        code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 85%; }
        pre code { padding: 0; background: transparent; font-size: 14px; display: block; color: #24292f; }
    </style>
</head>
<body>
    REPLACE_CONTENT
    <script>
        document.querySelectorAll('pre').forEach(pre => {
            const wrapper = document.createElement('div');
            wrapper.className = 'code-wrapper';

            const header = document.createElement('div');
            header.className = 'code-header';
            header.innerHTML = '<span>Bash</span>';

            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.title = 'Code kopieren';

            const copyIcon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>';
            const checkIcon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';

            btn.innerHTML = copyIcon;

            btn.addEventListener('click', () => {
                const codeEl = pre.querySelector('code');
                const text = codeEl ? codeEl.innerText : pre.innerText;
                navigator.clipboard.writeText(text).then(() => {
                    btn.innerHTML = checkIcon;
                    setTimeout(() => {
                        btn.innerHTML = copyIcon;
                    }, 2000);
                });
            });

            header.appendChild(btn);
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(header);
            wrapper.appendChild(pre);
        });
    </script>
</body>
</html>
"""

class MarkdownConverterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.example.MarkdownConverterGTK')
        self.selected_files = []
        self.last_dir = None
        self.window = None
        self.pending_output_dir = None

    def do_activate(self):
        self.window = Gtk.ApplicationWindow(application=self, title="Markdown zu HTML Konverter")
        self.window.set_default_size(500, 300)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_top(30)
        box.set_margin_bottom(30)
        box.set_margin_start(40)
        box.set_margin_end(40)
        self.window.set_child(box)

        label = Gtk.Label(label="Wähle eine oder mehrere Markdown-Dateien (.md) aus:")
        label.set_justify(Gtk.Justification.CENTER)
        box.append(label)

        btn = Gtk.Button(label="📁 Markdown-Dateien auswählen...")
        btn.set_css_classes(["suggested-action", "pill"])
        btn.connect("clicked", self.on_select_files_clicked, self.window)
        box.append(btn)

        self.status_label = Gtk.Label(label="Bereit.")
        self.status_label.set_wrap(True)
        box.append(self.status_label)

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        box.append(spacer)

        quit_btn = Gtk.Button(label="Beenden")
        quit_btn.set_halign(Gtk.Align.CENTER)
        quit_btn.set_size_request(120, -1)
        quit_btn.connect("clicked", lambda *_: self.quit())
        box.append(quit_btn)

        self.window.present()

    def on_select_files_clicked(self, button, window):
        dialog = Gtk.FileDialog.new()
        dialog.set_title("Markdown-Dateien auswählen (Mehrfachauswahl möglich)")

        f_filter = Gio.ListStore.new(Gtk.FileFilter)
        ff = Gtk.FileFilter()
        ff.set_name("Markdown Dateien")
        ff.add_pattern("*.md")
        ff.add_pattern("*.markdown")
        f_filter.append(ff)
        dialog.set_filters(f_filter)

        if self.last_dir and os.path.exists(self.last_dir):
            dialog.set_initial_folder(Gio.File.new_for_path(self.last_dir))

        dialog.open_multiple(window, None, self.on_files_selected, window)

    def on_files_selected(self, dialog, result, window):
        try:
            file_list = dialog.open_multiple_finish(result)
            if file_list:
                self.selected_files = []
                for i in range(file_list.get_n_items()):
                    f = file_list.get_item(i)
                    path = f.get_path()
                    self.selected_files.append(path)

                if self.selected_files:
                    self.last_dir = os.path.dirname(self.selected_files[0])

                    folder_dialog = Gio.File.new_for_path(self.last_dir)
                    target_dialog = Gtk.FileDialog.new()
                    target_dialog.set_title("Zielordner für die HTML-Dateien wählen")
                    target_dialog.set_initial_folder(folder_dialog)

                    target_dialog.select_folder(window, None, self.on_folder_selected)
        except Exception as e:
            pass

    def on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder and self.selected_files:
                output_dir = folder.get_path()
                self.pending_output_dir = output_dir

                # Prüfen, ob bereits Zieldateien existieren
                existing_files = []
                for file_path in self.selected_files:
                    title = os.path.splitext(os.path.basename(file_path))[0]
                    target_file = os.path.join(output_dir, title + ".html")
                    if os.path.exists(target_file):
                        existing_files.append(title + ".html")

                if existing_files:
                    # Eigener, absolut sicherer Abfrage-Dialog (Window)
                    self.show_overwrite_dialog(existing_files)
                else:
                    self.process_conversion(output_dir)

        except Exception as e:
            self.status_label.set_text(f"❌ Fehler bei Ordnerauswahl: {str(e)}")

    def show_overwrite_dialog(self, existing_files):
        dialog = Gtk.Window(transient_for=self.window, modal=True, title="Dateien überschreiben?")
        dialog.set_default_size(400, 200)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_margin_top(25)
        vbox.set_margin_bottom(25)
        vbox.set_margin_start(25)
        vbox.set_margin_end(25)
        dialog.set_child(vbox)

        names = ", ".join(existing_files[:3])
        if len(existing_files) > 3:
            names += " und weitere"

        lbl = Gtk.Label(label=f"Folgende Datei(en) existieren bereits:\n\n{names}\n\nMöchtest du sie überschreiben?")
        lbl.set_wrap(True)
        lbl.set_justify(Gtk.Justification.CENTER)
        vbox.append(lbl)

        # Buttons nebeneinander
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bbox.set_halign(Gtk.Align.CENTER)
        vbox.append(bbox)

        btn_cancel = Gtk.Button(label="Abbrechen")
        btn_cancel.set_size_request(100, -1)
        btn_cancel.connect("clicked", lambda *_: (dialog.destroy(), self.status_label.set_text("⚠️ Vorgang abgebrochen.")))
        bbox.append(btn_cancel)

        btn_overwrite = Gtk.Button(label="Überschreiben")
        btn_overwrite.set_size_request(100, -1)
        btn_overwrite.set_css_classes(["suggested-action"])
        btn_overwrite.connect("clicked", lambda *_: (dialog.destroy(), self.process_conversion(self.pending_output_dir)))
        bbox.append(btn_overwrite)

        dialog.present()

    def process_conversion(self, output_dir):
        success_count = 0
        for file_path in self.selected_files:
            if self.convert_single_file(file_path, output_dir):
                success_count += 1

        self.status_label.set_text(f"✅ {success_count} von {len(self.selected_files)} Dateien erfolgreich\ngespeichert in: {output_dir}")

    def convert_single_file(self, file_path, output_dir):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            text = text.replace("Verwende Code mit Vorsicht.", "")
            html_body = markdown.markdown(text, extensions=['fenced_code', 'tables', 'sane_lists'])

            title = os.path.splitext(os.path.basename(file_path))[0]
            output_file = os.path.join(output_dir, title + ".html")

            final_html = HTML_TEMPLATE.replace("REPLACE_TITLE", title)
            final_html = final_html.replace("REPLACE_CONTENT", html_body)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_html)

            return True
        except Exception as e:
            print(f"Fehler bei {file_path}: {e}")
            return False

if __name__ == '__main__':
    app = MarkdownConverterApp()
    app.run(sys.argv)
