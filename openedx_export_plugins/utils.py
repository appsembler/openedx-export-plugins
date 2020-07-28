"""
Utility classes and functions for openedx_export_plugins Django app.
"""

import contextlib
import shutil
import tempfile


# replicate Python 3.2+'s tempfile.TemporaryDirectory for now
@contextlib.contextmanager
def TemporaryDirectory(delete=True):
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        if delete:
            shutil.rmtree(temp_dir)
