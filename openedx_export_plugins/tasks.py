"""
Provide Celery tasks for export jobs.
"""

import datetime
import logging
import os

from celery.decorators import periodic_task
from celery.schedules import crontab

from django.core.mail import EmailMessage

from xmodule.modulestore.django import modulestore

from . import app_settings, constants, core, exceptions, storage, utils
from .plugins import CourseExporterPluginManager


QUEUE = app_settings.COURSE_EXPORT_PLUGIN_TASK_QUEUE

logger = logging.getLogger(__name__)


def _notify_error(plugin, error):
    dest_addrs = app_settings.COURSE_EXPORT_PLUGIN_TASK_NOTIFY_ON_ERROR
    if not dest_addrs:
        return
    subject = "Open edX course export as {} failed".format(plugin)
    errmsg = error.message or getattr(error, "strerror")
    message = "Course export as {} from {} failed with error: {}".format(
        plugin, app_settings.LMS_ROOT_URL, errmsg
    )
    mail = EmailMessage(subject, message, to=dest_addrs)
    mail.send()
    raise error


@periodic_task(
    run_every=crontab(**app_settings.COURSE_EXPORT_PLUGIN_TASK_SCHEDULE),
    queue=QUEUE,
    options={'queue': QUEUE}
)
def export_all_courses():
    for plugin in app_settings.COURSE_EXPORT_PLUGIN_SCHEDULED_PLUGINS:
        try:
            export_all_courses_as(plugin)
        except exceptions.ExportPluginsCourseExportError as e:
            # any single course not exporting shouldn't cause whole job to quit
            logger.warning(e.msg)
        # notify recipients by email of any other uncaught error, then continue
        except Exception as e:
            _notify_error(plugin, e)


def export_all_courses_as(plugin):
    """
    Save a gzipped (by default) tar file of all course exports.
    """
    plugin_class = CourseExporterPluginManager.get_plugin(plugin)
    store = modulestore()
    course_keys = [course.id for course in store.get_courses()]

    if not app_settings.COURSE_EXPORT_PLUGIN_STORAGE_OVERWRITE:
        outfilename = constants.EXPORT_FILENAME_FORMAT_MULTIPLE.format(
            plugin_class.filename_extension,
            datetime.datetime.now().strftime('%Y-%m-%d')
        )
    else:
        outfilename = constants.EXPORT_FILENAME_FORMAT_MULTIPLE_NO_DATE.format(
            plugin_class.filename_extension
        )

    with utils.TemporaryDirectory() as tempdir:
        tarf = next(core.export_courses_multiple(
            None, plugin_class, course_keys, tempdir, outfilename, check_author_perms=False
        ))

        if app_settings.COURSE_EXPORT_PLUGIN_STORAGE_TYPE == 's3':
            fn = os.path.basename(tarf.name)
            storage_path = '{}/{}'.format(plugin_class.name, fn)
            storage.do_store_s3(tarf.name, storage_path)
        # TODO: handle other storage types
