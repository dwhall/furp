import plugin

import urwid # 1.3.1


class HelloName(plugin.PdataPlugin):
    """A demonstration of the persistent data plugin.
    """

    def __init__(self, framework):
        super().__init__(framework)
        self.framework = framework

        # Init pdata
        name = self.pdata.get("name", "Mr. Noname")
        self.pdata['name'] = name

        # Init widgets
        self.edit = urwid.Edit("Name: ", name)
        self.text = urwid.Text("Hello, " + self.pdata['name'])
        self.main_widget = urwid.Pile([self.edit, self.text])

        urwid.connect_signal(self.edit, "change", self.on_name_change)


    def on_name_change(self, widget, newtext):
        self.pdata['name'] = newtext
        self.text.set_text("Hello, " + newtext)


    def get_main_widget(self):
        return self.main_widget


def new_instance(framework):
    return HelloName(framework)
