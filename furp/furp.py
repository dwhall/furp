#!/usr/bin/env python3

"""Furp - Framework for Urwid Plugins

Uses Urwid (www.urwid.org) and asyncio
to make an app with one standard layout.
One plugin at a time is activated by the user.
The app layout has a menu bar at the top,
a body widget occupying most of the screen
and a status bar at the bottom.
"""
import plugin

import collections, importlib, os, sys, time
try: import asyncio
except: import trollius as asyncio # trollius is Third Party

import urwid # 1.3.1


__version__ = (0,0,1)


class PluginSelectorPopup(urwid.WidgetWrap):
    """Fills the plugin popup with a button for every plugin.
    Appends the Quit button.
    """
    signals = ['close']
    def __init__(self, framework):
        self.framework = framework
        buttons = []
        for plug_info in framework.get_plugins().values():
            buttons.append(urwid.AttrMap(urwid.Button(plug_info['name'], on_press=self.buttonpress), None, focus_map="reversed"))
        buttons.append(urwid.AttrMap(urwid.Button("Quit", on_press=self.framework.quit), None, focus_map="reversed"))
        pile = urwid.Pile(buttons)
        fill = urwid.Filler(pile, valign='top')
        super().__init__(urwid.AttrWrap(fill, 'popbg'))


    def buttonpress(self, button):
        self.framework.activate_plugin(button)
        self._emit("close")


    def keypress(self, size, key):
        if key == "esc":
            self._emit("close")
        else:
            return super().keypress(size, key)


class SquareMenuButton(urwid.PopUpLauncher):
    SquareButton = urwid.Button
    SquareButton.button_left = urwid.Text('[')
    SquareButton.button_right = urwid.Text(']')


    def __init__(self, framework, label, on_click=None):
        self.framework = framework
        super().__init__(SquareMenuButton.SquareButton(label, on_click, label))
        if not on_click:
            urwid.connect_signal(self.original_widget, 'click', lambda button: self.open_pop_up())


    def create_pop_up(self,):
        pop_up = PluginSelectorPopup(self.framework)
        urwid.connect_signal(pop_up, 'close',
            lambda button: self.close_pop_up())
        return pop_up


    def get_pop_up_parameters(self,):
        return {'left':0, 'top':1, 'overlay_width':16, 'overlay_height':14}


class Furp:
    """Manages the widgets of the core application.
    """
    # TODO: put CFG_* into a Config module with persistent storage
    CFG_DT_FORMAT = "%Y/%m/%d %H:%M"
    CFG_DT_UPDT_RATE = 5.0
    CFG_STATUS_TEMPORARY_DURATION = 5.0

    # Default constants (overridden by a valid config value)
    DFLT_DT_FORMAT = "%Y/%m/%d %H:%M"


    #
    # Framework
    #
    def __init__(self, loop):
        self._init_widgets(loop)
        self._init_plugins()


    def _get_app_name(self):
        return self.__class__.__name__


    def _on_unhandled_input(self, input):
        """The application framework intercepts this small set of keypresses.
        Function keys 1-8 activate menu items.
        F1 shows the plugin selector popup.
        F2-F8 activate the plugin's menu items.
        """
        if input == 'f1':
            self.furp_button.keypress(0, 'enter')
            return True
        elif input in ('f2','f3','f4','f5','f6','f7','f8'):
            self._on_menu_button_click(None, input)
            return True


    #
    # Widgets
    #
    def _init_widgets(self, asyncio_loop):
        """Initializes the widgets of the basic app framework.
        """
        # Header is Columns of menu Button widgets
        self.furp_button = SquareMenuButton(self, self._get_app_name())
        cols = len(self._get_app_name()) + 4
        self.header_columns = urwid.Columns([(cols, self.furp_button)])

        # Body
        self.body = urwid.Text("Press F1 to list available plugins")
        self.body_filler = urwid.Filler(self.body)

        # Footer's Status text
        self.status_text_callback_handle = None
        self.status_text = urwid.Text("Status")
        self.set_status_persistent("")
        self.set_status_temporary(self.get_app_data_path())

        # Footer is Status and DateTime widgets
        self.dt_text = urwid.Text(self._get_time_as_str())
        cols = self.dt_text.pack()[0]
        self.footer_columns = urwid.Columns([self.status_text, (cols, self.dt_text)])

        # Init date/time callback to happen on even time-multiples of the update rate
        # This is done so the datetime display updates simultaneously with the computer's clock
        now = asyncio_loop.time()
        remainder = now % Furp.CFG_DT_UPDT_RATE
        next = (now - remainder) + Furp.CFG_DT_UPDT_RATE
        asyncio_loop.call_at(next, self._update_dt, next, asyncio_loop, self.dt_text)

        self.top_level_widget = urwid.Frame(self.body_filler, header=self.header_columns, footer=self.footer_columns)


    def get_top_level_widget(self,):
        return self.top_level_widget


    def quit(self, *vararg):
        #TODO save state
        raise urwid.ExitMainLoop()


    # Placeholder
    def _on_menu_button_click(self, btn_widget, user_data):
        self.set_status_temporary("emit button " + user_data, 3.0)


    #
    # DateTime Text methods
    #
    def _get_time_as_str(self):
        try: s = time.strftime(Furp.CFG_DT_FORMAT)
        except: s = time.strftime(Furp.DFLT_DT_FORMAT)
        return s


    def _update_dt(self, *args):
        now, loop, dt_text = args
        next = now + Furp.CFG_DT_UPDT_RATE
        loop.call_at(next, self._update_dt, next, loop, dt_text)
        dt_text.set_text(self._get_time_as_str())


    #
    # Status Text methods
    #
    def set_status_persistent(self, text):
        self.status_text_persistent = text
        self.status_text.set_text(text)


    def set_status_temporary(self, text, duration=CFG_STATUS_TEMPORARY_DURATION):
        if self.status_text_callback_handle is not None:
            self.status_text_callback_handle.cancel()
            self.status_text_callback_handle = None
        self.status_text.set_text(text)
        next = aloop.time() + duration
        self.status_text_callback_handle = aloop.call_at(next, self._on_status_temporary_expiration)


    def _on_status_temporary_expiration(self,):
        self.status_text.set_text(self.status_text_persistent)
        self.status_text_callback_handle = None


    #
    # Path and Config
    #
    def get_app_data_path(self):
        """Returns the OS-specific path to Application Data for the given App

        NOTE: Darwin: https://developer.apple.com/reference/foundation/1414224-nssearchpathfordirectoriesindoma?language=objc
        """
        if sys.platform == 'darwin':
            from AppKit import NSSearchPathForDirectoriesInDomains, NSApplicationSupportDirectory, NSUserDomainMask
            app_data_path = os.path.join(NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, True)[0], self._get_app_name())
        elif sys.platform == 'win32':
            app_data_path = os.path.join(os.environ['APPDATA'], self._get_app_name())
        else:
            app_data_path = os.path.expanduser(os.path.join("~", "." + self._get_app_name()))

        if not os.path.exists(app_data_path):
            os.mkdir(app_data_path)

        return app_data_path


    #
    # Plugins
    #
    def activate_plugin(self, button):
        """Activates the plugin whose button was selected.
        """
        plug_info = self._plugins[button.get_label()]
        if plug_info['instance'] is None:
            plug_module = importlib.import_module(plug_info['name'])
            plug_info['instance'] = plug_module.new_instance(self)

        self.active_plugin = plug_info['instance']
        self.body_filler.original_widget = self.active_plugin.get_main_widget()
        # TODO: register button handler, etc.
        self.set_status_temporary("Activated %s" % plug_info['name'])


    def get_plugins(self):
        return self._plugins


    def _init_plugins(self,):
        """Inits the plugin cache--a dict of key=name, val={name, path, instance}
        """
        self._plugins = {}

        for path in [os.path.join(self.get_app_data_path(), "plugins"),
                     os.path.join(os.getcwd(), "plugins"), # FOR DEVELOPMENT ONLY
                    ]:
            if os.path.isdir(path):
                for path_item in os.listdir(path): # path_item is potentially a plugin's name
                    fullpath = os.path.join(path, path_item)
                    if os.path.isdir(fullpath):
                        if path_item + ".py" in os.listdir(fullpath):
                            if fullpath not in sys.path:
                                sys.path.append(fullpath)
                            self._plugins[path_item] = {'name':path_item,
                                                        'path':fullpath,
                                                        'instance':None}


if __name__ == "__main__":
    aloop = asyncio.get_event_loop()
    app = Furp(aloop)
    ualoop = urwid.AsyncioEventLoop(loop=aloop)
    umloop = urwid.MainLoop(
                app.get_top_level_widget(),
                event_loop=ualoop,
                palette=[("reversed", "standout", "")],
                pop_ups=True,
                unhandled_input=app._on_unhandled_input)
    umloop.run()
