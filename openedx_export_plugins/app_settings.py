from django.conf import settings

ENV_TOKENS = settings.ENV_TOKENS
AUTH_TOKENS = settings.AUTH_TOKENS

AWS_ID = AUTH_TOKENS.get('AWS_ACCESS_KEY_ID', None)
AWS_KEY = AUTH_TOKENS.get('AWS_SECRET_ACCESS_KEY', None)

COURSE_EXPORT_STORAGE_TYPE = ENV_TOKENS.get('COURSE_EXPORT_STORAGE_TYPE', "s3")
COURSE_EXPORT_BUCKET = ENV_TOKENS.get('COURSE_EXPORT_BUCKET', 'openedx-course-exports')
COURSE_EXPORT_SINGLE_STORAGE_FILE = ENV_TOKENS.get('COURSE_EXPORT_SINGLE_STORAGE_FILE', False)

# url settings for xsl transformers
SCHEME = 'https://' if settings.HTTPS == "on" else "http://"
LMS_ROOT_URL  = getattr(settings, 'LMS_ROOT_URL', '{}{}'.format(SCHEME, settings.LMS_BASE))
