from django.contrib import admin
from .models import Word, Comment, Url, DRAEInfo, FlickrImage, VoteWord, ApiMeme

# Register your models here.
admin.site.register(Word)
admin.site.register(Comment)
admin.site.register(Url)
admin.site.register(DRAEInfo)
admin.site.register(FlickrImage)
admin.site.register(VoteWord)
admin.site.register(ApiMeme)
