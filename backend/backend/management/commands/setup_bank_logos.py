# Create: backend/management/commands/setup_bank_logos.py
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from cards.models import Bank
import requests
from io import BytesIO
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Setup default bank logos and fix missing images'
    
    def handle(self, *args, **kwargs):
        # Create placeholder logos for banks
        banks = Bank.objects.all()
        
        for bank in banks:
            if not bank.logo or 'default' in str(bank.logo):
                # Create a simple colored logo
                logo_path = os.path.join(settings.MEDIA_ROOT, 'bank_logos', f'{bank.code.lower()}.png')
                
                # Create a simple colored image using PIL (optional)
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # Create a colored square with bank initials
                    img = Image.new('RGB', (200, 200), color=(25, 118, 210))  # Blue color
                    d = ImageDraw.Draw(img)
                    
                    # Try to add text
                    try:
                        fnt = ImageFont.truetype("arial.ttf", 60)
                    except:
                        fnt = ImageFont.load_default()
                    
                    # Add bank initials
                    text = bank.name[0] if bank.name else bank.code[0]
                    text_bbox = d.textbbox((0, 0), text, font=fnt)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    position = ((200 - text_width) // 2, (200 - text_height) // 2)
                    d.text(position, text, font=fnt, fill=(255, 255, 255))
                    
                    # Save to BytesIO
                    img_io = BytesIO()
                    img.save(img_io, format='PNG')
                    img_content = ContentFile(img_io.getvalue())
                    
                    # Save to bank
                    bank.logo.save(f'{bank.code.lower()}.png', img_content, save=True)
                    
                    self.stdout.write(f'Created logo for {bank.name}')
                    
                except ImportError:
                    # If PIL not available, just update the path
                    bank.logo = f'bank_logos/default_{bank.code.lower()}.png'
                    bank.save()
                    self.stdout.write(f'Updated logo path for {bank.name}')
        
        self.stdout.write(self.style.SUCCESS('Bank logos setup completed!'))