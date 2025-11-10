import uuid
from django.db import models
from django.contrib.auth.models import(
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin
)
import qrcode
import io
import base64
################################################################################################################################################
################################################################################################################################################
class UserManager(BaseUserManager):
    def create_user(
        self,
        email,
        name,
        tc,
        password=None,
        password2=None,
        role='customer',
        phone=None,
        **extra_fields
    ):
        if not email:
            raise ValueError('User must have an email address')
        if not phone:
            raise ValueError('User must have a phone number')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            tc=tc,
            role=role,
            phone=phone,
            **extra_fields
        )
        user.set_password(password)  # hashes password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, tc, password=None, phone=None):
        user = self.create_user(
            email=email,
            name=name,
            tc=tc,
            password=password,
            role=User.ADMIN,
            phone=phone,
            is_staff=True,
            is_superuser=True
        )
        user.save(using=self._db)
        return user
##############################################################################################################################################
##############################################################################################################################################
class User(AbstractBaseUser, PermissionsMixin):
    # Role choices to match ENUM(admin, merchant, customer)
    ADMIN = 'admin'
    MERCHANT = 'merchant'
    CUSTOMER = 'customer'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MERCHANT, 'Merchant'),
        (CUSTOMER, 'Customer'),
    ]

    # Primary key as UUID (change to BigAutoField if you prefer integer)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CUSTOMER)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    profile_image = models.TextField(blank=True, null=True)

    tc = models.BooleanField()  # terms & conditions or similar

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'tc', 'phone']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        # Admins get all permissions
        if self.role == self.ADMIN:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        # Admin can access all modules
        if self.role == self.ADMIN:
            return True
        # merchants/customers: limit as needed
        return app_label in ['auth']
    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser
    ##############################################################################################
    # ✅ UPDATED: Generate both QR text and image for customers
    def generate_qr_code(self):
        """
        Generates the customer's personal QR code.

        Returns:
        {
            "qr_text": "user:<uuid>",
            "qr_image": "data:image/png;base64,<...>"
        }
        """
        qr_text = f"user:{self.id}"  # this is what the merchant scans

        # Create QR image
        qr_img = qrcode.make(qr_text)
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "qr_text": qr_text,
            "qr_image": f"data:image/png;base64,{qr_base64}"
        }
##############################################################################################################################################
##############################################################################################################################################
###########################################################################################################
# QRScan & CustomerPoints Models=======> new
###########################################################################################################
class QRScan(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey('User', on_delete=models.CASCADE, related_name='qr_scans')
    qr_code = models.CharField(max_length=255)
    points_awarded = models.PositiveIntegerField(default=0)
    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.email} scanned {self.qr_code} ({self.points_awarded} pts)"
###########################################################################################################
class CustomerPoints(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.OneToOneField('User', on_delete=models.CASCADE, related_name='points_wallet')
    total_points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.customer.email} — {self.total_points} pts"
################################################################################################################################
class About(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
##############################################################################################
class MessageStream(models.Model):
    question = models.TextField()  # unlimited length
    answer = models.TextField()    # unlimited length
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Short preview of question for display in admin
        return self.question[:50] + ("..." if len(self.question) > 50 else "")
















