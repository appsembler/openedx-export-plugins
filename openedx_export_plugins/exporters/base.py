"""
Define an Exporter Plugin class providing
additional options to xmodule lib ExportManager
"""
import datetime

from lxml import etree

from xmodule.modulestore import xml_exporter

from .. import app_settings
from . import resolvers


class PluggableCourseExportManager(xml_exporter.CourseExportManager):
    """
    Export format-agnostic block/module course export manager.
    Course export plugins should register themselves in the namespace
    `openedx.exporters.course` and inherit from this class.
    """

    @property
    def name(self):
        raise NotImplementedError

    @property
    def http_content_type(self):
        raise NotImplementedError

    @property
    def filename_extension(self):
        raise NotImplementedError

    def process_root(self, root, export_fs):
        """
        Perform any additional tasks to the root node.
        """
        super(PluggableCourseExportManager, self).process_root(root, export_fs)

    def process_extra(self, root, courselike, root_courselike_dir, xml_centric_courselike_key, export_fs):
        """
        Process additional content, like static assets.
        """
        super(PluggableCourseExportManager, self).process_extra(root, courselike, root_courselike_dir, xml_centric_courselike_key, export_fs)

    def post_process(self, root, export_fs):
        """
        Perform any final processing after the other export tasks are done.

        This is where most plugin export managers will do their work, after
        export to XML.  XModules and XBlocks provide XML serialization directly
        or via mixin, and it's much more work to directly serialize to some other
        format than to post-process XML output to another format
        """

    def export(self):
        """
        Perform the export given the parameters handed to this class at init.
        """
        super(PluggableCourseExportManager, self).export()

    def _load_export_xsl(self):
        """
        Get the XSL stylesheet for post_processing.
        """
        try:
            return self.DEFAULT_XSL_STYLESHEET
        except AttributeError:
            raise  # do something more intelligent here, not all exporter plugins may use XSL

    def _do_xsl_transform(self, root, export_fs):
        """
        Perform XSLT transform of export output using XSL stylesheet.
        """
        parser = etree.XMLParser(recover=True)  # use a forgiving parser, OLX is messy
        parser.resolvers.add(resolvers.ExportFSResolver(export_fs))
        parser.resolvers.add(resolvers.PyLocalXSLResolver())
        parser.resolvers.add(resolvers.AssetURLResolver(export_fs))
        xsl_sheet = bytes(self._load_export_xsl(), 'utf-8')
        xslt_root = etree.XML(xsl_sheet, parser)
        transform = etree.XSLT(xslt_root)
        dt = datetime.datetime.now()
        result_tree = transform(root, baseURL="'{}'".format(app_settings.LMS_ROOT_URL), curDateTime="'{}'".format(dt))
        print((str(result_tree)))
        return result_tree
