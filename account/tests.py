from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Contact, Profile


@override_settings(THUMBNAIL_DEBUG=False)
class UserDetailFollowingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.viewer = User.objects.create_user(username="viewer")
        cls.target = User.objects.create_user(username="target")
        cls.other = User.objects.create_user(username="other")

        for user in (cls.viewer, cls.target, cls.other):
            Profile.objects.get_or_create(user=user)

        # Otra persona sigue al perfil que vamos a consultar.
        Contact.objects.create(
            user_from=cls.other,
            user_to=cls.target,
        )

        # El visitante sigue a otra persona, pero todavía no al perfil.
        Contact.objects.create(
            user_from=cls.viewer,
            user_to=cls.other,
        )

    def setUp(self):
        self.client.force_login(self.viewer)
        self.url = reverse(
            "user_detail",
            args=[self.target.username],
        )

    def test_profile_when_viewer_does_not_follow_target(self):
        response = self.client.get(
            self.url,
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "account/user/detail.html",
        )
        self.assertEqual(
            response.context["user"],
            self.target,
        )
        self.assertEqual(
            response.context["total_followers"],
            1,
        )
        self.assertIs(
            response.context["is_following"],
            False,
        )
        self.assertContains(response, 'data-action="follow"')

    def test_profile_when_viewer_follows_target(self):
        Contact.objects.create(
            user_from=self.viewer,
            user_to=self.target,
        )

        response = self.client.get(
            self.url,
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["total_followers"],
            2,
        )
        self.assertIs(
            response.context["is_following"],
            True,
        )
        self.assertContains(response, 'data-action="unfollow"')

    def test_anonymous_visitor_is_redirected_to_login(self):
        self.client.logout()

        response = self.client.get(
            self.url,
            HTTP_HOST="localhost",
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
            fetch_redirect_response=False,
        )
