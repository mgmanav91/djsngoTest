from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from simple_history.models import HistoricalRecords
from annoying.fields import AutoOneToOneField
from Master.models import *
from express_stores.utils import *

class PaymentMethodType(models.TextChoices):
        CASH = 'CS', _('Cash')
        CREDIT = 'CR', _('Credit')
        BHIMUPI = 'BH', _('BHIM UPI')
        PAYTM = 'PY', _('Paytm')

class StoreModel(models.Model):
    model_type = models.CharField(max_length=50)

class Store(models.Model):
    user = AutoOneToOneField(User, on_delete=models.DO_NOTHING, related_name='store', primary_key=True)
    location = models.ForeignKey(
        'Master.Location',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    registered_phone_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=10, default="1234")
    address = models.TextField(default="")
    geolocation = models.CharField(max_length=50)
    is_gst_mandatory = models.BooleanField(default=False)
    gst_number = models.CharField(max_length=50)
    model_type = models.ForeignKey(
        'StoreModel',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    shop_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.shop_name

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class StoreCustomer(models.Model):
    class GenderType(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
    id = models.CharField(max_length=10, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    store = models.ForeignKey(
        'Store',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    
    name = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=2,
        choices=GenderType.choices,
        default=GenderType.MALE,
    )
    phone_number = models.CharField(max_length=15)
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_orders = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    avg_discount_per_order = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return "%s (%s)"%(self.name, self.phone_number)


class StoreInventory(models.Model):
    store = models.ForeignKey(
        'Store',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        'Master.Product',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    inventory = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return "%s - %s(%s)"%(self.store.shop_name, self.product.name, self.inventory)

class StoreSale(models.Model):
    class PaymentMethodType(models.TextChoices):
        CASH = 'CS', _('Cash')
        CREDIT = 'CR', _('Credit')
        CARD = 'CD', _('Card')
        BHIMUPI = 'BH', _('BHIM UPI')
        PAYTM = 'PY', _('Paytm')
    id = models.CharField(max_length=10, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    store = models.ForeignKey(
        'Store',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    customer = models.ForeignKey(
        'StoreCustomer',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    invoice = models.CharField(max_length=40)
    mrp_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    special_price_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cart_discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paymentmethod = models.ForeignKey(
        'Master.TxnType',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    c_payment_method = models.CharField(max_length=20, null=True, default="")
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cess = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_gst = models.BooleanField(default=False)
    is_receipt_printed = models.BooleanField(default=False)
    status = models.ForeignKey(
        'Master.Status',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

class StoreCustomProduct(models.Model):
    id = models.CharField(max_length=20, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    store = models.ForeignKey(
        'Store',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=100)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category = models.ForeignKey(
        'Master.Category',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    brand = models.ForeignKey(
        'Master.Brand',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    linked_product = models.ForeignKey(
        'Master.Product',        
        models.SET_NULL,
        blank=True,
        null=True,
    )
    barcode = models.CharField(max_length=25, blank=True)
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cess = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    to_be_saved = models.BooleanField(default=False)
    uom = models.CharField(max_length=15, blank=True)
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return "%s (%s)"%(self.name, self.store.shop_name)

class StoreSaleItem(models.Model):
    id = models.CharField(max_length=10, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    is_custom_product = models.BooleanField(default=False)
    storesale = models.ForeignKey(
        'StoreSale',
        models.SET_NULL,
        related_name='saleitems',
        blank=True,
        null=True,
    )
    quantity = models.PositiveSmallIntegerField()
    is_refunded = models.BooleanField(default=False)
    product = models.ForeignKey(
        'Master.Product',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    cproduct = models.ForeignKey(
        'StoreCustomProduct',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    barcode = models.CharField(max_length=15, null=True)
    mrp_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sp_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    mrp_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sp_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cess = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    

class StoreCredit(models.Model):
    id = models.CharField(max_length=10, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    customer = models.ForeignKey(
        'StoreCustomer',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    storesale = models.ForeignKey(
        'StoreSale',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    paymentmethod = models.ForeignKey(
        'Master.TxnType',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()


class StoreRefund(models.Model):
    id = models.CharField(max_length=10, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    total_amount_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_quantity_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paymentmethod = models.ForeignKey(
        'Master.TxnType',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    storesale = models.ForeignKey(
        'StoreSale',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    is_receipt_printed = models.BooleanField(default=False)


class StoreRefundItem(models.Model):
    id = models.CharField(max_length=10, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    storesaleitem = models.ForeignKey(
        'StoreSaleItem',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    refund = models.ForeignKey(
        'StoreRefund',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    invoice = models.CharField(max_length=20, default="")
    quantity = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paymentmethod = models.ForeignKey(
        'Master.TxnType',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    



