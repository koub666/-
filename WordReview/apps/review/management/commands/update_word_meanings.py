from django.core.management.base import BaseCommand
from django.db.models import Q, CharField, Value as V
from django.db.models.functions import Length
from apps.review.models import Words
from apps.review.src.spider import crawl_other_dict
import time

class Command(BaseCommand):
    help = 'Update word meanings for words that only have part of speech in the mean field'

    def handle(self, *args, **options):
        # Find words that likely only have part of speech in the mean field
        # Criteria: mean length < 10 and only contains letters and dots
        words_to_update = Words.objects.annotate(
            mean_length=Length('mean')
        ).filter(
            Q(mean_length__lt=10) & 
            Q(mean__regex=r'^[a-zA-Z\.\s]+$')
        )
        
        total_words = words_to_update.count()
        self.stdout.write(f'Found {total_words} words to update')
        
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        
        for word_obj in words_to_update:
            word = word_obj.word
            current_mean = word_obj.mean
            
            self.stdout.write(f'Processing word: {word} (current mean: {repr(current_mean)})')
            
            try:
                # Get translation from dict.cn
                status, data = crawl_other_dict(word, 'http://dict.cn/mini.php')
                
                if status == 200 and data and data.strip():
                    # Update the mean field with combined part of speech and translation
                    new_mean = f"{current_mean} {data}" if current_mean else data
                    word_obj.mean = new_mean
                    word_obj.save()
                    updated_count += 1
                    self.stdout.write(f'✓ Updated: {word} -> {repr(new_mean)}')
                else:
                    skipped_count += 1
                    self.stdout.write(f'✗ No translation found for: {word}')
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(f'✗ Error updating {word}: {str(e)}')
        
        self.stdout.write(f'\nUpdate completed:')
        self.stdout.write(f'✓ Updated: {updated_count} words')
        self.stdout.write(f'✗ Failed: {failed_count} words')
        self.stdout.write(f'➔ Skipped: {skipped_count} words')
        self.stdout.write(f'Total: {total_words} words')
