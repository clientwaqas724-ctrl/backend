# Loyalty_App/models.py
import uuid
from django.db import models
from django.conf import settings   # for AUTH_USER_MODEL
from Merchants_App.models import Merchant, Outlet, Coupon
#######################################################################################################################################################
#######################################################################################################################################################
class Transaction(models.Model):
    """
    Tracks points history and coupon redemptions.
    • Positive `points` = points added
    • Negative `points` = points redeemed
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # FK → users.id (customer)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loyalty_transactions',
        help_text="Customer who earns or redeems points."
    )
    # FK → merchants.id
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='loyalty_transactions',
        help_text="Merchant associated with this transaction."
    )
    # FK → outlets.id
    outlet = models.ForeignKey(
        Outlet,
        on_delete=models.CASCADE,
        related_name='loyalty_transactions',
        help_text="Specific outlet where the transaction occurred."
    )
    # FK → coupons.id (nullable if just adding points)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loyalty_transactions',
        help_text="Coupon redeemed in this transaction (if any)."
    )
    # Positive for add, negative for redeem
    points = models.IntegerField(
        help_text="Positive for points added, negative for redeemed."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
    def __str__(self):
        action = "Redeem" if self.points < 0 else "Add"
        return f"{action} {abs(self.points)} pts - {self.user.email} @ {self.merchant.company_name}"
#######################################################################################################################################################
#######################################################################################################################################################
