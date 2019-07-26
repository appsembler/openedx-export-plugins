# -*- coding: utf-8 -*-
"""
URLs for openedx_export_plugins.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import patterns, url

from lms.envs.common import COURSE_KEY_PATTERN


urlpatterns = patterns(
    '',
    url(r'^export/{}/(?P<plugin_name>.*)$'.format(COURSE_KEY_PATTERN),
        'openedx_export_plugins.views.plugin_export_handler'),
    url(r'^export/all/(?P<plugin_name>.*)$',
        'openedx_export_plugins.views.plugin_export_handler'),
)
