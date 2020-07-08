Change Log
----------

..
   All enhancements and patches to openedx_export_plugins will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).
   
   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
~~~~~~~~~~

*

[0.2.0] - 2020-07-08
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* Periodic Celery task to export all courses on schedule with plugins and schedule as configured.
* Email notification of errors with task, if configured.

Changed
_______

* Refactor core export code to not require a Request object


[0.1.0] - 2019-06-05
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* First release.
* Markdown exporter plugin.
