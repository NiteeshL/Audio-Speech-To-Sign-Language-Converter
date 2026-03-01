from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from django.contrib.staticfiles import finders
import os
import tempfile

try:
	from faster_whisper import WhisperModel
except Exception:
	WhisperModel = None


WHISPER_MODEL = None


def _get_whisper_model():
	global WHISPER_MODEL
	if WHISPER_MODEL is None:
		WHISPER_MODEL = WhisperModel("small", device="cpu", compute_type="int8")
	return WHISPER_MODEL

def home_view(request):
	return render(request,'home.html')


def manifest_view(request):
	manifest_content = """
{
	"id": "/",
	"name": "GestureStream Console",
	"short_name": "GestureStream",
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
			"src": "/static/pwa-192.png",
			"sizes": "192x192",
			"type": "image/png",
			"purpose": "any maskable"
		},
		{
			"src": "/static/pwa-512.png",
			"sizes": "512x512",
			"type": "image/png",
			"purpose": "any maskable"
		}
	]
}
""".strip()
	response = HttpResponse(manifest_content, content_type='application/manifest+json')
	response['Cache-Control'] = 'no-cache'
	return response


def service_worker_view(request):
	service_worker = """
const CACHE_NAME = 'gesturestream-v1';
const ASSETS_TO_CACHE = [
	'/',
	'/animation/',
	'/manifest.webmanifest',
	'/static/pwa-192.png',
	'/static/pwa-512.png',
	'/static/pwa-180.png',
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
	event.respondWith(
		caches.match(event.request).then((cached) => cached || fetch(event.request))
	);
});
""".strip()
	response = HttpResponse(service_worker, content_type='application/javascript')
	response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	return response


@require_POST
def transcribe_audio_view(request):
	if WhisperModel is None:
		return JsonResponse({'error': 'Whisper dependency is not installed.'}, status=500)

	audio_file = request.FILES.get('audio')
	if not audio_file:
		return JsonResponse({'error': 'Audio file is required.'}, status=400)

	_, extension = os.path.splitext(audio_file.name or '')
	if not extension:
		extension = '.webm'

	temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
	try:
		for chunk in audio_file.chunks():
			temp_file.write(chunk)
		temp_file.flush()
		temp_file.close()

		model = _get_whisper_model()
		segments, info = model.transcribe(temp_file.name, beam_size=5, vad_filter=True)
		transcribed_text = " ".join(segment.text.strip() for segment in segments).strip()

		return JsonResponse({
			'text': transcribed_text,
			'detected_language': getattr(info, 'language', 'unknown'),
			'language_probability': getattr(info, 'language_probability', 0),
		})
	except Exception:
		return JsonResponse({'error': 'Unable to transcribe audio.'}, status=500)
	finally:
		if os.path.exists(temp_file.name):
			os.remove(temp_file.name)

def animation_view(request):
	if request.method == 'POST':
		text = request.POST.get('sen')
		#tokenizing the sentence
		text.lower()
		#tokenizing the sentence
		words = word_tokenize(text)

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


		#adding the specific word to specify tense
		words = filtered_text
		temp=[]
		for w in words:
			if w=='I':
				temp.append('Me')
			else:
				temp.append(w)
		words = temp
		probable_tense = max(tense,key=tense.get)

		if probable_tense == "past" and tense["past"]>=1:
			temp = ["Before"]
			temp = temp + words
			words = temp
		elif probable_tense == "future" and tense["future"]>=1:
			if "Will" not in words:
					temp = ["Will"]
					temp = temp + words
					words = temp
			else:
				pass
		elif probable_tense == "present":
			if tense["present_continuous"]>=1:
				temp = ["Now"]
				temp = temp + words
				words = temp


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
