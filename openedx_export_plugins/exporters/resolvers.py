"""
XML Resolvers for lxml.etree
"""

import os

from lxml import etree


class PyLocalXSLResolver(etree.Resolver):
    """
    Resolve URL lookups relative to this Python module directory.
    """
    def resolve(self, url, id, context):
        if not url.startswith('pylocal:'):
            return None   # move on to next Resolver

        path = os.path.join(os.path.dirname(__file__), 'xsl', url.replace('pylocal:', ''))
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

        path = self.fs.getsyspath(url.replace('tmpfs:', '', 1))
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
