
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import Quote
from .forms import QuoteForm
from .views import _pick_random


# ==========================================
# TESTY MODELU QUOTE
# ==========================================

class QuoteModelTests(TestCase):

    def test_create_quote(self):
        quote = Quote.objects.create(
            text="Wiedza to potęga.",
            author="Francis Bacon"
        )

        self.assertEqual(Quote.objects.count(), 1)
        self.assertEqual(quote.text, "Wiedza to potęga.")
        self.assertEqual(quote.author, "Francis Bacon")

    def test_create_quote_without_author(self):
        quote = Quote.objects.create(
            text="Cytat bez autora."
        )

        self.assertEqual(quote.author, "")

    def test_multiple_quotes(self):
        Quote.objects.create(text="Cytat 1", author="Autor 1")
        Quote.objects.create(text="Cytat 2", author="Autor 2")

        self.assertEqual(Quote.objects.count(), 2)


# ==========================================
# TESTY FUNKCJI LOSUJĄCEJ
# ==========================================

class RandomQuoteTests(TestCase):

    def test_returns_none_when_database_is_empty(self):
        result = _pick_random()

        self.assertIsNone(result)

    def test_returns_existing_quote(self):
        quote = Quote.objects.create(
            text="Wiedza to potęga.",
            author="Francis Bacon"
        )

        result = _pick_random()

        self.assertEqual(result, quote)

    def test_returns_one_of_existing_quotes(self):
        quote1 = Quote.objects.create(
            text="Cytat pierwszy",
            author="Autor 1"
        )
        quote2 = Quote.objects.create(
            text="Cytat drugi",
            author="Autor 2"
        )

        result = _pick_random()

        self.assertIn(result, [quote1, quote2])

    def test_excludes_previous_quote_when_possible(self):
        quote1 = Quote.objects.create(
            text="Cytat pierwszy",
            author="Autor 1"
        )
        quote2 = Quote.objects.create(
            text="Cytat drugi",
            author="Autor 2"
        )

        result = _pick_random(exclude_id=quote1.id)

        self.assertEqual(result, quote2)


# ==========================================
# TESTY FORMULARZA QUOTEFORM
# ==========================================

class QuoteFormTests(TestCase):

    def test_valid_form(self):
        form = QuoteForm(data={
            "text": "Wiedza to potęga.",
            "author": "Francis Bacon"
        })

        self.assertTrue(form.is_valid())

    def test_empty_text_is_invalid(self):
        form = QuoteForm(data={
            "text": "",
            "author": "Francis Bacon"
        })

        self.assertFalse(form.is_valid())

    def test_whitespace_only_text_is_invalid(self):
        form = QuoteForm(data={
            "text": "     ",
            "author": "Francis Bacon"
        })

        self.assertFalse(form.is_valid())

    def test_author_can_be_empty(self):
        form = QuoteForm(data={
            "text": "Cytat bez autora.",
            "author": ""
        })

        self.assertTrue(form.is_valid())


# ==========================================
# TESTY WIDOKU RANDOM_QUOTE
# ==========================================

class RandomQuoteViewTests(TestCase):

    def test_random_quote_page_returns_200(self):
        response = self.client.get(
            reverse("quotes:random")
        )

        self.assertEqual(response.status_code, 200)

    def test_random_quote_uses_correct_template(self):
        response = self.client.get(
            reverse("quotes:random")
        )

        self.assertTemplateUsed(
            response,
            "quotes/random_quote.html"
        )

    def test_random_quote_is_displayed(self):
        quote = Quote.objects.create(
            text="Wiedza to potęga.",
            author="Francis Bacon"
        )

        response = self.client.get(
            reverse("quotes:random")
        )

        self.assertEqual(response.context["quote"], quote)

    def test_empty_database_returns_none(self):
        response = self.client.get(
            reverse("quotes:random")
        )

        self.assertIsNone(response.context["quote"])

    def test_quote_is_remembered_for_the_day(self):
        quote = Quote.objects.create(
            text="Wiedza to potęga.",
            author="Francis Bacon"
        )

        first_response = self.client.get(
            reverse("quotes:random")
        )

        second_response = self.client.get(
            reverse("quotes:random")
        )

        self.assertEqual(first_response.context["quote"], quote)
        self.assertEqual(second_response.context["quote"], quote)


# ==========================================
# TESTY WIDOKU REROLL
# ==========================================

class RerollViewTests(TestCase):

    def test_reroll_requires_post_method(self):
        response = self.client.get(
            reverse("quotes:reroll")
        )

        self.assertEqual(response.status_code, 405)

    def test_reroll_redirects_to_random_quote(self):
        Quote.objects.create(
            text="Przykładowy cytat.",
            author="Autor"
        )

        response = self.client.post(
            reverse("quotes:reroll")
        )

        self.assertRedirects(
            response,
            reverse("quotes:random")
        )

    def test_reroll_selects_different_quote(self):
        quote1 = Quote.objects.create(
            text="Cytat pierwszy",
            author="Autor 1"
        )
        quote2 = Quote.objects.create(
            text="Cytat drugi",
            author="Autor 2"
        )

        session = self.client.session
        session["quote_of_day"] = {
            "id": quote1.id,
            "date": timezone.localdate().isoformat()
        }
        session.save()

        self.client.post(reverse("quotes:reroll"))

        session = self.client.session

        self.assertEqual(
            session["quote_of_day"]["id"],
            quote2.id
        )

    def test_reroll_with_empty_database_redirects_to_add(self):
        response = self.client.post(
            reverse("quotes:reroll")
        )

        self.assertRedirects(
            response,
            reverse("quotes:add")
        )

    def test_reroll_with_one_quote_keeps_that_quote(self):
        quote = Quote.objects.create(
            text="Jedyny cytat.",
            author="Autor"
        )

        self.client.post(reverse("quotes:reroll"))

        session = self.client.session

        self.assertEqual(
            session["quote_of_day"]["id"],
            quote.id
        )


# ==========================================
# TESTY WIDOKU ADD_QUOTE
# ==========================================

class AddQuoteViewTests(TestCase):

    def test_add_quote_page_returns_200(self):
        response = self.client.get(
            reverse("quotes:add")
        )

        self.assertEqual(response.status_code, 200)

    def test_add_quote_uses_correct_template(self):
        response = self.client.get(
            reverse("quotes:add")
        )

        self.assertTemplateUsed(
            response,
            "quotes/add_quote.html"
        )

    def test_add_quote_displays_form(self):
        response = self.client.get(
            reverse("quotes:add")
        )

        self.assertIsInstance(
            response.context["form"],
            QuoteForm
        )

    def test_add_quote_successfully_saves_quote(self):
        response = self.client.post(
            reverse("quotes:add"),
            {
                "text": "Wiedza to potęga.",
                "author": "Francis Bacon"
            }
        )

        self.assertRedirects(
            response,
            reverse("quotes:add")
        )

        self.assertEqual(Quote.objects.count(), 1)

        quote = Quote.objects.first()

        self.assertEqual(quote.text, "Wiedza to potęga.")
        self.assertEqual(quote.author, "Francis Bacon")

    def test_add_quote_without_author(self):
        response = self.client.post(
            reverse("quotes:add"),
            {
                "text": "Cytat bez autora.",
                "author": ""
            }
        )

        self.assertRedirects(
            response,
            reverse("quotes:add")
        )

        self.assertEqual(Quote.objects.count(), 1)

    def test_empty_text_is_not_saved(self):
        response = self.client.post(
            reverse("quotes:add"),
            {
                "text": "",
                "author": "Autor"
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Quote.objects.count(), 0)
        self.assertFalse(response.context["form"].is_valid())

    def test_whitespace_text_is_not_saved(self):
        response = self.client.post(
            reverse("quotes:add"),
            {
                "text": "     ",
                "author": "Autor"
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Quote.objects.count(), 0)

    def test_add_quote_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(
            reverse("quotes:add"),
            {
                "text": "Testowy cytat.",
                "author": "Autor"
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Quote.objects.count(), 0)
