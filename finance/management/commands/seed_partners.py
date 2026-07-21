from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from finance.models import Partner
import datetime

class Command(BaseCommand):
    help = 'Seeds default partner users and profiles for Co-Fi'

    def handle(self, *args, **kwargs):
        # 1. Create Superuser (Admin) if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS("Superuser 'admin' created with password 'admin123'."))

        # 2. Define Partner Data
        partners_data = [
            {
                'username': 'partner1',
                'password': 'partner1password',
                'email': 'partner1@example.com',
                'name': 'Ashish',
                'phone': '+91 98765 43210'
            },
            {
                'username': 'partner2',
                'password': 'partner2password',
                'email': 'partner2@example.com',
                'name': 'Akhil',
                'phone': '+91 87654 32109'
            }
        ]

        # 3. Seed Partners
        for p_info in partners_data:
            user, created = User.objects.get_or_create(
                username=p_info['username'],
                defaults={'email': p_info['email']}
            )
            if created:
                user.set_password(p_info['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"User '{p_info['username']}' created with password '{p_info['password']}'."))
            else:
                self.stdout.write(f"User '{p_info['username']}' already exists.")

            # Get or create Partner Profile
            partner, p_created = Partner.objects.get_or_create(
                user=user,
                defaults={
                    'name': p_info['name'],
                    'email': p_info['email'],
                    'phone': p_info['phone']
                }
            )
            if p_created:
                self.stdout.write(self.style.SUCCESS(f"Partner profile created for '{p_info['name']}'."))
            else:
                # Update existing profile details
                partner.name = p_info['name']
                partner.email = p_info['email']
                partner.phone = p_info['phone']
                partner.save()
                self.stdout.write(self.style.SUCCESS(f"Partner profile updated to '{p_info['name']}'."))
