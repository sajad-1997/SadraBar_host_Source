from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Caption
from .utils import normalize_caption


class NormalizeCaptionTests(TestCase):
    """تست توابع عمومی ماژول توضیحات"""

    def test_normalize_arabic_to_persian(self):
        self.assertEqual(normalize_caption("ي ك"), "ی ک")

    def test_normalize_removes_zwnj_and_extra_spaces(self):
        self.assertEqual(normalize_caption("هرگونه\u200cآب   خوردگی"), "هرگونه آب خوردگی")

    def test_normalize_removes_space_before_punctuation(self):
        self.assertEqual(normalize_caption("سلام ، دنیا"), "سلام، دنیا")

    def test_normalize_empty(self):
        self.assertEqual(normalize_caption(None), "")
        self.assertEqual(normalize_caption(""), "")


class CaptionViewAuthTests(TestCase):
    """دسترسی ناشناس به تمام ویوهای توضیحات باید مسدود باشد"""

    def test_all_views_require_login(self):
        urls = [
            reverse("captions:caption_list"),
            reverse("captions:add_caption"),
            reverse("captions:edit_caption", args=[1]),
            reverse("captions:search_caption"),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"URL {url} نباید بدون ورود باز باشد")
            self.assertIn("login", response.url)


class CaptionCrudTests(TestCase):
    """تست CRUD ماژول توضیحات"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="tester", password="test12345")

    def setUp(self):
        self.client.force_login(self.user)

    def test_caption_list_shows_entries(self):
        Caption.objects.create(name="خیس شدن بار", content="هرگونه آب خوردگی به مسئولیت راننده است.")
        response = self.client.get(reverse("captions:caption_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "خیس شدن بار")

    def test_caption_list_search_filter(self):
        Caption.objects.create(name="یکی", content="توضیح اول")
        Caption.objects.create(name="دومی", content="توضیح دوم")
        response = self.client.get(reverse("captions:caption_list"), {"q": "دومی"})
        self.assertContains(response, "توضیح دوم")
        self.assertNotContains(response, "توضیح اول")

    def test_add_caption_creates_with_user_tracking(self):
        response = self.client.post(
            reverse("captions:add_caption"),
            {"name": "توضیح جدید", "content": "محتوای توضیح جدید"},
        )
        self.assertRedirects(response, reverse("captions:caption_list"))
        caption = Caption.objects.get(content="محتوای توضیح جدید")
        self.assertEqual(caption.created_by, self.user)

    def test_add_caption_duplicate_is_rejected(self):
        Caption.objects.create(content="توضیح تکراری")
        response = self.client.post(
            reverse("captions:add_caption"),
            {"name": "چیز دیگر", "content": "توضیح   تکراری"},  # با فاصله اضافی = تکراری
        )
        self.assertRedirects(response, reverse("captions:caption_list"))
        self.assertEqual(Caption.objects.count(), 1)

    def test_edit_caption_updates_content(self):
        caption = Caption.objects.create(name="قدیمی", content="متن قدیمی")
        response = self.client.post(
            reverse("captions:edit_caption", args=[caption.id]),
            {"name": "جدید", "content": "متن جدید"},
        )
        self.assertRedirects(response, reverse("captions:caption_list"))
        caption.refresh_from_db()
        self.assertEqual(caption.content, "متن جدید")
        self.assertEqual(caption.updated_by, self.user)

    def test_search_caption_json(self):
        Caption.objects.create(name="بیمه", content="خسارت بیمه‌ای")
        response = self.client.get(reverse("captions:search_caption"), {"q": "بیم"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["name"], "بیمه")

    def test_search_caption_short_query_returns_empty(self):
        response = self.client.get(reverse("captions:search_caption"), {"q": "ب"})
        self.assertEqual(response.json()["results"], [])


class IssuanceIntegrationTests(TestCase):
    """بررسی اتصال ماژول صدور بارنامه به ماژول مستقل توضیحات"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="tester", password="test12345")

    def setUp(self):
        self.client.force_login(self.user)

    def test_issuance_add_caption_url_redirects_to_captions_module(self):
        response = self.client.get(reverse("issuance:crud:add_caption"))
        self.assertRedirects(response, reverse("captions:add_caption"))

    def test_issuance_form_links_to_captions_module(self):
        """فرم صدور بارنامه باید دکمه افزودن توضیح را از ماژول captions بگیرد"""
        response = self.client.get(reverse("issuance:crud:create_new"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("captions:add_caption"))

