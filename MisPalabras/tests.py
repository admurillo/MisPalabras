from django.test import TestCase
from django.test import Client
from .models import Word


# Create your tests here.
class GetTests(TestCase):
    def test_index(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)

    def test_help(self):
        c = Client()
        response = c.get('/help')
        self.assertEqual(response.status_code, 200)

    def test_stored_word(self):
        name = 'silla'
        c = Client()
        if Word.objects.exists():
            response = c.post('/', {'name': Word.objects.get(name=name)})
            self.assertEqual(response.status_code, 302)
            content = response.content.decode('utf-8')
            self.assertIn('<h3>Comentarios:</h3>', content)

    def test_comment(self):
        comment = 'This is a comment'
        name = 'silla'
        c = Client()
        if Word.objects.exists():
            response = c.post(f'/{Word.objects.get(name=name)}', {'text': comment})
            self.assertEqual(response.status_code, 302)
            content = response.content.decode('utf-8')
            self.assertIn(comment, content)

    def test_not_stored_word(self):
        c = Client()
        response = c.get('/empty')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertNotIn('<h3>Comentarios:</h3>', content)
