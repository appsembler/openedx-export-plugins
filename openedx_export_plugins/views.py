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
from django.http import FileResponse, HttpResponse, Http404
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


def _export_course_single(user, plugin_class, course_key):
    """
    Generate a single export file to return.
    """
    if not has_course_author_access(user, course_key):
            raise PermissionDenied()

    try:
        (outfilepath, response_fn) = _do_course_export(user, plugin_class, course_key)
    except SerializationError:
        raise  # TODO: maybe do something better here

    # return a single export file in the response
    with open(outfilepath) as outfile:
        wrapper = FileWrapper(outfile)
        response = HttpResponse(wrapper, content_type='text/markdown; charset=UTF-8')
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(response_fn.encode('utf-8')))
        response['Content-Length'] = os.path.getsize(outfile.name)
        return response


def _export_courses_multiple(user, plugin_class, course_keys, response_zip):
    """
    Generate a Zip file with multiple course exports
    """
    # immediately yield some bytes to keep the HTTPStreaming connection open
    # yield " " * 1024

    for course_key in course_keys:
        if not has_course_author_access(user, course_key):
            logger.warn('User {} has no access to export {}'.format(user, course_key))
            continue

        try:
            (outfilepath, response_fn) = _do_course_export(user, plugin_class, course_key)
            response_zip.write(filename=outfilepath, arcname=response_fn)
        except SerializationError as e:
            logger.warn('Could not export {} due to core OLX export error {}. Skipping.'.format(course_key, e.message))
            continue

    zipfn = response_zip.fp.name
    response_zip.close()
    with open(zipfn) as zipf:
        yield zipf.read()


def _do_course_export(user, plugin_class, course_key):
    """
    Run the actual export transformation.
    """
    root_dir = mkdtemp()
    course_key_normalized = str(course_key).replace('/', '+')
    target_dir = os.path.normpath(course_key_normalized)
    exporter = plugin_class(modulestore(), contentstore(), course_key, root_dir, target_dir)
    fn_ext = exporter.filename_extension
    exporter.export()

    output_filepath = os.path.join(root_dir, target_dir, "output.{}".format(fn_ext))
    response_fn = "{}_{}.{}".format(
        course_key_normalized,
        datetime.datetime.now().strftime('%Y-%m-%d'),
        fn_ext
    )
    return (output_filepath, response_fn)


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
        courselike_module = store.get_course(course_keys[0])
        if courselike_module is None:
            raise Http404  # this should only ever happen if a course_key_string is passed
    else:
        courses = store.get_courses()
        course_keys = [course.id for course in courses]

    if len(course_keys) == 1:
        return _export_course_single(request.user, plugin_class, course_keys[0])
    else:
        # TODO: really we should pass this off to Celery and make a view to list and download the ...
        # completed file simliar to Instructor dashboard.  This is a shortcut until then.
        # if exporting all files, stream the response back to avoid proxy timeout at front-end webserver
        # return a zip archive of all export files in the response
        exporter = plugin_class(modulestore(), contentstore(), course_keys[0], "/tmp", "")  # just to get extension
        zipfn = os.path.join(mkdtemp(), 'all_courses_as_{}_{}.zip'.format(exporter.filename_extension, datetime.datetime.now().strftime('%Y-%m-%d')))
        response_zip = zipfile.ZipFile(zipfn, 'w')
        response = FileResponse(_export_courses_multiple(request.user, plugin_class, course_keys, response_zip), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(zipfn.encode('utf-8')))
        return response
