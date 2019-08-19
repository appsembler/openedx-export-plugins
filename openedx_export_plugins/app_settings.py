from django.conf import settings


SCHEME = 'https://' if settings.HTTPS == "on" else "http://"
LMS_ROOT_URL  = getattr(settings, 'LMS_ROOT_URL', '{}{}'.format(SCHEME, settings.LMS_BASE))
