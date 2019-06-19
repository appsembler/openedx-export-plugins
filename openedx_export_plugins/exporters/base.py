"""
Define an Exporter Plugin class providing
additional options to xmodule lib ExportManager
"""

import os

from lxml import etree

from xmodule.modulestore import xml_exporter


class PluggableCourseExportManager(xml_exporter.CourseExportManager):
    """
    Export format-agnostic block/module course export manager.
    Course export plugins should register themselves in the namespace
    `openedx.exporters.course` and inherit from this class.
    """

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
        parser.resolvers.add(ExportFSResolver(export_fs))
        parser.resolvers.add(PyLocalXSLResolver())
        xsl_sheet = self._load_export_xsl()
        xslt_root = etree.XML(xsl_sheet, parser)
        transform = etree.XSLT(xslt_root)
        result_tree = transform(root)
        print(str(result_tree))
        return result_tree


class PyLocalXSLResolver(etree.Resolver):
    """
    Resolve URL lookups relative to this Python module directory.
    """
    def resolve(self, url, id, context):
        if not url.startswith('pylocal:'):
            return None   # move on to next Resolver

        path = os.path.join(os.path.dirname(__file__), 'xsl', url.replace('pylocal:',''))        
        if os.path.exists(path):
            return self.resolve_filename(path, context)
        else:
            print ("can't resolve url {}. returning empty document".format(url))
            return self.resolve_empty(context)


class ExportFSResolver(etree.Resolver):
    """
    Resolve xsl:document() URL lookups to local tempory FS files
    """
    def __init__(self, fs):
        self.fs = fs
        super(ExportFSResolver, self).__init__()

    def resolve(self, url, id, context):
        print("Resolving URL {}".format(url))
        if not url.startswith('tmpfs:'):
            return None   # move on to next Resolver

        path = self.fs.getsyspath(url.replace('tmpfs:','',1))
        if os.path.exists(path):
            # TODO: maybe move this into some error handling code
            try:
                if '.html' in path:
                    # we have to turn it into proper XHTML
                    # mostly they are invalid fragments without enclosing <html>
                    with open(path) as f:
                        contents = f.read()
                        html_tree = etree.HTML(contents)
                        return self.resolve_string(etree.tostring(html_tree), context)
                else:
                        etree.parse(path)  # validate parseability
                        return self.resolve_filename(path, context)
            except etree.ParseError as e:
                print("Refusing to load a malformed document {} with error {}.  Returning empty document".format(url, e.message))
                return self.resolve_empty(context)
        else:
            print ("can't resolve url {}. returning empty document".format(url))
            return self.resolve_empty(context)
