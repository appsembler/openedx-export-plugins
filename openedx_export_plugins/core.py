"""
Core export functionality.
"""

import datetime
import io
import logging
import os
import shutil
import tarfile

from django.core.exceptions import PermissionDenied

from xmodule.contentstore.django import contentstore
from xmodule.exceptions import SerializationError
from xmodule.modulestore.django import modulestore

from student.auth import has_course_author_access

from . import exceptions


logger = logging.getLogger(__name__)


def export_course_single(user, plugin_class, tempdir, course_key):
    """
    Generate a single export file and return a path to it and its name.
    """
    if not has_course_author_access(user, course_key):
        raise PermissionDenied()

    (outfilepath, out_fn) = _do_course_export(plugin_class, tempdir, course_key)
    return (outfilepath, out_fn)


def export_courses_multiple(user, plugin_class, course_keys, tempdir, outfilename, stream=False, check_author_perms=True):
    """
    Build a tar file from multi-course export and either yield its bytes to stream
    or yield a finished gzipped tar file.
    """
    if not stream:
        outfilename += ".gz"

    tarf = os.path.join(tempdir, outfilename)
    write_method = "w:" if stream else "w:gz"
    with tarfile.open(tarf, write_method) as out_tar:
        for course_key in course_keys:
            if check_author_perms:
                if not has_course_author_access(user, course_key):
                    logger.warn('User {} has no access to export {}'.format(user, course_key))
                    continue
            try:
                if stream:
                    for tar_bytes in _course_tar_bytes(user, plugin_class, tempdir, course_key, out_tar):
                        yield tar_bytes
                else:
                    output_filepath, out_fn = _do_course_export(plugin_class, tempdir, course_key)
                    out_tar.add(output_filepath, out_fn)
            except exceptions.ExportPluginsCourseExportError:
                continue
        if stream:
            yield _get_tar_end_padding_bytes()
            shutil.rmtree(tempdir)  # clean up the temp files as they won't be otherwise when streaming
        else:
            yield out_tar


def _get_tar_end_padding_bytes():
    """tar files are finished with two blocks of zeros."""
    pad_data = io.BytesIO()
    pad_data.write(tarfile.NUL * (tarfile.BLOCKSIZE * 2))
    return pad_data.getvalue()


def _course_tar_bytes(user, plugin_class, tempdir, course_key, out_tar):
    """
    Generate tarball data from multiple course exports
    """

    def _get_tar_record_bytes(tarinfo, src_file_path):
        tar_header = tarinfo.tobuf(out_tar.format, out_tar.encoding, out_tar.errors)

        # replicating behavior of TarFile.add
        tar_data = io.BytesIO()
        with open(src_file_path, "rb") as src:
            shutil.copyfileobj(src, tar_data, length=tarinfo.size)
            blocks, remainder = divmod(tarinfo.size, tarfile.BLOCKSIZE)
            if remainder > 0:
                tar_data.write(tarfile.NUL * (tarfile.BLOCKSIZE - remainder))

        return (tar_header, tar_data.getvalue())

    (outfilepath, out_fn) = _do_course_export(plugin_class, tempdir, course_key)

    tarinfo = out_tar.gettarinfo(name=outfilepath, arcname=out_fn)
    (tar_hd, tar_data) = _get_tar_record_bytes(tarinfo, outfilepath)
    yield tar_hd
    yield tar_data


def _do_course_export(plugin_class, tempdir, course_key):
    """
    Run the actual export transformation.
    """
    # TODO: clean up the temporary directory if possible.
    # Since it needs to exist until we wrap and return the file for 
    # HTTP responses, not sure how to handle this
    course_key_normalized = str(course_key).replace('/', '+')
    target_dir = os.path.normpath(course_key_normalized)
    exporter = plugin_class(modulestore(), contentstore(), course_key, tempdir, target_dir)
    fn_ext = exporter.filename_extension
    try:
        exporter.export()
    except SerializationError as e:
        logger.warn('Could not export {} due to core OLX export error {}. Skipping.'.format(course_key, e.message))
        raise exceptions.ExportPluginsCourseExportError(e.message)

    output_filepath = os.path.join(tempdir, target_dir, "output.{}".format(fn_ext))
    out_fn = "{}_{}.{}".format(
        course_key_normalized,
        datetime.datetime.now().strftime('%Y-%m-%d'),
        fn_ext
    )
    return (output_filepath, out_fn)
