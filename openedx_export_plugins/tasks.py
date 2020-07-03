"""
Provide Celery tasks for export jobs.
"""
import datetime
import os

from celery.task import task

from xmodule.modulestore.django import modulestore

from . import app_settings, constants, core, storage
from .plugins import CourseExporterPluginManager


@task
def export_all_courses(plugin):
    """
    Save a gzipped (by default) tar file of all course exports.
    """
    plugin_class = CourseExporterPluginManager.get_plugin(plugin)
    store = modulestore()
    course_keys = [course.id for course in store.get_courses()]

    if not app_settings.COURSE_EXPORT_SINGLE_STORAGE_FILE:
        outfilename = constants.EXPORT_FILENAME_FORMAT_MULTIPLE.format(
            plugin_class.filename_extension,
            datetime.datetime.now().strftime('%Y-%m-%d')
        )
    else:
        outfilename = constants.EXPORT_FILENAME_FORMAT_MULTIPLE_NO_DATE.format(
                plugin_class.filename_extension
        )

    tarf = core.export_courses_multiple(
        None, plugin_class, course_keys, outfilename, check_author_perms=False
    ).next()

    if app_settings.COURSE_EXPORT_STORAGE_TYPE == 's3':
        bucketname = app_settings.COURSE_EXPORT_BUCKET
        fn = os.path.basename(tarf.name)
        storage_location = '{}/{}'.format(plugin_class.name, fn)
        storage.do_store_s3(tarf.name, storage_location, bucketname)
    # TODO: handle other storage types

    # delete the temp file
    if os.path.exists(tarf.name):
        os.remove(tarf.name)
