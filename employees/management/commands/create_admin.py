from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = "Create production admin user"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")

        if not all([username, email, password]):
            self.stdout.write(
                self.style.ERROR("Admin environment variables missing.")
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write("Admin user already exists.")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(
            self.style.SUCCESS("Production admin created successfully!")
        )