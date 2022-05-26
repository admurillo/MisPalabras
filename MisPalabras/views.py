from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import WordSearchForm, CommentForm, UrlForm, MemeForm, LoginForm
from .models import Word, Comment, DRAEInfo, Url, FlickrImage, VoteWord, ApiMeme
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import random
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import quote
from .wikiparser import WikiChannel
from django.core.serializers import serialize
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# Create your views here.
def login_or_signup(request, action):
    created = True
    exists = False

    data = request.POST
    username = data.get("username")
    password = data.get("password")

    if action == "Login":
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        else:
            created = False

    elif action == "SignUp":
        created = True
        user = authenticate(request, username=username, password=password)
        if user is None:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            login(request, user)
        else:
            exists = True

    return created, exists


def wiki_info(request, name):
    url = f'https://es.wikipedia.org/w/api.php?action=query&format=xml&titles={quote(name)}&prop=extracts&exintro&explaintext'
    xml_stream = urllib.request.urlopen(url)
    definition = WikiChannel(xml_stream).definition()

    url2 = f'https://es.wikipedia.org/w/api.php?action=query&titles={quote(name)}&prop=pageimages&format=json&pithumbsize=200'
    with urllib.request.urlopen(url2) as json_doc:
        json_str = json_doc.read().decode(encoding="ISO-8859-1")
        data = json.dumps(json.loads(json_str))
        try:
            image = data.split('"source"')[1].split('"width"')[0][3:][:-3]
        except:
            image = ""

    return definition, image


def get_drae_info(request, word):
    url = f'https://dle.rae.es/{quote(word.name)}'
    user_agent = "Mozilla/5.0 (X11) Gecko/20100101 Firefox/100.0"
    req = urllib.request.Request(url, headers={'User-Agent': user_agent})
    page = urllib.request.urlopen(req)
    bs = BeautifulSoup(page.read(), 'html.parser')
    description = bs.find('meta', property='og:description')
    description = description['content']
    drae_info = DRAEInfo(user=request.user, word=word, description=description)
    drae_info.save()


def get_flickr_image(request, word):
    url = f'https://www.flickr.com/services/feeds/photos_public.gne?tags={quote(word.name)}'
    user_agent = "Mozilla/5.0 (X11) Gecko/20100101 Firefox/100.0"
    req = urllib.request.Request(url, headers={'User-Agent': user_agent})
    page = urllib.request.urlopen(req)
    bs = BeautifulSoup(page.read(), 'xml')
    image = bs.find('link', rel='enclosure')
    image = image['href']
    flickr_image = FlickrImage(user=request.user, word=word, image=image)
    flickr_image.save()


@csrf_exempt
def get_embedded_info(request):
    data = request.POST
    link = data.get("link")

    user_agent = "Mozilla/5.0 (X11) Gecko/20100101 Firefox/100.0"
    req = urllib.request.Request(link, headers={'User-Agent': user_agent})
    page = urllib.request.urlopen(req)
    bs = BeautifulSoup(page.read(), 'html.parser')

    try:
        image = bs.find('meta', property='og:image')
        image = image['content']
    except:
        image = ""

    try:
        description = bs.find('meta', property='og:description')

        if description is None:
            description = bs.find('meta', property='og:title')

        description = description['content']
    except:
        description = ""

    return image, description


def get_common_items(request):
    wordsearch_form = WordSearchForm(request.POST or None)
    try:
        random_word = random.choice(Word.objects.all())
        sorted_words = Word.objects.all().order_by('-votes')[:10]
        words_number = Word.objects.count()
    except IndexError:
        random_word = None
        sorted_words = None
        words_number = 0

    return wordsearch_form, random_word, sorted_words, words_number


def get_paginated_words(request):
    word_list = Word.objects.all().order_by('-date')

    paginator = Paginator(word_list, 5)
    page = request.GET.get('page')

    try:
        paginated_words = paginator.page(page)
    except PageNotAnInteger:  # Deliver first page
        paginated_words = paginator.page(1)
    except EmptyPage:  # Deliver last page
        paginated_words = paginator.page(paginator.num_pages)

    return paginated_words


@csrf_exempt
def index(request):
    wordsearch_form, random_word, sorted_words, words_number = get_common_items(request)
    login_form = LoginForm(request.POST or None)
    created = True
    exists = False

    if request.method == "POST":
        action = request.POST["action"]

        if action == "Login" or action == "SignUp":
            if login_form.is_valid():
                created, exists = login_or_signup(request, action)

        elif action == "Logout":
            created = True
            logout(request)

        elif action == "SearchWord":
            if wordsearch_form.is_valid():
                data = request.POST
                name = data.get("name")
                return redirect('get_word', name=name)

    paginated_words = get_paginated_words(request)

    context = {
        'created': created,
        'exists': exists,
        'login_form': login_form,
        'word_list': paginated_words,
        'wordsearch_form': wordsearch_form,
        'sorted_words': sorted_words,
        'words_number': words_number,
        'random_word': random_word,
    }

    format = request.GET.get('format')
    if format == 'xml':
        content = serialize('xml', Word.objects.all())
        return HttpResponse(content, content_type="application/xml")

    elif format == 'json':
        content = serialize('json', Word.objects.all())
        return HttpResponse(content, content_type="application/json")

    return render(request, 'MisPalabras/index.html', context)


@csrf_exempt
def get_word(request, name):
    try:
        word = Word.objects.get(name=name)
        comment_form = CommentForm(request.POST or None)
        url_form = UrlForm(request.POST or None)
        meme_form = MemeForm(request.POST or None)
        if request.user.is_authenticated:
            try:
                vote_word = VoteWord.objects.get(user=request.user, word=word)
            except VoteWord.DoesNotExist:
                vote_word = ""
        else:
            vote_word = ""
        wordsearch_form, random_word, sorted_words, words_number = get_common_items(request)
        login_form = LoginForm(request.POST or None)
        created = True
        exists = False

        if request.method == "POST":
            action = request.POST["action"]

            if action == "Login" or action == "SignUp":
                if login_form.is_valid():
                    created, exists = login_or_signup(request, action)

            elif action == "Logout":
                created = True
                logout(request)

            elif action == "SearchWord":
                if wordsearch_form.is_valid():
                    data = request.POST
                    name = data.get("name")
                    return redirect('get_word', name=name)

            elif action == "SendComment":
                if comment_form.is_valid():
                    comment_form.instance.user = request.user
                    comment_form.instance.word = word
                    comment = comment_form.save()
                    comment.save()
                return redirect('get_word', name=word.name)

            elif action == "SendUrl":
                if url_form.is_valid():
                    url_form.instance.user = request.user
                    url_form.instance.word = word
                    url = url_form.save()
                    image, description = get_embedded_info(request)
                    url.image = image
                    url.description = description
                    url.save()
                return redirect('get_word', name=word.name)

            elif action == "DRAEInfo":
                get_drae_info(request, word)
                return redirect('get_word', name=word.name)

            elif action == "FlickrImage":
                get_flickr_image(request, word)
                return redirect('get_word', name=word.name)

            elif action == "SendMeme":
                if meme_form.is_valid():
                    meme_form.instance.user = request.user
                    meme_form.instance.word = word
                    meme = meme_form.save()
                    data = request.POST
                    text = data.get("text")
                    image = data.get("image")
                    url = f'http://apimeme.com/meme?meme={quote(image)}&top={quote(word.name)}&bottom={quote(text)}'
                    meme.image = url
                    meme.text = text
                    meme.save()
                return redirect('get_word', name=word.name)

            elif action == "VoteWord":
                word.votes += 1
                word.save()
                vote_word = VoteWord(user=request.user, word=word)
                vote_word.save()
                return redirect('get_word', name=word.name)

            elif action == "DeleteVote":
                word.votes -= 1
                word.save()
                VoteWord.objects.filter(user=request.user, word=word).delete()
                return redirect('get_word', name=word.name)

        context = {
            'crated': created,
            'exists': exists,
            'login_form': login_form,
            'word': word,
            'comment_form': comment_form,
            'url_form': url_form,
            'meme_form': meme_form,
            'vote_word': vote_word,
            'wordsearch_form': wordsearch_form,
            'sorted_words': sorted_words,
            'words_number': words_number,
            'random_word': random_word,
        }

    except Word.DoesNotExist:
        definition, image = wiki_info(request, name)
        short_def = definition[:300]
        wordsearch_form, random_word, sorted_words, words_number = get_common_items(request)
        login_form = LoginForm(request.POST or None)
        created = True
        exists = False

        if request.method == "POST":
            action = request.POST['action']

            if action == "Login" or action == "SignUp":
                if login_form.is_valid():
                    created, exists = login_or_signup(request, action)

            elif action == "Logout":
                created = True
                logout(request)

            elif action == "SearchWord":
                if wordsearch_form.is_valid():
                    data = request.POST
                    name = data.get("name")
                    return redirect('get_word', name=name)

            elif action == "Save":
                url = request.build_absolute_uri(reverse('get_word', args=[name]))
                word = Word(user=request.user, name=name,
                            definition=definition, image=image,
                            short_def=short_def, full_url=url)
                word.save()
                return redirect('get_word', name=word.name)

            elif action == "Delete":
                return redirect('index')

        context = {
            'created': created,
            'exists': exists,
            'login_form': login_form,
            'name': name,
            'definition': definition,
            'image': image,
            'wordsearch_form': wordsearch_form,
            'sorted_words': sorted_words,
            'words_number': words_number,
            'random_word': random_word,
        }

    return render(request, 'MisPalabras/word_page.html', context)


def help_info(request):
    wordsearch_form, random_word, sorted_words, words_number = get_common_items(request)
    login_form = LoginForm(request.POST or None)
    created = True
    exists = False

    if request.method == "POST":
        action = request.POST["action"]

        if action == "Login" or action == "SignUp":
            if login_form.is_valid():
                created, exists = login_or_signup(request, action)

        elif action == "Logout":
            created = True
            logout(request)

        elif action == "SearchWord":
            if wordsearch_form.is_valid():
                data = request.POST
                name = data.get("name")
                return redirect('get_word', name=name)

    context = {
        'created': created,
        'exists': exists,
        'login_form': login_form,
        'wordsearch_form': wordsearch_form,
        'sorted_words': sorted_words,
        'words_number': words_number,
        'random_word': random_word,
    }

    return render(request, 'MisPalabras/help.html', context)


def my_page(request):
    wordsearch_form, random_word, sorted_words, words_number = get_common_items(request)
    login_form = LoginForm(request.POST or None)
    created = True
    exists = False

    if request.method == "POST":
        action = request.POST["action"]

        if action == "Login" or action == "SignUp":
            if login_form.is_valid():
                created, exists = login_or_signup(request, action)

        elif action == "Logout":
            created = True
            logout(request)

        elif action == "SearchWord":
            if wordsearch_form.is_valid():
                data = request.POST
                name = data.get("name")
                return redirect('get_word', name=name)

        elif action == "Delete":
            User.objects.get(username=request.user.username, password=request.user.password).delete()
            return redirect('index')

    if request.user.is_authenticated:
        word_list = Word.objects.filter(user=request.user).order_by('-date')
        comment_list = Comment.objects.filter(user=request.user).order_by('-date')
        url_list = Url.objects.filter(user=request.user).order_by('-date')
        drae_info_list = DRAEInfo.objects.filter(user=request.user).order_by('-date')
        flickr_image_list = FlickrImage.objects.filter(user=request.user).order_by('-date')
        meme_list = ApiMeme.objects.filter(user=request.user).order_by('-date')

        context = {
            'created': created,
            'exists': exists,
            'login_form': login_form,
            'word_list': word_list,
            'comment_list': comment_list,
            'url_list': url_list,
            'drae_info_list': drae_info_list,
            'flickr_image_list': flickr_image_list,
            'meme_list': meme_list,
            'wordsearch_form': wordsearch_form,
            'sorted_words': sorted_words,
            'words_number': words_number,
            'random_word': random_word,
        }
        return render(request, 'MisPalabras/my_page.html', context)

    else:
        paginated_words = get_paginated_words(request)

        context = {
            'created': created,
            'exists': exists,
            'login_form': login_form,
            'word_list': paginated_words,
            'wordsearch_form': wordsearch_form,
            'sorted_words': sorted_words,
            'words_number': words_number,
            'random_word': random_word,
        }
        return render(request, 'MisPalabras/index.html', context)
