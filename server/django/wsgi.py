import os, sys, site
sys.path.insert(0, '/project/{{ PROJECT_NAME }}/current')
# The project root should be on the pythonpath. This lets you drop-in 3rd-party apps.
sys.path.insert(0, '/project/{{ PROJECT_NAME }}/current/{{ PROJECT_NAME }}')
site.addsitedir('/envs/{{ PROJECT_NAME }}/lib/python{{ PYTHON_VERSION_STR }}/site-packages/')

os.environ['DJANGO_SETTINGS_MODULE'] = '{{ PROJECT_NAME }}.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
