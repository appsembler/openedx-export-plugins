# -*- coding: utf-8 -*-
"""
openedx_export_plugins Django application initialization.
"""
from django.apps import AppConfig

from openedx.core.djangoapps.plugins.constants import PluginURLs, ProjectType


class OpenedxExportPluginsConfig(AppConfig):
    """
    Configuration for the openedx_export_plugins Django application.
    """

    name = 'openedx_export_plugins'
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.CMS: {
                PluginURLs.NAMESPACE: 'openedx_export_plugins',
                PluginURLs.RELATIVE_PATH: 'urls',
            }
        },
    }
