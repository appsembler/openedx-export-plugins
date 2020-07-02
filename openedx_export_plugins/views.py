"""
Views for export plugins.
"""

import datetime
import logging
import os

from django.contrib.auth.decorators import login_required
try:
    # removed in Django 1.9
    from django.core.servers.basehttp import FileWrapper
except ImportError:
    from wsgiref.util import FileWrapper
from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from xmodule.modulestore.django import modulestore

from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api import plugins
from util.views import ensure_valid_course_key

from . import core
from .plugins import CourseExporterPluginManager


logger = logging.getLogger(__name__)


@ensure_csrf_cookie
@login_required
@require_http_methods(("GET",))
@ensure_valid_course_key
def plugin_export_handler(request, plugin_name, course_key_string=None):
    """
    The restful handler for exporting a course, or all courses, with an exporter plugin.
    Passing no course key string will export all courses to which the user has access
    """
    store = modulestore()
    try:
        plugin_class = CourseExporterPluginManager.get_plugin(plugin_name)
        plugin_ctype = plugin_class.http_content_type
    except plugins.PluginError:
        raise Http404

    if course_key_string:
        course_keys = (CourseKey.from_string(course_key_string),)
        courselike_module = store.get_course(course_keys[0])
        if courselike_module is None:
            raise Http404  # this should only ever happen if a course_key_string is passed
    else:
        courses = store.get_courses()
        course_keys = [course.id for course in courses]

    if len(course_keys) == 1:
        (outfilepath, outfn) = core.export_course_single(request.user, plugin_class, course_keys[0])
        with open(outfilepath) as outfile:
            wrapper = FileWrapper(outfile)
            response = HttpResponse(wrapper, content_type='{}; charset=UTF-8'.format(plugin_ctype))
            response['Content-Disposition'] = 'attachment; filename={}'.format(outfn)
            response['Content-Length'] = os.path.getsize(outfilepath)
            return response
    else:
        # if exporting all files, stream the response back to avoid proxy timeout at front-end webserver
        # return a tarball of all export files in the response
        outfilename = constants.EXPORT_FILENAME_FORMAT_MULTIPLE.format(
            plugin_class.filename_extension,
            datetime.datetime.now().strftime('%Y-%m-%d'),
            ''
        )
        response = StreamingHttpResponse(
            core.export_courses_multiple(request.user, plugin_class, course_keys, outfilename, stream=True),
            content_type='application/tar'
        )
        response['Content-Disposition'] = 'attachment; filename={}'.format(outfilename)
        return response
