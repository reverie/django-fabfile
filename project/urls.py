from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.views.generic.simple import direct_to_template, redirect_to

from root_dir import root_dir

admin.autodiscover()

urlpatterns = patterns('main.views',
    (r'^$', 'index'),
    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    (r'^favicon\.ico$', redirect_to, {'url': '/static/images/favicon.ico'}),
)
