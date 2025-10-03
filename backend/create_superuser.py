# backend/create_superuser.py
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(email="shams@gmail.com").exists():
    User.objects.create_superuser(
        email="shams@gmail.com",
        password="12345",
        name="shams",               # ✅ make sure this matches your model field
        tc=True,                    # ✅ make sure this matches your model field
        phone="03339853616",        # ✅ make sure this matches your model field
        is_staff=True,
        is_superuser=True
    )

