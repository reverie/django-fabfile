"""
Support both Django auth and FB Connect.
"""
import datetime
from picklefield.fields import PickledObjectField

from django.contrib.auth.models import User, AnonymousUser
from django.db import models

from fixjam.common.dependencies import FEATURES
from fixjam.common.models import BaseModel

TWITTER_SESSION_KEY = '_twitter_user_id'

class ModelWithCache(models.Model):
    """
    Stores info beyond the basic profile that is time-consuming
    to calculate.
    """
    data_cache = PickledObjectField(null=True)

    def get_cached_data(self, name, fetcher, *args):
        expiry_key = name + '_updated'
        if ( 
            (not self.data_cache)
            or (name not in self.data_cache)
            or (expiry_key not in self.data_cache)
            or (self.data_cache[expiry_key] < 
                    datetime.datetime.now() - datetime.timedelta(days=1))
        ):
            self.data_cache = self.data_cache or {}
            self.data_cache[name] = fetcher(*args)
            self.data_cache[expiry_key] = datetime.datetime.now()
            self.save()
        return self.data_cache[name]

    class Meta:
        abstract = True

class FacebookUser(BaseModel, ModelWithCache):
    remote_id = models.BigIntegerField(unique=True)

    # Don't use this directly; use get_info method
    user_info = PickledObjectField(null=True)

    @classmethod
    def from_session(self, session_dict):
        fbid = session_dict['uid']
        return self.objects.get_or_create(remote_id=fbid, defaults={'user_info': {}})[0]

    def update_info(self, api_instance):
        # TODO: call this more often? users tells when they add location eg?
        self.user_info = api_instance.get_object('me')
        self.save()

    def get_info(self, api_instance):
        if not self.user_info:
            self.update_info(api_instance)
        return self.user_info

    @staticmethod
    def is_fb_object(o):
        return isinstance(o, dict) and ('id' in o) and ('name' in o)

    def pages_from_profile(self, fb_api):
        objects = [self.user_info]
        pages = []
        while objects:
            o = objects.pop()
            if self.is_fb_object(o):
                pages.append(o)
            if isinstance(o, dict):
                objects.extend(o.values())
            elif isinstance(o, list):
                objects.extend(o)
        return pages

    def pages_for_user(self, fb_api):
        """List of fb objects of interest for fb user."""
        objects = self.pages_from_profile(fb_api)
        objects.extend(fb_api.get_connections('me', 'likes')['data'])
        ids = [str(x['id']) for x in objects]
        full_object_info = fb_api.get_objects(ids)
        for id, info in full_object_info.items():
            if not (('id' in info) and ('name' in info) and ('fan_count' in info)):
                del full_object_info[id]
        return full_object_info.values()

    def get_pages(self, fb_api):
        """List of all Graph API objects this user is connected to"""
        return self.get_cached_data('pages', self.pages_for_user, fb_api)

class TwitterUser(BaseModel, ModelWithCache):
    screen_name = models.CharField(max_length=20, unique=True)
    oauth_token = models.TextField()
    oauth_secret = models.TextField()
    user_info = PickledObjectField(null=True)

    @classmethod
    def from_access_token(self, access_token):
        return self.objects.get_or_create(
                screen_name=access_token['screen_name'],
                defaults={
                    'oauth_token': access_token['oauth_token'],
                    'oauth_secret': access_token['oauth_token_secret']
                })[0]

    def api_request(self, url, method, parameters=None):
        import simplejson, oauth2
        from django.conf import settings
        consumer = oauth2.Consumer(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
        token = oauth2.Token(self.oauth_token, self.oauth_secret)
        client = oauth2.Client(consumer, token)
        headers, response = client.request(url, method, parameters=parameters)
        response = simplejson.loads(response)
        assert int(headers['status']) == 200, response
        return response

    def update_info(self):
        url = 'https://twitter.com/account/verify_credentials.json'
        self.user_info = self.api_request(url, 'GET')
        self.save()

    def send_status_update(self, msg):
        url = 'http://api.twitter.com/1/statuses/update.json'
        return self.api_request(url, 'POST', parameters={'status': msg})

    def get_info(self):
        if not self.user_info:
            self.update_info()
        return self.user_info

class MultiUserIncompatible(Exception):
    pass

class MultiUser(BaseModel):
    # TODO: Make manager always select_related the actual user

    # Additionally:
    # TODO: update this to include twitter user; constraint dropped for now
    # ALTER TABLE multiauth_multiuser ADD CONSTRAINT exactly_one_account CHECK ((auth_user_id IS NULL) <> (fb_user_id IS NULL) <> (twitter_user IS NULL>);

    auth_user = models.ForeignKey(User, null=True, unique=True)
    fb_user = models.ForeignKey(FacebookUser, null=True, unique=True)
    twitter_user = models.ForeignKey(TwitterUser, null=True, unique=True)

    # Storing this here to support other input methods later.
    # Like lat/long directly from geolocation API.
    location = PickledObjectField(null=True) # See <Location> in API doc

    is_banned = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, default='')

    def is_authenticated(self):
        return True

    def acct_type(self):
        if self.fb_user_id:
            return 'fb'
        if self.twitter_user_id:
            return 'twitter'
        if self.auth_user_id:
            return 'auth'

    def _type_remote_id(self, acct_type):
        assert acct_type in ('auth', 'fb', 'twitter')
        if acct_type == 'auth':
            return self.auth_user.username
        elif acct_type == 'fb':
            return self.fb_user.remote_id
        elif acct_type == 'twitter':
            return self.twitter_user.screen_name

    def _type_display_name(self, acct_type, request=None):
        assert acct_type in ('auth', 'fb', 'twitter')
        if acct_type == 'auth':
            if self.auth_user.first_name:
                if self.auth_user.last_name:
                    return self.auth_user.first_name + ' ' + self.auth_user.last_name
                return self.auth_user.first_name
            return self.auth_user.username
        elif acct_type == 'fb':
            if request is None:
                fb_api = FEATURES['facebook'].GraphAPI()
            else:
                fb_api = request.fb_api
            return self.fb_user.get_info(fb_api)['name']
        elif acct_type == 'twitter':
            return self.twitter_user.get_info()['name']

    def remote_id(self):
        return self._type_remote_id(self.acct_type())

    def display_name(self, request=None):
        return self._type_display_name(self.acct_type(), request)

    def profile_image_url(self):
        acct_type = self.acct_type()
        if acct_type == 'auth':
            return None
        elif acct_type == 'fb':
            return "http://graph.facebook.com/%s/picture?type=small" % self.remote_id()
        elif acct_type == 'twitter':
            return self.twitter_user.get_info()['profile_image_url']

    def get_location(self, fb_api):
        if self.location:
            return self.location
        if self.auth_user:
            return
        if self.fb_user:
            fb_info = self.fb_user.get_info(fb_api)
            if 'location' not in fb_info:
                return
            loc = fb_info['location']
            if (not loc.get('id')) or (not loc.get('name')):
                return
            try:
                loc = Location.from_fb_location(loc)
            except UnknownLocation:
                return 
            if not loc:
                return
        else:
            assert self.twitter_user
            loc = Location.from_name(self.twitter_user.get_info()['location'])
            if not loc:
                return
        self.location = {
                'name': loc.name,
                'lat': loc.lat,
                'long': loc.long
                }
        self.save()
        return self.location

    @classmethod
    def from_set(self, auth_user=None, fb_session=None, twitter_user=None):
        """
        Given a set of accounts, creates (if necessary) and returns the 
        appropriate multiuser. If they are associated with contradictory 
        users, raise MultiUserIncompatible.
        """
        num_authd = sum(map(bool, [auth_user, fb_session, twitter_user]))
        if not num_authd:
            return AnonymousUser()
        if num_authd > 1:
            raise MultiUserIncompatible # causes auth_logout in MW

        if auth_user:
            return self.objects.get_or_create(auth_user=auth_user)[0]
        elif fb_session:
            fb_user = FacebookUser.from_session(fb_session)
            return self.objects.get_or_create(fb_user=fb_user)[0]
        else:
            assert twitter_user
            return self.objects.get_or_create(twitter_user=twitter_user)[0]

        ## Case: ... and both have MultiUser objects:
        #if auth_match and fb_match:
        #    if auth_match[0] != fb_match[0]:
        #        # TODO: if they are separate but compatible,
        #        # merge them
        #        raise ValueError, "MultiUser mismatch"
        #    return auth_match[0]
        ## Case: ... and only one has a MultiUser object:
        #if not fb_match:
        #    mu = auth_match[0]
        #    mu.fb_user = fb_user
        #    mu.save()
        #    return mu
        #if not auth_match:
        #    mu = fb_match[0]
        #    mu.auth_user = auth_user
        #    mu.save()
        #    return mu
        ## Case: ... and neither has a MultiUser object:
        #return MultiUser.objects.create(
        #        auth_user=auth_user,
        #        fb_user=fb_user)

    def __unicode__(self):
        return self.display_name()

class UnknownLocation(Exception):
    pass

class Location(BaseModel):
    """Serves mostly as a cache in front of geonames."""
    name = models.TextField(db_index=True)
    lat = models.FloatField()
    long = models.FloatField()
    fb_location_id = models.BigIntegerField(null=True, unique=True)

    @classmethod
    def from_fb_location(self, fb_loc):
        loc_id = fb_loc['id']
        name = fb_loc['name']
        assert loc_id and name
        try:
            return self.objects.get(fb_location_id=loc_id)
        except self.DoesNotExist:
            pass
        loc = self.from_name(name)
        if not loc:
            return
        # TODO: race condition?
        loc.fb_location_id = loc_id
        loc.save()
        return loc

    @classmethod
    def from_name(self, name):
        cached = self.objects.filter(name=name)[:1]
        if len(cached):
            return cached[0]
        ll = self.wrapped_ll_from_geoname(name)
        if not ll:
            return
        lat, long = ll
        return self.objects.create(name=name, lat=lat, long=long)

    @classmethod
    def wrapped_ll_from_geoname(self, name):
        import socket
        geonames = FEATURES.get('geonames', self.ll_from_geonames)
        try:
            ll = geonames(name)
        except socket.error as e:
            # Connection failed -- skip for now
            #print 'SOCKET ERROR'
            return
        except AssertionError:
            #print 'Server error'
            return
        return ll

    @staticmethod
    def ll_from_geonames(name):
        """Returns (lat, long) pair by getting from geonames."""
        #print 'll_from_geonames called'
        import httplib
        import simplejson
        import urllib
        assert isinstance(name, unicode) # Not (UTF8?) bytes
        conn = httplib.HTTPConnection('ws.geonames.org', timeout=10)
        params = {
                'q': name.encode('utf8'),
                'maxRows': 1
            }
        args = '?' + urllib.urlencode(params)
        conn.request('GET', '/searchJSON' + args, headers={'User-Agent': 'Mozilla/5.0 FlyByChat.com -- Contact andrewbadr@gmail.com'})
        #print 'ws.geonames.org/searchJSON' + args
        resp = conn.getresponse()
        assert resp.status == 200
        result = simplejson.loads(resp.read())
        conn.close()
        if not result['totalResultsCount']:
            raise UnknownLocation
        geoname = result['geonames'][0]
        return geoname['lat'], geoname['lng']

