"""
A Django command that exports a course using an exporter plugin.

If <filename> is '-', it pipes the file to stdout.
"""

import os
from tempfile import mkdtemp, mktemp
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.lib.api import plugins
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore


from openedx_export_plugins.plugins import CourseExporterPluginManager


class Command(BaseCommand):
    """
    Export a course to a format provided by a CourseExportManager subclass plugin.
    The output format is determined by the plugin.
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument('plugin')
        parser.add_argument('course_id')
        parser.add_argument('--output', default=None)

    def handle(self, *args, **options):

        root_dir = mkdtemp()

        course_id = options['course_id']
        target_dir = os.path.normpath(course_id)

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise CommandError("Unparsable course_id")
        except IndexError:
            raise CommandError("Insufficient arguments")

        plugin_name = options['plugin']
        try:
            plugin_class = CourseExporterPluginManager.get_plugin(plugin_name)
        except plugins.PluginError:
            self.stderr.write("Course export plugin with the name {} not found".format(plugin_name))

        filename = options['output']
        pipe_results = False
        if filename is None:
            filename = mktemp()
            pipe_results = True

        exporter = plugin_class(modulestore(), contentstore(), course_key, root_dir, target_dir)
        exporter.export()

        results = self._get_results(filename) if pipe_results else None

        self.stdout.write(results, ending="")

    def _get_results(self, filename):
        """Load results from file"""
        with open(filename) as f:
            results = f.read()
            os.remove(filename)
        return results
