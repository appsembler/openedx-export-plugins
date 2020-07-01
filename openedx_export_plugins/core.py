"""
Core export functionality.
"""

import datetime
import io
import os
from tempfile import mkdtemp
import shutil
import tarfile

from django.core.exceptions import PermissionDenied

from xmodule.contentstore.django import contentstore
from xmodule.exceptions import SerializationError
from xmodule.modulestore.django import modulestore

from student.auth import has_course_author_access


def export_course_single(user, plugin_class, course_key):
    """
    Generate a single export file and return a path to it and its name.
    """
    if not has_course_author_access(user, course_key):
        raise PermissionDenied()

    try:
        (outfilepath, out_fn) = _do_course_export(user, plugin_class, course_key)
    except SerializationError:
        raise  # TODO: maybe do something better here

    # return a single export file in the response
    return (outfilepath, out_fn)

def export_courses_multiple(user, plugin_class, course_keys, outfilename, stream=False):
    """
    Build a tar file from multi-course export and either yield its bytes to stream 
    or return a finished gzipped tar file.
    """
    tarf = os.path.join(mkdtemp(), outfilename)
    with tarfile.open(tarf, "w:") as out_tar:
        for tar_bytes in courses_tar_bytes(user, plugin_class, course_keys, out_tar):
            if stream:
                yield tar_bytes            
            else:
                out_tar.write(tar_bytes)
        if not stream:
            yield out_tar


def courses_tar_bytes(user, plugin_class, course_keys, out_tar):
    """
    Generate tarball data from multiple course exports
    """

    def _get_tar_record_bytes(tarinfo, src_file_path):
        tar_header = tarinfo.tobuf(out_tar.format, out_tar.encoding, out_tar.errors)

        # replicating behavior of TarFile.add
        tar_data = io.BytesIO()
        with open(src_file_path, "r") as src:
            shutil.copyfileobj(src, tar_data, length=tarinfo.size)
            blocks, remainder = divmod(tarinfo.size, tarfile.BLOCKSIZE)
            if remainder > 0:
                tar_data.write(tarfile.NUL * (tarfile.BLOCKSIZE - remainder))

        return (tar_header, tar_data.getvalue())

    def _get_tar_end_padding_bytes():
        """tar files are finished with two blocks of zeros."""
        pad_data = io.BytesIO()
        pad_data.write(tarfile.NUL * (tarfile.BLOCKSIZE * 2))
        return pad_data.getvalue()

    for course_key in course_keys:
        if not has_course_author_access(user, course_key):
            logger.warn('User {} has no access to export {}'.format(user, course_key))
            continue
        try:
            (outfilepath, out_fn) = _do_course_export(user, plugin_class, course_key)

            # yield tar format data bit by bit,...
            tarinfo = out_tar.gettarinfo(name=outfilepath, arcname=out_fn)
            (tar_hd, tar_data) = _get_tar_record_bytes(tarinfo, outfilepath)
            yield tar_hd
            yield tar_data

        except SerializationError as e:
            logger.warn('Could not export {} due to core OLX export error {}. Skipping.'.format(course_key, e.message))
            continue

    # ...now add the padding to mark the end of the tarfile
    yield _get_tar_end_padding_bytes()


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
    out_fn = "{}_{}.{}".format(
        course_key_normalized,
        datetime.datetime.now().strftime('%Y-%m-%d'),
        fn_ext
    )
    return (output_filepath, out_fn)
