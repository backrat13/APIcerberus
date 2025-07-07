'''python
import sys
import os
from collections import defaultdict
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk
from .scanner import scan_processes
from .utils import kill_process

class ApiSecurityCheckWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("API Security Check")
        self.set_default_size(700, 800)
        self.add_css_class("background")

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.add_css_class("toast-overlay")
        self.set_content(self.toast_overlay)

        # Main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.add_css_class("main-box")
        self.toast_overlay.set_child(self.main_box)

        # Header bar with refresh button
        header = Adw.HeaderBar()
        self.main_box.append(header)

        reload_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        reload_button.set_tooltip_text("Reload Theme")
        reload_button.connect("clicked", self.on_reload_theme_clicked)
        header.pack_start(reload_button)

        self.refresh_button = Gtk.Button(label="Refresh")
        self.refresh_button.connect("clicked", self.on_refresh_clicked)
        header.pack_end(self.refresh_button)

        # Scrolled window for the list
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add_css_class("main-scroll")
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.main_box.append(scrolled_window)

        # Main listbox to hold category expanders
        self.main_list_box = Gtk.ListBox()
        self.main_list_box.add_css_class("boxed-list")
        self.main_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled_window.set_child(self.main_list_box)

        # Bottom action bar with Kill button
        action_bar = Gtk.ActionBar()
        self.main_box.append(action_bar)
        self.kill_button = Gtk.Button(label="Kill Selected API")
        self.kill_button.add_css_class("destructive-action")
        self.kill_button.connect("clicked", self.on_kill_clicked)
        self.kill_button.set_sensitive(False)
        action_bar.pack_start(self.kill_button)

        self.selected_pid = None

    def on_reload_theme_clicked(self, widget):
        app = self.get_application()
        app.reload_css()

    def on_kill_clicked(self, widget):
        if self.selected_pid:
            pid_to_kill = self.selected_pid
            print(f"Attempting to kill process with PID: {pid_to_kill}")
            if kill_process(pid_to_kill):
                toast = Adw.Toast.new(f"Process {pid_to_kill} terminated.")
                self.toast_overlay.add_toast(toast)
                self.update_api_list()
            else:
                dialog = Adw.MessageDialog(
                    heading="Error",
                    body=f"Failed to terminate process {self.selected_pid}.",
                    transient_for=self,
                )
                dialog.add_response("ok", "OK")
                dialog.connect("response", lambda d, r: d.destroy())
                dialog.present()
        self.kill_button.set_sensitive(False)
        self.selected_pid = None

    def on_refresh_clicked(self, widget):
        self.update_api_list()

    def clear_list(self):
        while child := self.main_list_box.get_first_child():
            self.main_list_box.remove(child)
        self.kill_button.set_sensitive(False)
        self.kill_button.remove_css_class("pulse")
        self.selected_pid = None

    def update_api_list(self):
        self.clear_list()

        apis = scan_processes()

        if not apis:
            status_page = Adw.StatusPage(
                title="No APIs Found",
                description="The scan didn't find any running applications with open network ports.",
                icon_name="view-reveal-symbolic",
            )
            self.main_list_box.append(status_page)
            return

        grouped_apis = defaultdict(list)
        for api in apis:
            grouped_apis[api['category']].append(api)

        for category, api_list in sorted(grouped_apis.items()):
            expander = Adw.ExpanderRow(
                title=category,
                subtitle=f"{len(api_list)} running"
            )
            expander.add_css_class("expander-row")
            self.main_list_box.append(expander)

            for api in api_list:
                row = Adw.ActionRow(
                    title=f"{api['name']} (PID: {api['pid']})",
                    subtitle=f"{api['address']}:{api['port']}"
                )
                row.add_css_class("action-row")
                row.set_tooltip_text(api.get("description", "No description available."))
                row.set_name(str(api['pid']))

                if api.get('is_suspicious', False):
                    row.add_css_class("error")
                    icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
                    row.add_prefix(icon)

                row.connect("activated", self.on_row_activated)
                expander.add_row(row)

    def on_row_activated(self, row):
        self.selected_pid = int(row.get_name())
        self.kill_button.set_sensitive(True)
        if row.has_css_class("error"):
            self.kill_button.add_css_class("pulse")
        else:
            self.kill_button.remove_css_class("pulse")

class ApiSecurityCheckApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.css_provider = Gtk.CssProvider()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.css_path = os.path.join(self.script_dir, "theme.css")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.load_css()
        # Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self.win = ApiSecurityCheckWindow(application=app)
        self.win.present()
        self.win.update_api_list()

    def load_css(self):
        print("Looking for theme.css at:", self.css_path)
        print("Exists:", os.path.exists(self.css_path))
        try:
            self.css_provider.load_from_path(self.css_path)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
            )
            print(f"Initial theme loaded from: {self.css_path}")
        except Exception as e:
            print(f"Failed to load CSS: {e}")

    def reload_css(self):
        try:
            self.css_provider.load_from_path(self.css_path)
            print(f"Theme reloaded successfully from: {self.css_path}")
        except Exception as e:
            print(f"Error reloading CSS: {e}")

def main():
    app = ApiSecurityCheckApp(application_id="com.windsurf.ApiSecurityCheck")
    app.run(sys.argv)

if __name__ == "__main__":
    main()
