from django.shortcuts import render_to_response

from common.views import req_render_to_response

def index(request):
    return req_render_to_response(request, 'index.html')
