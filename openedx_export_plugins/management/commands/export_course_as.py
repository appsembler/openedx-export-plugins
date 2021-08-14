"""
A Django command that exports a course using an exporter plugin.

If <filename> is '-', it pipes the file to stdout.
"""

import os
import shutil
from tempfile import mkdtemp, mktemp
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.lib import plugins
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
        target_dir = os.path.normpath(course_id.replace('/', '+'))

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

        exporter = plugin_class(modulestore(), contentstore(), course_key, root_dir, target_dir)
        exporter.export()

        # read results from tmp output.md, write results to stdout or filename, if passed
        results = self._get_results(root_dir, target_dir, exporter)
        if filename:
            with open(filename, "w") as outfile:
                outfile.write(results)
        else:
            self.stdout.write(results, ending="")

    def _get_results(self, root_dir, target_dir, exporter):
        """Load results from file"""
        tmp_output_path = os.path.join(root_dir, target_dir, "output.{}".format(exporter.filename_extension))
        with open(tmp_output_path) as f:
            results = f.read()
        shutil.rmtree(root_dir)
        return results
