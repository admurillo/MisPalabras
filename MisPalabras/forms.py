from django import forms
from .models import Word, Comment, Url, ApiMeme
from django.contrib.auth.models import User


class WordSearchForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = {'name'}

    name = forms.CharField(label='', required=False)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = {'text'}

    text = forms.CharField(widget=forms.Textarea, label='', required=False)


class UrlForm(forms.ModelForm):
    class Meta:
        model = Url
        fields = {'link'}

    link = forms.CharField(label='', required=False)


class MemeForm(forms.ModelForm):
    MEME_CHOICE = [
        ('Afraid-To-Ask-Andy', 'Afraid To Ask Andy'),
        ('1990s-First-World-Problems', '1990s First World Problems'),
        ('Albert-Einstein-1', 'Albert Einstein'),
    ]

    class Meta:
        model = ApiMeme
        fields = {'text', 'image'}

    text = forms.CharField(label='Elige un texto', required=False)
    image = forms.CharField(label='Elige una imagen', widget=forms.Select(choices=MEME_CHOICE), required=False)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
