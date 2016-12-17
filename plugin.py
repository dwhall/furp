#!/usr/bin/env python3

"""plugin - base classes for plugins
"""

import os, shelve


class BasePlugin:
    """The most rudimentary plugin.
    """
    def get_main_widget(self):
        raise NotImplementedError("The plugin subclass MUST implement this method.")


class PdataPlugin(BasePlugin):
    """A plugin with a managed persistent data object.
    The persistent data object is implemented as a shelf with writeback=True.
    The framework calls the objects sync() method periodically
    and in the deconstructor so data is saved.

    The plugin author uses self.pdata like a dictionary.
    The keys of self.pdata must be strings.
    """
    def __init__(self, framework):
        super().__init__()
        self.framework = framework

        # Create/open the shelf file
        pdata_fn = self.__class__.__name__ + ".pdata"
        pdata_path = os.path.join(framework.get_app_data_path(), pdata_fn)
        self.pdata = shelve.open(pdata_path, writeback=True)


    def sync_pdata(self):
        self.pdata.sync()


    def __del__(self):
        self.pdata.close()
