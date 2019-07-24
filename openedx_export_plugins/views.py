import datetime
import os
import shutil
from tempfile import mkdtemp

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api import plugins
from student.auth import has_course_author_access
from util.views import ensure_valid_course_key

from .plugins import CourseExporterPluginManager


@ensure_csrf_cookie
@login_required
@require_http_methods(("GET",))
@ensure_valid_course_key
def plugin_export_handler(request, course_key_string, plugin_name):
    """
    The restful handler for exporting a course with an exporter plugin.
    """
    course_key = CourseKey.from_string(course_key_string)

    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    courselike_module = modulestore().get_course(course_key)
    if courselike_module is None:
        raise Http404

    try:
        plugin_class = CourseExporterPluginManager.get_plugin(plugin_name)
    except plugins.PluginError:
        raise HttpResponse(status=406)

    root_dir = mkdtemp()
    target_dir = os.path.normpath(course_key_string.replace('/', '+'))
    exporter = plugin_class(modulestore(), contentstore(), course_key, root_dir, target_dir)
    exporter.export()

    fn_ext = exporter.filename_extension
    output_filepath = os.path.join(root_dir, target_dir, "output.{}".format(fn_ext))
    response_fn = "{}_{}.{}".format(
        course_key_string,
        str(datetime.datetime.now()),
        fn_ext
    )

    with open(output_filepath) as outfile:
        wrapper = FileWrapper(outfile)
        response = HttpResponse(wrapper, content_type='text/markdown; charset=UTF-8')
        response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(response_fn.encode('utf-8'))
        response['Content-Length'] = os.path.getsize(outfile.name)
        return response
