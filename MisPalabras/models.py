from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Word(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    definition = models.TextField(blank=True)
    image = models.TextField()
    votes = models.IntegerField(default=0)
    short_def = models.CharField(max_length=300, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    full_url = models.URLField(blank=True)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    date = models.DateTimeField(auto_now=True)


class Url(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    link = models.URLField()
    date = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)
    image = models.TextField()


class DRAEInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.OneToOneField(Word, on_delete=models.CASCADE, primary_key=True)
    description = models.TextField()
    date = models.DateTimeField(auto_now=True)


class FlickrImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    image = models.TextField(blank=True)
    date = models.DateTimeField(auto_now=True)


class ApiMeme(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    image = models.TextField(blank=True)
    text = models.TextField(blank=True)
    date = models.DateTimeField(auto_now=True)


class VoteWord(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)
