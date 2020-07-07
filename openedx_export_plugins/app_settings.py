from django.conf import settings

ENV_TOKENS = settings.ENV_TOKENS
AUTH_TOKENS = settings.AUTH_TOKENS

AWS_ID = AUTH_TOKENS.get("AWS_ACCESS_KEY_ID", None)
AWS_KEY = AUTH_TOKENS.get("AWS_SECRET_ACCESS_KEY", None)

COURSE_EXPORT_PLUGIN_STORAGE_TYPE = ENV_TOKENS.get("COURSE_EXPORT_PLUGIN_STORAGE_TYPE", "s3")
COURSE_EXPORT_PLUGIN_BUCKET = ENV_TOKENS.get("COURSE_EXPORT_PLUGIN_BUCKET", "openedx-course-exports")
COURSE_EXPORT_PLUGIN_STORAGE_OVERWRITE = ENV_TOKENS.get("COURSE_EXPORT_PLUGIN_STORAGE_OVERWRITE", False)
COURSE_EXPORT_PLUGIN_TASK_QUEUE = ENV_TOKENS.get(
    "COURSE_EXPORT_PLUGIN_TASK_QUEUE",
    getattr(settings, "HIGH_MEM_QUEUE", settings.LOW_PRIORITY_QUEUE)
)
COURSE_EXPORT_PLUGIN_TASK_SCHEDULE = ENV_TOKENS.get("COURSE_EXPORT_PLUGIN_TASK_SCHEDULE", {
    "minute": "0",
    "hour": "3",
    "day_of_week": "*",
    "day_of_month": "*",
    "month_of_year": "*",
})
COURSE_EXPORT_PLUGIN_SCHEDULED_PLUGINS = ENV_TOKENS.get("COURSE_EXPORT_PLUGIN_SCHEDULED_PLUGINS", ("markdown", ))

# url settings for xsl transformers
SCHEME = "https://" if settings.HTTPS == "on" else "http://"
LMS_ROOT_URL  = getattr(settings, "LMS_ROOT_URL", "{}{}".format(SCHEME, getattr(settings, "LMS_BASE", "localhost")))
