"""
Markdown format exporter for Open edX course content
"""

from lxml import etree
import json
import os

from . import base


class MarkdownCourseExportManager(base.PluggableCourseExportManager):
    """
    Manages export of course objects to the Markdown format.
    """

    # TODO: allow for alternative xsl via ConfigurationModel storage
    with open(os.path.join(os.path.dirname(__file__), 'xsl', 'md_single_doc.xsl'), 'r') as xslf:
        DEFAULT_XSL_STYLESHEET = xslf.read()

    def post_process(self, root, export_fs):
        """
        Perform final processing of outputted XML structure to Markdown
        via XSLT
        """
        self._build_markdown_document(root, export_fs)

        # start with course/{}.xml value contained from course.xml://course/@url_name
        # from there get the correct course/coursefoo.xml file
        # build out main headings from course display name, info from about/ files
        # then iterate over chapters in coursefoo.xml, in sequence
        # process each chapter
        # output display name
        #   iterate over sequentials
        #   output display name
        #   iterate over verticals
        #   get correct verical type (html, video, problem, etc.)
        # process assets - policies/assets.json (make a list at end of course, w/ storage url)
        # process updates - info/updates.html (HTML contents)
        # process handouts - info/handouts.html (HTML contents)

        # we get an output like this:
        """
        (Pdb) export_fs.listdir()
        [u'sequential', u'policies', u'assets', u'drafts', u'about', u'chapter', u'course.xml', u'course']
        (Pdb) export_fs.tree()
        |-- about
        |   `-- overview.html
        |-- assets
        |   `-- assets.xml
        |-- chapter
        |   `-- cbeaa9eb48f840dd87fa51454f35c1e6.xml
        |-- course
        |   `-- course.xml
        |-- course.xml
        |-- drafts
        |   `-- vertical
        |       `-- df56f0af0131468b99e9fea02f8ae8a1.xml
        |-- policies
        |   |-- assets.json
        |   `-- course
        |       |-- grading_policy.json
        |       `-- policy.json
        `-- sequential
            `-- 16eb45a39bb64c1bab1651a9028d508c.xml
        """
        # we want to put together a single Markdown file from...
        # course.xml: org, name, run
        # course/(id).xml
        #  display_name
        #  sequencing of chapters (`chapter/@url_name`)
        # about/short_description.html: (text short description)
        # about/overview.html:
        #  `section.about`: html content
        #  `section.prerequisities`: html content
        #  `section.course-staff`: html content `article.teacher`
        #  `section.faq`: html content  `article.response`
        # chapter/foo.xml:
        #   `chapter/@display_name
        #   order of sequentials, ids:`chapter/sequential/@url_name
        # sequential/foo.xml
        #   `sequential/@display_name
        #  order of verticals, ids: `sequential/vertical/@url_name`
        # verticals are of different types (html, problem, video, ...)

        # there are these types of things that need to be converted to Markdown
        #   XML
        #   JSON
        #   HTML
        #   plain text (short description)

        # there are common functions that need to happen
        #   traverse folder structure from path in XML
        #   output full static URL
        #   strip HTML tags
        #

    def _build_markdown_document(self, root, export_fs):
        transformed = self._do_xsl_transform(root, export_fs)
        output_path = export_fs.getsyspath("output.md")
        # TODO: need to them transform JSON to markdown
        transformed.write(output_path, encoding="utf-8", method="text")
        # TODO: need to return something here

    def _do_xsl_transform(self, root, export_fs):
        """
        Perform XSLT transform of export output using XSL stylesheet.
        """
        parser = etree.XMLParser(recover=True)  # use a forgiving parser, OLX is messy
        parser.resolvers.add(base.ExportFSResolver(export_fs))
        parser.resolvers.add(base.PyLocalXSLResolver())
        parser.resolvers.add(ExportFSAssetsFileResolver(export_fs))
        xsl_sheet = self._load_export_xsl()
        xslt_root = etree.XML(xsl_sheet, parser)
        transform = etree.XSLT(xslt_root)
        result_tree = transform(root)
        print(str(result_tree))
        return result_tree


class ExportFSAssetsFileResolver(base.ExportFSResolver):
    """
    Resolve assets.json file using custom parsing
    """
    def resolve(self, url, id, context):
        print("Resolving assets URL {}".format(url))
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
            if 'contentType' in obj.keys():
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
            for key in new_dict.keys():
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
