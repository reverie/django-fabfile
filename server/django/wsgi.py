import os, sys, site
sys.path.insert(0, '/project/fixjam/current')
site.addsitedir('/envs/default/lib/python2.6/site-packages/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'fixjam.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
