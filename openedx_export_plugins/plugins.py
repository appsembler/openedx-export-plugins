"""
Plugins for course, library, and block export
"""
from openedx.core.lib.plugins import PluginManager


# Stevedore extension point namespaces
COURSE_EXPORTER_NAMESPACE = 'openedx.exporters.course'


class CourseExporterPluginManager(PluginManager):
    """
    Manager for all of the course exporters/formats that have been made available.

    All exporters should implement `CourseExporter`.
    """
    NAMESPACE = COURSE_EXPORTER_NAMESPACE
