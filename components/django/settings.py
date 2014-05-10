import os, sys

PROJECT_ROOT = os.path.dirname(__file__)
DEPLOY_ROOT = os.path.join(os.path.dirname(os.path.dirname(PROJECT_ROOT)), 'deploy')

SITE_ID = 1
DEBUG = True
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ['*']


####################################################################
#
# Paths and Static files
#
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))
MEDIA_ROOT                          = os.path.join(DEPLOY_ROOT, 'media')
MEDIA_URL                           = '/media/'
STATIC_ROOT                         = os.path.join(DEPLOY_ROOT, 'static')
STATIC_URL                          = '/static/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static_app'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'pipeline.finders.CachedFileFinder',
)

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
    
PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.csstidy.CSSTidyCompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.uglifyjs.UglifyJSCompressor'

PIPELINE_CSS = {
    'styles': {
        'source_filenames': (
          'main.css',
        ),
        'output_filename': 'css/main.min.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}

PIPELINE_JS = {
    'scripts': {
        'source_filenames': (
            'js/jquery-1.11.1.min.js',
            'js/sockjs-0.3.4.min.js',
            'js/stapes.min.js',
            'js/main.js',
            'js/chat.js',
        ),
        'output_filename': 'main.min.js',
    }
}


####################################################################
#
# Other django settings
#
INTERNAL_IPS                        = ('127.0.0.1',)
LANGUAGE_CODE                       = 'en-gb'
SECRET_KEY                          = '15n)qzsv)e1a$b8-8kl^5iw(wt*so+7(3zvdd^j&08+q=o&3$='
TIME_ZONE                           = 'UTC'
USE_TZ                              = True
USE_ETAGS                           = False
DEFAULT_CHARSET                     = 'utf-8'
USE_I18N                            = False
USE_L10N                            = False
PREPEND_WWW                         = False
ROOT_URLCONF                        = 'urls'
MESSAGE_STORAGE                     = 'django.contrib.messages.storage.session.SessionStorage'
#WSGI_APPLICATION                   = 'wsgi.application'
COMPRESS_HTML                       = TEMPLATE_DEBUG == False


####################################################################
#
# Cache / Sessions
#
# See: https://docs.djangoproject.com/en/1.6/topics/http/sessions/
# Redis: http://niwibe.github.io/django-redis/
#
SESSION_EXPIRE_AT_BROWSER_CLOSE     = False
SESSION_COOKIE_NAME = 'UNICORNS'
CSRF_COOKIE_NAME = 'PIRATES'
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:1',
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
            #'PASSWORD': 'secretpassword',  # Optional
        }
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


####################################################################
#
# Databases
#
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'camaste',
        'USER': 'camaste',
        'PASSWORD': 'camaste',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
            "init_command": "SET storage_engine=INNODB",
        }
    }
}


####################################################################
#
# Applications & Middleware
#
INSTALLED_APPS = (
	'django.contrib.auth',
    'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.staticfiles',
	'django.contrib.messages',
	'django.contrib.admin',
	'django.contrib.humanize',
	'south',
    'pipeline',

    'camaste',
    'backend',
)
if DEBUG:
    INSTALLED_APPS += ('devserver',)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # Transaction middleware is deprecated in 1.6+, use ATOMIC_REQUESTS
    #'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # Note: our HTML minifier is better than Pipeline's
    'camaste.middleware.MinifyHTMLMiddleware',
    #'pipeline.middleware.MinifyHTMLMiddleware',
)

####################################################################
#
# Authentication
#
AUTH_USER_MODEL = 'camaste.Account'
AUTHENTICATION_BACKENDS = (
    'camaste.auth.Backend',
)
# Only allow secure hashing algorithms
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
)

####################################################################
#
# Template settings
#
if DEBUG:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
else:
    TEMPLATE_LOADERS = (
        ('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            #'django.template.loaders.app_directories.Loader',
        )),
    )

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
 )


####################################################################
#
# Logging
#
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },        
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

