"""
XML Resolvers for lxml.etree
"""

import json
import os

from lxml import etree

from django.utils.translation import ugettext as _

from xmodule.contentstore.content import StaticContent


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
            # print ("can't resolve url {}. returning empty document".format(url))
            return self.resolve_empty(context)


class ExportFSResolver(etree.Resolver):
    """
    Resolve xsl:document() URL lookups to local tempory FS files
    """
    def __init__(self, fs):
        self.fs = fs
        super(ExportFSResolver, self).__init__()

    def resolve(self, url, id, context):
        # print("Resolving URL {}".format(url))
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
                        if html_tree is not None:
                            return self.resolve_string(etree.tostring(html_tree), context)
                        else:
                            return self.resolve_empty(context)
                else:
                        etree.parse(path)  # validate parseability
                        return self.resolve_filename(path, context)
            except etree.ParseError as e:
                # print("Refusing to load a malformed document {} with error {}.  Returning empty document".format(url, e.message))
                return self.resolve_empty(context)
        else:
            # component nodes will have url_names even if all information is stored as attributes
            # on the node so this resolver will not find a matching file
            return self.resolve_empty(context)


class ExportFSPolicyTabsJSONResolver(ExportFSResolver):
    """
    Resolve tabs from url_slug value in policies/course/policy.json file using custom parsing
    """
    def resolve(self, url, id, context):
        if not url.startswith('tabs:'):
            return None   # move on to next Resolver

        path = self.fs.getsyspath(url.replace('tabs:', '', 1))

        if os.path.exists(path):
            with open(path) as f:
                policy_json = json.load(f)
                try:
                    # we only care about tabs that have a url_name and aren't course staff only
                    policy_tabs = policy_json['course/course']['tabs']
                    print policy_tabs
                    tabs = [tab for tab in policy_tabs if 'url_slug' in tab.keys() and not tab['course_staff_only']]
                except KeyError:
                    return self.resolve_empty(context)
                if tabs:
                    # resolver can't return multiple filenames out of
                    #  policy.json so we have to call another resolver on each
                    tabs_xml = _("<h1>Additional Course Pages</h1>")
                    for tab in tabs:
                        # docs_xsl += "<xsl:apply-templates select=\"document('tmpfs:tabs/{}.html')\"/>".format(tab['url_slug'])
                        with open(os.path.join(self.fs.getsyspath('tabs'), '{}.html'.format(tab['url_slug']))) as html:
                            tabs_xml += u"\n<h2>{}</h2>".format(tab['name']) + '\n' + html.read().decode('utf-8') + "<hr/>"
                    return self.resolve_string(u"<xml>{}</xml>".format(tabs_xml), context)
                else:
                    return self.resolve_empty(context)
        else:
            return self.resolve_empty(context)


class ExportFSUpdatesJSONResolver(ExportFSResolver):
    """
    Resolve updates info/updates.items.json file using custom parsing
    """
    def resolve(self, url, id, context):
        if not url.startswith('updates:'):
            return None   # move on to next Resolver

        path = self.fs.getsyspath(url.replace('updates:', '', 1))

        if os.path.exists(path):
            with open(path) as f:
                updates_json = json.load(f)
                if len(updates_json):
                    updates_xml = ""
                    for update in updates_json:
                        if update['status'] == 'visible':
                            updates_xml += "<h4>{}</h4>".format(update['date'])
                            updates_xml += update['content']
                    return self.resolve_string(u"<xml>{}</xml>".format(updates_xml), context)
                else:
                    return self.resolve_empty(context)
        else:
            return self.resolve_empty(context)


class AssetURLResolver(ExportFSResolver):
    """ Resolve to string of content asset URL via assets.json"""

    def resolve(self, url, id, context):
        if not url.startswith('asseturl:'):
            return None   # move on to next Resolver

        asset_id = url.replace('asseturl:/static/', '', 1)
        json_path = self.fs.getsyspath("policies/assets.json")
        if os.path.exists(json_path):
            with open(json_path) as f:
                assets = json.load(f)
                try:
                    asset_url = assets[asset_id]['filename']
                    return self.resolve_string(u"<xml>{}</xml>".format(asset_url), context)
                except KeyError:
                    return self.resolve_empty(context)
        else:
            return self.resolve_empty(context)
