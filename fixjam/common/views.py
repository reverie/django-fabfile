"""Helpers relating to views."""

from django.http import HttpResponse

def json_response(obj):
    """Makes JSON HttpResponse out of obj."""
    from django.http import HttpResponse
    from django.utils import simplejson
    return HttpResponse(simplejson.dumps(obj), mimetype='application/javascript')

def json(f):
    """Decorator for views that return JSON."""
    from functools import wraps
    @wraps(f)
    def json_view(*args, **kwargs):
        result = f(*args, **kwargs)
        if isinstance(result, HttpResponse):
            return result
        return json_response(result)
    return json_view

def req_render_to_response(request, template, context=None):
    """render_to_response with request context"""
    from django.shortcuts import render_to_response
    from django.template import RequestContext
    context = context or {}
    rc = RequestContext(request, context)
    return render_to_response(template, context_instance=rc)

def response_403(content='Permission denied'):
    from django.http import HttpResponseForbidden
    return HttpResponseForbidden(content)

def get_post_action(post):
    actions = [key for key in post.keys() if key.startswith('submit_')]
    if not actions:
        return None
    if len(actions) != 1:
        raise ValueError('get_post_action got post with multiple actions')
    return actions[0].split('_', 1)[1]
