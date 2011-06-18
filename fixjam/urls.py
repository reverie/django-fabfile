from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template, redirect_to

from root_dir import root_dir

admin.autodiscover()

urlpatterns = patterns('fixjam.core.views',
    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^accounts/', include('registration.urls')),

    (r'^$', 'index'),

)

urlpatterns += patterns('',
    (r'^favicon\.ico$', redirect_to, {'url': '/static/images/favicon.ico'}),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                {'document_root': root_dir('..', 'static')})
        )

