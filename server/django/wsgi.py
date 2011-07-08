import os, sys, site
sys.path.insert(0, '/project/foobar/current')
# The project root should be on the pythonpath. This lets you drop-in 3rd-party apps.
sys.path.insert(0, '/project/foobar/current/foobar')
site.addsitedir('/envs/foobar/lib/python2.6/site-packages/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'foobar.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
