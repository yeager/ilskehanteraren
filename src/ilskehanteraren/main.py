"""Ilskehanteraren - Step-by-step anger management for children."""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio
import gettext, locale, os, json, time

__version__ = "0.1.0"
APP_ID = "se.danielnylander.ilskehanteraren"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'share', 'locale')
if not os.path.isdir(LOCALE_DIR): LOCALE_DIR = "/usr/share/locale"
try:
    locale.bindtextdomain(APP_ID, LOCALE_DIR)
    gettext.bindtextdomain(APP_ID, LOCALE_DIR)
    gettext.textdomain(APP_ID)
except Exception: pass
_ = gettext.gettext

def N_(s): return s

# Anger levels
ANGER_LEVELS = [
    {"name": N_("A little annoyed"), "icon": "😤", "color": "#fbbf24"},
    {"name": N_("Frustrated"), "icon": "😠", "color": "#f97316"},
    {"name": N_("Angry"), "icon": "😡", "color": "#ef4444"},
    {"name": N_("Very angry"), "icon": "🤬", "color": "#dc2626"},
    {"name": N_("Explosion"), "icon": "💥", "color": "#991b1b"},
]

# Calm-down strategies
STRATEGIES = [
    {"name": N_("Deep Breathing"), "icon": "🌬️",
     "steps": [N_("Stop what you're doing"), N_("Breathe in through your nose... 1, 2, 3, 4"),
               N_("Hold... 1, 2, 3"), N_("Breathe out through your mouth... 1, 2, 3, 4, 5"),
               N_("Repeat 3 times"), N_("How do you feel now?")]},
    {"name": N_("Walk Away"), "icon": "🚶",
     "steps": [N_("Tell someone you need a break"), N_("Walk to a calm place"),
               N_("Stay there for 5 minutes"), N_("Think about what happened"),
               N_("When you're calm, go back")]},
    {"name": N_("Count Down"), "icon": "🔢",
     "steps": [N_("Close your eyes"), N_("Count slowly from 10 to 1"),
               N_("10... 9... 8... 7... 6..."), N_("5... 4... 3... 2... 1..."),
               N_("Open your eyes"), N_("Take a deep breath")]},
    {"name": N_("Squeeze and Release"), "icon": "✊",
     "steps": [N_("Make tight fists with both hands"), N_("Squeeze as hard as you can"),
               N_("Hold for 5 seconds"), N_("Now release and shake your hands"),
               N_("Feel the tension leaving"), N_("Do it again if needed")]},
    {"name": N_("Talk About It"), "icon": "💬",
     "steps": [N_("Find a trusted person"), N_("Say: 'I feel angry because...'"),
               N_("Let them listen"), N_("Ask for help if you need it"),
               N_("Make a plan together")]},
]


class IlskeWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_("Ilskehanteraren"))
        self.set_default_size(500, 600)
        self._current_step = 0
        self._current_strategy = None
        self._log = []

        
        # Easter egg state
        self._egg_clicks = 0
        self._egg_timer = None

        header = Adw.HeaderBar()
        
        # Add clickable app icon for easter egg
        app_btn = Gtk.Button()
        app_btn.set_icon_name("se.danielnylander.ilskehanteraren")
        app_btn.add_css_class("flat")
        app_btn.set_tooltip_text(_("Ilskehanteraren"))
        app_btn.connect("clicked", self._on_icon_clicked)
        header.pack_start(app_btn)

        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu = Gio.Menu()
        menu.append(_("About"), "app.about")
        menu_btn.set_menu_model(menu)
        header.pack_end(menu_btn)

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)

        # === Check-in page ===
        checkin = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        checkin.set_margin_top(24)
        checkin.set_margin_bottom(24)
        checkin.set_margin_start(24)
        checkin.set_margin_end(24)

        q = Gtk.Label(label=_("How angry are you right now?"))
        q.add_css_class("title-2")
        q.set_wrap(True)
        checkin.append(q)

        for i, level in enumerate(ANGER_LEVELS):
            btn = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            icon = Gtk.Label(label=level["icon"])
            icon.add_css_class("title-2")
            box.append(icon)
            name = Gtk.Label(label=_(level["name"]))
            name.add_css_class("title-4")
            name.set_hexpand(True)
            name.set_xalign(0)
            box.append(name)
            btn.set_child(box)
            btn.add_css_class("card")
            btn.connect("clicked", self._on_level_chosen, i)
            checkin.append(btn)

        self._stack.add_titled(checkin, "checkin", _("Check-in"))

        # === Strategy picker ===
        strat_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        strat_page.set_margin_top(24)
        strat_page.set_margin_bottom(24)
        strat_page.set_margin_start(24)
        strat_page.set_margin_end(24)

        self._strat_title = Gtk.Label(label=_("Choose a calming strategy"))
        self._strat_title.add_css_class("title-2")
        strat_page.append(self._strat_title)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        strat_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        for i, strat in enumerate(STRATEGIES):
            btn = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(8)
            box.set_margin_end(8)
            icon = Gtk.Label(label=strat["icon"])
            icon.add_css_class("title-2")
            box.append(icon)
            name = Gtk.Label(label=_(strat["name"]))
            name.add_css_class("title-4")
            box.append(name)
            btn.set_child(box)
            btn.add_css_class("card")
            btn.connect("clicked", self._on_strategy_chosen, i)
            strat_list.append(btn)

        scroll.set_child(strat_list)
        strat_page.append(scroll)

        back1 = Gtk.Button(label=_("← Back"))
        back1.add_css_class("pill")
        back1.connect("clicked", lambda b: self._stack.set_visible_child_name("checkin"))
        strat_page.append(back1)

        self._stack.add_titled(strat_page, "strategies", _("Strategies"))

        # === Step-by-step page ===
        step_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        step_page.set_margin_top(32)
        step_page.set_margin_bottom(32)
        step_page.set_margin_start(32)
        step_page.set_margin_end(32)
        step_page.set_valign(Gtk.Align.CENTER)

        self._step_icon = Gtk.Label()
        self._step_icon.add_css_class("title-1")
        step_page.append(self._step_icon)

        self._step_number = Gtk.Label()
        self._step_number.add_css_class("dim-label")
        step_page.append(self._step_number)

        self._step_text = Gtk.Label()
        self._step_text.add_css_class("title-2")
        self._step_text.set_wrap(True)
        self._step_text.set_justify(Gtk.Justification.CENTER)
        step_page.append(self._step_text)

        self._step_progress = Gtk.ProgressBar()
        step_page.append(self._step_progress)

        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        nav.set_halign(Gtk.Align.CENTER)

        self._prev_btn = Gtk.Button(label=_("← Previous"))
        self._prev_btn.add_css_class("pill")
        self._prev_btn.connect("clicked", self._on_prev_step)
        nav.append(self._prev_btn)

        self._next_btn = Gtk.Button(label=_("Next →"))
        self._next_btn.add_css_class("suggested-action")
        self._next_btn.add_css_class("pill")
        self._next_btn.connect("clicked", self._on_next_step)
        nav.append(self._next_btn)

        step_page.append(nav)
        self._stack.add_titled(step_page, "steps", _("Steps"))

        # === Done page ===
        done_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        done_page.set_valign(Gtk.Align.CENTER)
        done_page.set_margin_top(48)
        done_page.set_margin_bottom(48)
        done_page.set_margin_start(32)
        done_page.set_margin_end(32)

        done_icon = Gtk.Label(label="🌟")
        done_icon.add_css_class("title-1")
        done_page.append(done_icon)

        done_text = Gtk.Label(label=_("Great job! You handled your anger!"))
        done_text.add_css_class("title-2")
        done_text.set_wrap(True)
        done_text.set_justify(Gtk.Justification.CENTER)
        done_page.append(done_text)

        self._done_feel = Gtk.Label(label=_("How do you feel now?"))
        self._done_feel.add_css_class("title-4")
        done_page.append(self._done_feel)

        feel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        feel_box.set_halign(Gtk.Align.CENTER)
        for emoji in ["😊", "😐", "😤"]:
            btn = Gtk.Button(label=emoji)
            btn.add_css_class("circular")
            btn.connect("clicked", self._on_feel_after, emoji)
            feel_box.append(btn)
        done_page.append(feel_box)

        restart = Gtk.Button(label=_("Start over"))
        restart.add_css_class("pill")
        restart.connect("clicked", lambda b: self._stack.set_visible_child_name("checkin"))
        done_page.append(restart)

        self._stack.add_titled(done_page, "done", _("Done"))

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(header)
        main_box.append(self._stack)
        self.set_content(main_box)

    def _on_level_chosen(self, btn, level_index):
        level = ANGER_LEVELS[level_index]
        self._strat_title.set_text(_("You feel: %s %s\nChoose a strategy:") % (level["icon"], _(level["name"])))
        self._stack.set_visible_child_name("strategies")

    def _on_strategy_chosen(self, btn, strat_index):
        self._current_strategy = STRATEGIES[strat_index]
        self._current_step = 0
        self._update_step_display()
        self._stack.set_visible_child_name("steps")

    def _update_step_display(self):
        strat = self._current_strategy
        steps = strat["steps"]
        self._step_icon.set_text(strat["icon"])
        self._step_number.set_text(_("Step %d of %d") % (self._current_step + 1, len(steps)))
        self._step_text.set_text(_(steps[self._current_step]))
        self._step_progress.set_fraction((self._current_step + 1) / len(steps))
        self._prev_btn.set_sensitive(self._current_step > 0)
        self._next_btn.set_label(_("Done ✓") if self._current_step == len(steps) - 1 else _("Next →"))

    def _on_prev_step(self, btn):
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step_display()

    def _on_next_step(self, btn):
        steps = self._current_strategy["steps"]
        if self._current_step < len(steps) - 1:
            self._current_step += 1
            self._update_step_display()
        else:
            self._stack.set_visible_child_name("done")

    def _on_feel_after(self, btn, emoji):
        self._done_feel.set_text(_("You feel %s — that's okay!") % emoji)

    def _on_icon_clicked(self, *args):
        """Handle clicks on app icon for easter egg."""
        self._egg_clicks += 1
        if self._egg_timer:
            GLib.source_remove(self._egg_timer)
        self._egg_timer = GLib.timeout_add(500, self._reset_egg)
        if self._egg_clicks >= 7:
            self._trigger_easter_egg()
            self._egg_clicks = 0

    def _reset_egg(self):
        """Reset easter egg click counter."""
        self._egg_clicks = 0
        self._egg_timer = None
        return False

    def _trigger_easter_egg(self):
        """Show the secret easter egg!"""
        try:
            # Play a fun sound
            import subprocess
            subprocess.Popen(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            # Fallback beep
            try:
                subprocess.Popen(['pactl', 'play-sample', 'bell'], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass

        # Show confetti message
        toast = Adw.Toast.new(_("🎉 Du hittade hemligheten!"))
        toast.set_timeout(3)
        
        # Create toast overlay if it doesn't exist
        if not hasattr(self, '_toast_overlay'):
            content = self.get_content()
            self._toast_overlay = Adw.ToastOverlay()
            self._toast_overlay.set_child(content)
            self.set_content(self._toast_overlay)
        
        self._toast_overlay.add_toast(toast)



class IlskeApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", self._on_activate)
        about = Gio.SimpleAction.new("about", None)
        about.connect("activate", self._on_about)
        self.add_action(about)

    def _on_activate(self, app):
        win = IlskeWindow(application=app)
        win.present()

    def _on_about(self, action, param):
        about = Adw.AboutDialog(
            application_name=_("Ilskehanteraren"),
            application_icon=APP_ID,
            version=__version__,
            developer_name="Daniel Nylander",
            website="https://github.com/yeager/ilskehanteraren",
            license_type=Gtk.License.GPL_3_0,
            comments=_("Step-by-step anger management for children with NPF"),
            developers=["Daniel Nylander <daniel@danielnylander.se>"],
        )
        about.present(self.get_active_window())

def main():
    app = IlskeApp()
    app.run()

if __name__ == "__main__":
    main()
