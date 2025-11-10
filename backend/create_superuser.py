from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(email="shams@gmail.com").exists():
    User.objects.create_superuser(
        email="shams@gmail.com",
        password="12345",
        name="shams",
        tc=True,
        phone="03339853616"
    )
    print("✅ Superuser created successfully: shams@gmail.com / 12345")
else:
    print("⚠️ Superuser already exists: shams@gmail.com")
