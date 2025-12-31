from apps.review.models import Words

# Check the specific word 'pretend'
try:
    w = Words.objects.get(word='pretend')
    print(f'Word: {w.word}')
    print(f'Mean: {repr(w.mean)}')
    print(f'Length of mean: {len(w.mean)}')
except Words.DoesNotExist:
    print('Word pretend not found')

# Check a few random words
print('\nChecking 5 random words:')
words = Words.objects.all().order_by('?')[:5]
for w in words:
    print(f'Word: {w.word}, Mean: {repr(w.mean)}')

# Check words with short mean values (likely just parts of speech)
print('\nChecking words with short mean values:')
short_words = Words.objects.filter(mean__length__lt=10).order_by('word')[:10]
for w in short_words:
    print(f'Word: {w.word}, Mean: {repr(w.mean)}')
