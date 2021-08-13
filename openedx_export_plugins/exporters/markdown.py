"""
Markdown format exporter for Open edX course content.
Targeted Markdown variant is Pandoc's extended Markdown
https://pandoc.org/MANUAL.html#pandocs-markdown
"""

import datetime
import json
import os

from lxml import etree

from .. import app_settings
from . import base, resolvers


class MarkdownCourseExportManager(base.PluggableCourseExportManager):
    """
    Manages export of course objects to the Markdown format.
    """

    # TODO: allow for alternative xsl via ConfigurationModel storage
    with open(os.path.join(os.path.dirname(__file__), 'xsl', 'md_single_doc.xsl'), 'r') as xslf:
        DEFAULT_XSL_STYLESHEET = xslf.read()

    name = "markdown"
    http_content_type = "text/markdown"
    filename_extension = "md"

    def post_process(self, root, export_fs):
        """
        Perform final processing of outputted XML structure to Markdown
        via XSLT.
        """
        self._build_markdown_document(root, export_fs)

    def _build_markdown_document(self, root, export_fs):
        transformed = self._do_xsl_transform(root, export_fs)
        output_path = export_fs.getsyspath("output.md")
        transformed.write(output_path, encoding="utf-8", method="text")

    def _do_xsl_transform(self, root, export_fs):
        """
        Perform XSLT transform of export output using XSL stylesheet.
        """
        parser = etree.XMLParser(recover=True)  # use a forgiving parser, OLX is messy
        parser.resolvers.add(resolvers.ExportFSResolver(export_fs))
        parser.resolvers.add(resolvers.PyLocalXSLResolver())
        parser.resolvers.add(ExportFSAssetsFileResolver(export_fs))
        parser.resolvers.add(resolvers.ExportFSPolicyTabsJSONResolver(export_fs))
        parser.resolvers.add(resolvers.AssetURLResolver(export_fs))
        parser.resolvers.add(resolvers.ExportFSUpdatesJSONResolver(export_fs))

        xsl_sheet = self._load_export_xsl()
        xslt_root = etree.XML(xsl_sheet, parser)
        transform = etree.XSLT(xslt_root)
        dt = datetime.datetime.now()
        course_id = export_fs.sub_dir.replace('/', '')
        result_tree = transform(
            root, baseURL="'{}/'".format(app_settings.LMS_ROOT_URL),
            curDateTime="'{}'".format(dt), courseID="'{}'".format(course_id)
        )
        # print(str(result_tree))
        return result_tree


class ExportFSAssetsFileResolver(resolvers.ExportFSResolver):
    """
    Resolve assets.json file using custom parsing
    """
    def resolve(self, url, id, context):
        # print("Resolving assets URL {}".format(url))
        if not url.startswith('assets:'):
            return None   # move on to next Resolver

        def asset_object_hook(obj):
            TYPE_LOOKUP = {
                'image/png': 'Images',
                'image/jpeg': 'Images',
                'image/gif': 'Images',
                'application/pdf': 'Documents',
                'application/javascript': 'Code',
                'text/html': 'Code',
                'text/css': 'Code',
            }
            if 'contentType' in obj:
                try:
                    supertype = TYPE_LOOKUP[obj['contentType']]
                except KeyError:
                    supertype = 'Other'
                return dict(supertype=supertype, name=obj['displayname'])
            else:
                return obj

        def sorted_by_type(assets):
            new_dict = dict(Images=[], Documents=[], Code=[], Other=[])

            for key, val in assets.items():
                new_dict[val['supertype']].append(val['name'])

            ret_str = ""
            # TODO: this resolver doesn't have to be markdown-specific
            # if we can make the return string more generic
            for key in new_dict:
                ret_str += "\n\n#### {}\n* ".format(key)
                ret_str += "\n* ".join(sorted(new_dict[key]))
            return ret_str

        path = self.fs.getsyspath(url.replace('assets:', '', 1))
        if os.path.exists(path):
            with open(path) as f:
                assets = json.load(f, object_hook=asset_object_hook)
                assets_str = sorted_by_type(assets)
                return self.resolve_string("<xml><![CDATA[{}]]></xml>".format(assets_str), context)
        else:
            return self.resolve_empty(context)
