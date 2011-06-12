import oauth2 as oauth
import cgi

from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from fixjam.common.views import req_render_to_response
from fixjam.lib import log
from fixjam.multiauth.models import TwitterUser, TWITTER_SESSION_KEY

# It's probably a good idea to put your consumer's OAuth token and
# OAuth secret into your project's settings. 
consumer = oauth.Consumer(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)

request_token_url = 'http://twitter.com/oauth/request_token'
access_token_url = 'http://twitter.com/oauth/access_token'

# This is the slightly different URL used to authenticate/authorize.
authenticate_url = 'http://twitter.com/oauth/authenticate'

class TwitterException(Exception):
    pass

def twitter_auth(request):
    client = oauth.Client(consumer)
    # Step 1. Get a request token from Twitter.
    resp, content = client.request(request_token_url, "GET", parameters={
        'oauth_callback': request.build_absolute_uri(reverse('twitter_auth_done'))
    })
    if resp['status'] != '200':
        return req_render_to_response(request, 'about/twitter_error.html')
        #raise TwitterException(resp['status'], content)

    # Step 2. Store the request token in a session for later use.
    request.session['request_token'] = dict(cgi.parse_qsl(content))

    # Step 3. Redirect the user to the authentication URL.
    # TODO: put oauth_callback here
    url = "%s?oauth_token=%s" % (authenticate_url,
        request.session['request_token']['oauth_token'])

    return HttpResponseRedirect(url)

def twitter_auth_done(request):
    if 'denied' in request.GET:
        return HttpResponseRedirect('/')

    # Step 1. Use the request token in the session to build a new client.
    token = oauth.Token(request.session['request_token']['oauth_token'],
        request.session['request_token']['oauth_token_secret'])
    token.set_verifier(request.GET['oauth_verifier'])
    client = oauth.Client(consumer, token)

    log.info('twitter_auth_done', consumer, token, getattr(token, 'verifier', None), client)

    # Step 2. Request the authorized access token from Twitter.
    resp, content = client.request(access_token_url, "GET")
    if resp['status'] != '200':
        return req_render_to_response(request, 'about/twitter_error.html')
        #raise TwitterException(resp['status'], content)

    """
    This is what you'll get back from Twitter. Note that it includes the
    user's user_id and screen_name.
    {
        'oauth_token_secret': 'IcJXPiJh8be3BjDWW50uCY31chyhsMHEhqJVsphC3M',
        'user_id': '120889797', 
        'oauth_token': '120889797-H5zNnM3qE0iFoTTpNEHIz3noL9FKzXiOxwtnyVOD',
        'screen_name': 'heyismysiteup'
    }
    """
    access_token = dict(cgi.parse_qsl(content))

    # Step 3. Lookup the user or create them if they don't exist.
    twitter_user = TwitterUser.from_access_token(access_token)
    request.session[TWITTER_SESSION_KEY] = twitter_user.id
    return HttpResponseRedirect('/')
