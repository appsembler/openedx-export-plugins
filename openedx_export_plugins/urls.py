# -*- coding: utf-8 -*-
"""
URLs for openedx_export_plugins.
"""

from django.conf import settings
from django.conf.urls import url

from openedx_export_plugins import views


urlpatterns = [
    url(r'^export/{}/(?P<plugin_name>.*)$'.format(settings.COURSE_KEY_PATTERN),
        views.plugin_export_handler),
    url(r'^export/all/(?P<plugin_name>.*)$',
        views.plugin_export_handler)
]
