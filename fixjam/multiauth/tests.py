from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponse
from django.test import TestCase

import mock

from fixjam.common.dependencies import FEATURES
from fixjam.common.tests import RequestFactory
from fixjam.multiauth.models import MultiUser, FacebookUser, Location, TwitterUser
from fixjam.multiauth.middleware import MultiAuthMiddleware
from fixjam.multiauth.test_data import FB_SESSION, FB_INFO, FB_NULL_LOC_INFO, TWITTER_USER_INFO

class FakeFBAPI(object):
    def get_object(self, *args, **kwargs):
        self.num_calls += 1
        return self.fb_info

    def __init__(self, fb_info):
        self.fb_info = fb_info
        self.num_calls = 0

class FakeGeoNames(object):
    def __call__(self, name):
        self.num_calls += 1
        return '1.1', '2.2'

    def __init__(self):
        self.num_calls = 0

class MiddlewareTest(TestCase):
    def setUp(self):
        self.orig_fb = FEATURES['facebook']
        self.fake_fb = mock.Mock()
        FEATURES['facebook'] = self.fake_fb

    def tearDown(self):
        FEATURES['facebook'] = self.orig_fb

    def test_anon(self):
        # Get an AnonymousUser
        self.fake_fb.get_user_from_cookie.return_value = None
        rf = RequestFactory()
        request = rf.get('/d/getauth/')
        self.assertTrue(isinstance(request.multiuser, AnonymousUser))

    def test_user(self):
        # Get a MultiUser with fb_user attached
        self.fake_fb.get_user_from_cookie.return_value = FB_SESSION
        self.fake_fb.GraphAPI = lambda *a: FakeFBAPI(FB_INFO)
        rf = RequestFactory()
        request = rf.get('/d/getauth/')
        mu = request.multiuser
        self.assertTrue(isinstance(mu, MultiUser))
        self.assertEqual(int(mu.fb_user.remote_id), int(FB_SESSION['uid']))

        # Get the same user next time
        del request.multiuser
        result = MultiAuthMiddleware().process_request(request)
        self.assertEqual(result, None)
        mu2 = request.multiuser
        self.assertTrue(isinstance(mu2, MultiUser))
        self.assertEqual(mu2, mu)

        # Ban the user
        del request.multiuser
        mu.is_banned = True
        mu.save()
        result = MultiAuthMiddleware().process_request(request)
        self.assertTrue(isinstance(result, HttpResponse))
        self.assertEqual(result.status_code, 603)

class MockedTestCase(TestCase):
    def setUp(self):
        FEATURES['geonames'] = FakeGeoNames()
        self.user = User.objects.create_user('rossfan', 'tests@seddit.com', password='rossfanpw')
        self.twitter_user = TwitterUser.objects.create(
                screen_name=TWITTER_USER_INFO['screen_name'],
                user_info=TWITTER_USER_INFO,
                oauth_token='',
                oauth_secret=''
                )

    def tearDown(self):
        del FEATURES['geonames']

class MultiUserTest(MockedTestCase):
    def test_from_set_anon(self):
        u_anon = MultiUser.from_set()
        self.assertTrue(isinstance(u_anon, AnonymousUser))

    def test_from_set_fb(self):
        u_fb = MultiUser.from_set(fb_session=FB_SESSION)
        self.assertTrue(isinstance(u_fb, MultiUser))
        self.assertEqual(int(u_fb.fb_user.remote_id), int(FB_SESSION['uid']))

        u_fb2 = MultiUser.from_set(fb_session=FB_SESSION)
        self.assertEqual(u_fb2.id, u_fb.id)

    def test_from_set_auth(self):
        u_auth = MultiUser.from_set(auth_user=self.user)
        self.assertTrue(isinstance(u_auth, MultiUser))
        self.assertEqual(u_auth.auth_user_id, self.user.id)

    def test_from_set_twitter(self):
        u_twitter = MultiUser.from_set(twitter_user=self.twitter_user)
        self.assertTrue(isinstance(u_twitter, MultiUser))
        self.assertEqual(u_twitter.twitter_user_id, self.twitter_user.id)

    def test_from_set_twitter(self):
        u_twitter = MultiUser.from_set(twitter_user=self.twitter_user)


    def test_location(self):
        fb_api = FakeFBAPI(FB_INFO)

        u_auth = MultiUser.from_set(auth_user=self.user)
        self.assertEqual(u_auth.get_location(fb_api), None)

        u_fb = MultiUser.from_set(fb_session=FB_SESSION)
        loc = u_fb.get_location(fb_api)
        self.assertEqual(loc['name'], u_fb.fb_user.user_info['location']['name'])


class FacebookTest(MockedTestCase):
    def test_basic(self):
        u_fb = MultiUser.from_set(fb_session=FB_SESSION)
        u_fb.get_location(FakeFBAPI(FB_INFO))


    def test_location(self):
        fb_api = FakeFBAPI(FB_INFO)

        u_auth = MultiUser.from_set(auth_user=self.user)
        self.assertEqual(u_auth.get_location(fb_api), None)

        u_fb = MultiUser.from_set(fb_session=FB_SESSION)
        loc = u_fb.get_location(fb_api)
        self.assertEqual(loc['name'], u_fb.fb_user.user_info['location']['name'])


class FacebookTest(MockedTestCase):
    def test_basic(self):
        u_fb = MultiUser.from_set(fb_session=FB_SESSION)
        u_fb.get_location(FakeFBAPI(FB_INFO))

    def test_null_location(self):
        u_fb = MultiUser.from_set(fb_session=FB_SESSION)
        loc = u_fb.get_location(FakeFBAPI(FB_NULL_LOC_INFO))
        self.assertEqual(loc, None)

    def test_caching(self):
        startlocs = Location.objects.count()
        
        u_fb = MultiUser.from_set(fb_session=FB_SESSION)
        fb_api = FakeFBAPI(FB_INFO)
        self.assertEqual(FEATURES['geonames'].num_calls, 0)
        self.assertEqual(fb_api.num_calls, 0)
        loc1 = u_fb.get_location(fb_api)
        self.assertEqual(FEATURES['geonames'].num_calls, 1)
        self.assertEqual(fb_api.num_calls, 1)
        loc1 = u_fb.get_location(fb_api)
        self.assertEqual(FEATURES['geonames'].num_calls, 1)
        self.assertEqual(fb_api.num_calls, 1)
        
        self.assertEqual(Location.objects.count(), startlocs + 1)


class TestRealGeonames(TestCase): # Doesn't inherit from Mocked
    def test_real_geonames(self):
        assert not 'geonames' in FEATURES 
        
        loc_name = u'Oakland, CA'

        fb_api = FakeFBAPI(FB_INFO)
        fb_location = {'id': 1234, 'name': loc_name}

        loc1 = Location.from_fb_location(fb_location)
        assert isinstance(loc1, Location)
        self.assertEqual(loc1.name, loc_name)
        self.assertAlmostEqual(loc1.lat, 37.8043722)
        self.assertAlmostEqual(loc1.long, -122.2708026)

        loc2 = Location.from_fb_location(fb_location)
        # Didn't remake location:
        self.assertEqual(loc1, loc2)
