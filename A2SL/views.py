from django.shortcuts import render
from django.http import HttpResponse
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from django.contrib.staticfiles import finders

def home_view(request):
	return render(request,'home.html')


def manifest_view(request):
	manifest_content = """
{
	"id": "/",
	"name": "சைகை",
	"short_name": "சைகை",
	"description": "Multilingual speech to sign animation workspace",
	"start_url": "/",
	"scope": "/",
	"display": "standalone",
	"display_override": ["standalone", "minimal-ui"],
	"background_color": "#070b1a",
	"theme_color": "#101a36",
	"lang": "en-US",
	"icons": [
		{
			"src": "/static/logo.jpg",
			"sizes": "192x192",
			"type": "image/jpeg",
			"purpose": "any"
		},
		{
			"src": "/static/logo.jpg",
			"sizes": "512x512",
			"type": "image/jpeg",
			"purpose": "any"
		},
		{
			"src": "/static/logo.jpg",
			"sizes": "180x180",
			"type": "image/jpeg",
			"purpose": "any"
		}
	]
}
""".strip()
	response = HttpResponse(manifest_content, content_type='application/manifest+json')
	response['Cache-Control'] = 'no-cache'
	return response


def service_worker_view(request):
	service_worker = """
const CACHE_NAME = 'gesturestream-v2';
const ASSETS_TO_CACHE = [
	'/static/logo.jpg',
	'/static/mic3.png'
];

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((keys) => Promise.all(keys
			.filter((key) => key !== CACHE_NAME)
			.map((key) => caches.delete(key))))
	);
});

self.addEventListener('fetch', (event) => {
	if (event.request.method !== 'GET') {
		return;
	}

	if (event.request.mode === 'navigate' || (event.request.headers.get('accept') || '').includes('text/html')) {
		return;
	}

	event.respondWith(
		caches.match(event.request).then((cached) => cached || fetch(event.request))
	);
});
""".strip()
	response = HttpResponse(service_worker, content_type='application/javascript')
	response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	return response

def animation_view(request):
	if request.method == 'POST':
		text = request.POST.get('sen')
		#tokenizing the sentence
		text.lower()
		#tokenizing the sentence
		words = word_tokenize(text)
		words = [word for word in words if any(char.isalnum() for char in word)]

		tagged = nltk.pos_tag(words)
		tense = {}
		tense["future"] = len([word for word in tagged if word[1] == "MD"])
		tense["present"] = len([word for word in tagged if word[1] in ["VBP", "VBZ","VBG"]])
		tense["past"] = len([word for word in tagged if word[1] in ["VBD", "VBN"]])
		tense["present_continuous"] = len([word for word in tagged if word[1] in ["VBG"]])



		#stopwords that will be removed
		stop_words = set(["mightn't", 're', 'wasn', 'wouldn', 'be', 'has', 'that', 'does', 'shouldn', 'do', "you've",'off', 'for', "didn't", 'm', 'ain', 'haven', "weren't", 'are', "she's", "wasn't", 'its', "haven't", "wouldn't", 'don', 'weren', 's', "you'd", "don't", 'doesn', "hadn't", 'is', 'was', "that'll", "should've", 'a', 'then', 'the', 'mustn', 'i', 'nor', 'as', "it's", "needn't", 'd', 'am', 'have',  'hasn', 'o', "aren't", "you'll", "couldn't", "you're", "mustn't", 'didn', "doesn't", 'll', 'an', 'hadn', 'whom', 'y', "hasn't", 'itself', 'couldn', 'needn', "shan't", 'isn', 'been', 'such', 'shan', "shouldn't", 'aren', 'being', 'were', 'did', 'ma', 't', 'having', 'mightn', 've', "isn't", "won't"])



		#removing stopwords and applying lemmatizing nlp process to words
		lr = WordNetLemmatizer()
		filtered_text = []
		for w,p in zip(words,tagged):
			if w not in stop_words:
				if p[1]=='VBG' or p[1]=='VBD' or p[1]=='VBZ' or p[1]=='VBN' or p[1]=='NN':
					filtered_text.append(lr.lemmatize(w,pos='v'))
				elif p[1]=='JJ' or p[1]=='JJR' or p[1]=='JJS'or p[1]=='RBR' or p[1]=='RBS':
					filtered_text.append(lr.lemmatize(w,pos='a'))

				else:
					filtered_text.append(lr.lemmatize(w))


		filtered_text = []
		for w in words:
			path = w + ".mp4"
			f = finders.find(path)
			#splitting the word if its animation is not present in database
			if not f:
				for c in w:
					filtered_text.append(c)
			#otherwise animation of word
			else:
				filtered_text.append(w)
		words = filtered_text;


		return render(request,'animation.html',{'words':words,'text':text})
	else:
		return render(request,'animation.html')
