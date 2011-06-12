from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

from fixjam.common.dependencies import FEATURES
from fixjam.multiauth.models import MultiUser, TwitterUser, TWITTER_SESSION_KEY, MultiUserIncompatible

class MultiAuthMiddleware(object):
    """This middleware handles all account merging and login."""
    def user_info_from_request(self, request):
        user_info = {
            'auth_user': None,
            'fb_session': None,
            'twitter_user': None
        }
        # Django auth:
        if request.user.is_authenticated() and request.user.is_active:
            user_info['auth_user'] = request.user

        # Facebook:
        user_info['fb_session'] = FEATURES['facebook'].get_user_from_cookie(request.COOKIES, settings.FACEBOOK_API_KEY, settings.FACEBOOK_SECRET_KEY)

        # Twitter
        if TWITTER_SESSION_KEY in request.session:
            try:
                twitter_id = request.session[TWITTER_SESSION_KEY]
                twitter_user = TwitterUser.objects.get(id=twitter_id)
                user_info['twitter_user'] = twitter_user
            except TwitterUser.DoesNotExist:
                pass
        return user_info

    def process_request(self, request):
        user_info = self.user_info_from_request(request)
        if user_info['fb_session']:
            request.fb_api = FEATURES['facebook'].GraphAPI(
                    user_info['fb_session']['access_token'])
        else:
            request.fb_api = FEATURES['facebook'].GraphAPI()
        try:
            request.multiuser = MultiUser.from_set(**user_info)
        except MultiUserIncompatible: # get this if there's an unresolvable conflict b/w accounts
            if user_info['fb_session']:
                # We can't logout FB accounts server-side,
                # so use that as the default account.
                # (If this changed, unset fb_api above.)
                auth_logout(request)
                # NOTE: auth_logout just cleared all session data! This is only
                # OK because I know that getauth is always the first call the client
                # makes, and it checks for the sessionid after that has finished.
                # In general, the right solution is probably to:
                # - merge accounts when possible, and
                # - if not possible, return an error condition here that the client handles.
            else:
                assert user_info['twitter_user']
                del request.session[TWITTER_SESSION_KEY]
            user_info = self.user_info_from_request(request)
            request.multiuser = MultiUser.from_set(**user_info)
        if request.multiuser.is_authenticated() and request.multiuser.is_banned:
            return HttpResponse('b&', status=603)
    
    def process_response(self, request, response):
        if not hasattr(request, 'multiuser'):
            # Can happen on redirects, somehow.
            return response
        # Here was: setting and deleting of signed cookie. See chat project history.
        return response
