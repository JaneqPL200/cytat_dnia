from django.test import TestCase, Client
from django.urls import reverse

from .models import Quote
from .forms import QuoteForm
from .views import get_random_quote


# ==========================================
# TESTY MODELU QUOTE
# ==========================================

class QuoteModelTests(TestCase):

    def test_create_quote(self):
        """Sprawdza poprawne utworzenie cytatu."""

        quote = Quote.objects.create(
            text="Wiedza to potęga.",
            author="Francis Bacon"
        )

        self.assertEqual(quote.text, "Wiedza to potęga.")
        self.assertEqual(quote.author, "Francis Bacon")

    def test_quote_without_author(self):
        """Sprawdza możliwość dodania cytatu bez autora."""

        quote = Quote.objects.create(
            text="Czas to pieniądz.",
            author=""
        )

        self.assertEqual(quote.author, "")

    def test_quote_string_representation(self):
        """Sprawdza tekstową reprezentację obiektu."""

        quote = Quote.objects.create(
            text="Wiedza to potęga.",
            author="Francis Bacon"
        )

        self.assertEqual(
            str(quote),
            "Wiedza to potęga. - Francis Bacon"
        )

    def test_quote_is_saved_in_database(self):
        """Sprawdza, czy cytat został zapisany w bazie danych."""

        Quote.objects.create(
            text="Nigdy się nie poddawaj.",
            author="Autor"
        )

        self.assertEqual(Quote.objects.count(), 1)


# ==========================================
# TESTY FUNKCJI LOSUJĄCEJ
# ==========================================

class RandomQuoteTests(TestCase):

    def test_random_quote_when_database_is_empty(self):
        """Sprawdza zachowanie funkcji przy pustej bazie."""

        result = get_random_quote()

        self.assertIsNone(result)

    def test_random_quote_returns_existing_quote(self):
        """Sprawdza, czy funkcja zwraca istniejący cytat."""

        quote = Quote.objects.create(
            text="Wiedza to potęga.",
            author="Francis Bacon"
        )

        result = get_random_quote()

        self.assertIsNotNone(result)
        self.assertEqual(result.pk, quote.pk)

    def test_random_quote_returns_quote_from_database(self):
        """Sprawdza, czy wynik losowania należy do bazy."""

        Quote.objects.create(
            text="Cytat pierwszy",
            author="Autor 1"
        )

        Quote.objects.create(
            text="Cytat drugi",
            author="Autor 2"
        )

        result = get_random_quote()

        self.assertIn(
            result.text,
            ["Cytat pierwszy", "Cytat drugi"]
        )


# ==========================================
# TESTY FORMULARZA
# ==========================================

class QuoteFormTests(TestCase):

    def test_valid_quote_form(self):
        """Sprawdza poprawność formularza z prawidłowymi danymi."""

        form = QuoteForm(data={
            "text": "Wiedza to potęga.",
            "author": "Francis Bacon"
        })

        self.assertTrue(form.is_valid())

    def test_empty_quote_form(self):
        """Sprawdza odrzucanie pustej treści cytatu."""

        form = QuoteForm(data={
            "text": "",
            "author": "Autor"
        })

        self.assertFalse(form.is_valid())
        self.assertIn("text", form.errors)

    def test_quote_with_only_whitespace(self):
        """Sprawdza odrzucanie treści zawierającej same spacje."""

        form = QuoteForm(data={
            "text": "     ",
            "author": "Autor"
        })

        self.assertFalse(form.is_valid())

    def test_quote_without_author_is_valid(self):
        """Sprawdza, czy autor może pozostać pusty."""

        form = QuoteForm(data={
            "text": "Czas to pieniądz.",
            "author": ""
        })

        self.assertTrue(form.is_valid())

    def test_quote_text_is_stripped(self):
        """Sprawdza usuwanie zbędnych spacji z treści."""

        form = QuoteForm(data={
            "text": "   Wiedza to potęga.   ",
            "author": "Francis Bacon"
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["text"],
            "Wiedza to potęga."
        )


# ==========================================
# TESTY WIDOKU RANDOM_QUOTE
# ==========================================

class RandomQuoteViewTests(TestCase):

    def setUp(self):
        self.quote = Quote.objects.create(
            text="Wiedza to potęga.",
            author="Francis Bacon"
        )

    def test_random_quote_page_loads(self):
        """Sprawdza, czy strona cytatu dnia się wyświetla."""

        response = self.client.get(reverse("random_quote"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "quotes/random_quote.html"
        )

    def test_random_quote_is_displayed(self):
        """Sprawdza, czy cytat i autor są widoczni na stronie."""

        response = self.client.get(reverse("random_quote"))

        self.assertContains(response, "Wiedza to potęga.")
        self.assertContains(response, "Francis Bacon")

    def test_empty_database_message(self):
        """Sprawdza komunikat przy braku cytatów."""

        Quote.objects.all().delete()

        response = self.client.get(reverse("random_quote"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brak cytatów")


# ==========================================
# TESTY WIDOKU ADD_QUOTE
# ==========================================

class AddQuoteViewTests(TestCase):

    def test_add_quote_page_loads(self):
        """Sprawdza poprawne wyświetlanie formularza."""

        response = self.client.get(reverse("add_quote"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "quotes/add_quote.html"
        )

    def test_add_quote_contains_csrf_token(self):
        """Sprawdza obecność tokena CSRF w formularzu."""

        response = self.client.get(reverse("add_quote"))

        self.assertContains(response, "csrfmiddlewaretoken")

    def test_add_quote_successfully(self):
        """Sprawdza poprawne dodanie cytatu."""

        response = self.client.post(
            reverse("add_quote"),
            {
                "text": "Nigdy się nie poddawaj.",
                "author": "Autor testowy"
            }
        )

        self.assertRedirects(
            response,
            reverse("random_quote")
        )

        self.assertTrue(
            Quote.objects.filter(
                text="Nigdy się nie poddawaj.",
                author="Autor testowy"
            ).exists()
        )

    def test_add_quote_without_author(self):
        """Sprawdza dodawanie cytatu bez autora."""

        response = self.client.post(
            reverse("add_quote"),
            {
                "text": "Czas to pieniądz.",
                "author": ""
            }
        )

        self.assertRedirects(
            response,
            reverse("random_quote")
        )

        self.assertTrue(
            Quote.objects.filter(
                text="Czas to pieniądz.",
                author=""
            ).exists()
        )

    def test_empty_quote_is_rejected(self):
        """Sprawdza odrzucenie pustego cytatu."""

        response = self.client.post(
            reverse("add_quote"),
            {
                "text": "",
                "author": "Autor testowy"
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(Quote.objects.count(), 0)

        self.assertFormError(
            response.context["form"],
            "text",
            "To pole jest wymagane."
        )

    def test_invalid_quote_shows_error_message(self):
        """Sprawdza wyświetlanie komunikatu o błędzie."""

        response = self.client.post(
            reverse("add_quote"),
            {
                "text": "   ",
                "author": "Autor testowy"
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Treść cytatu nie może być pusta."
        )

    def test_csrf_protection(self):
        """Sprawdza, czy Django blokuje POST bez tokena CSRF."""

        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(
            reverse("add_quote"),
            {
                "text": "Test CSRF",
                "author": "Autor"
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Quote.objects.count(), 0)

    def test_success_message_after_adding_quote(self):
        """Sprawdza komunikat po poprawnym zapisaniu cytatu."""

        response = self.client.post(
            reverse("add_quote"),
            {
                "text": "Wiedza to potęga.",
                "author": "Francis Bacon"
            },
            follow=True
        )

        self.assertContains(
            response,
            "Cytat został dodany!"
        )