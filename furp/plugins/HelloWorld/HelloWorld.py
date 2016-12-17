import plugin

import urwid # 1.3.1


class HelloWorld(plugin.BasePlugin):
    """A simple demonstration plugin.
    """

    def __init__(self):
        super().__init__()
        self.main_widget = urwid.Text("Hello World!")


    def get_main_widget(self):
        return self.main_widget


def new_instance(framework):
    return HelloWorld()
