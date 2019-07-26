"""
Views for export plugins.
"""

import datetime
import logging
import os
from tempfile import mkdtemp
import zipfile

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from wsgiref.util import FileWrapper

from xmodule.contentstore.django import contentstore
from xmodule.exceptions import SerializationError
from xmodule.modulestore.django import modulestore

from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api import plugins
from student.auth import has_course_author_access
from util.views import ensure_valid_course_key

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
    except plugins.PluginError:
        raise Http404

    if course_key_string:
        course_keys = (CourseKey.from_string(course_key_string),)
    else:
        courses = store.get_courses()
        course_keys = [course.id for course in courses]

    outfiles = []
    response_fns = []

    for course_key in course_keys:
        if not has_course_author_access(request.user, course_key):
            if len(course_keys) == 1:
                raise PermissionDenied()
            else:
                logger.warn('User {} has no access to export {}'.format(request.user, course_key))
                continue

        courselike_module = store.get_course(course_key)
        if courselike_module is None:
            raise Http404  # this should only ever happen if a course_key_string is passed

        root_dir = mkdtemp()
        course_key_normalized = str(course_key).replace('/', '+')
        target_dir = os.path.normpath(course_key_normalized)
        exporter = plugin_class(modulestore(), contentstore(), course_key, root_dir, target_dir)
        try:
            exporter.export()
        except SerializationError as e:
            if len(course_keys == 1):
                raise
            else:
                logger.warn('Could not export {} due to core OLX export error {}. Skipping.'.format(course_key, e.message))
                continue

        fn_ext = exporter.filename_extension
        output_filepath = os.path.join(root_dir, target_dir, "output.{}".format(fn_ext))
        outfiles.append(output_filepath)
        response_fn = "{}_{}.{}".format(
            course_key_normalized,
            datetime.datetime.now().strftime('%Y-%m-%d'),
            fn_ext
        )
        response_fns.append(response_fn)

    response_files = list(zip(outfiles, response_fns))

    if len(response_files) == 1:
        # return a single export file in the response
        with open(response_files[0][0]) as outfile:
            response_fn = response_files[0][1]
            wrapper = FileWrapper(outfile)
            response = HttpResponse(wrapper, content_type='text/markdown; charset=UTF-8')
            response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(response_fn.encode('utf-8')))
            response['Content-Length'] = os.path.getsize(outfile.name)
            return response
    else:
        # return a zip archive of all export files in the response
        zipfn = 'all_courses_as_{}_{}.zip'.format(fn_ext, datetime.datetime.now().strftime('%Y-%m-%d'))
        with zipfile.ZipFile(zipfn, 'w') as response_zip:
            for file in response_files:
                response_zip.write(filename=file[0], arcname=file[1])
        with open(zipfn, 'r') as response_zip:
            wrapper = FileWrapper(response_zip)
            response = HttpResponse(wrapper, content_type='application/zip; charset=UTF-8')
            response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(zipfn.encode('utf-8')))
            response['Content-Length'] = os.path.getsize(zipfn)
            return response
