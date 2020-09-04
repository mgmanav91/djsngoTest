from django.utils.translation import gettext_lazy as _
from django.db import models
from simple_history.models import HistoricalRecords
from Master.models import *
from Store.models import *


class StockRequest(models.Model):
    id = models.CharField(max_length=10, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    store = models.ForeignKey(
        'Store.Store',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True)
    accepted_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    total_items = models.PositiveSmallIntegerField()
    status = models.ForeignKey(
        'Master.Status',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    cstatus = models.CharField(max_length=20, default="")
    history = HistoricalRecords()


class PackageDispatcher(models.Model):
    id = models.AutoField(primary_key=True)
    store = models.ForeignKey(
        'Store.Store',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    total_items = models.PositiveSmallIntegerField(default=0)
    status = models.ForeignKey(
        'Master.Status',
        models.SET_NULL,
        default=Status.objects.get(name= 'stock_transfer_pacakge_created').id,
        blank=True,
        null=True,
    )
    cstatus = models.CharField(max_length=10, default="", blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return "%s - Rs. %s (%s)"%(self.store.shop_name if self.store else "-",
                self.total_amount,
                self.delivered_at.strftime("%d/%m/%Y %H:%M"))



class StockRequestItem(models.Model):
    id = models.CharField(max_length=10, primary_key=True, default=pkgen)
    clientId = models.IntegerField(db_index=True)
    packageId = models.ForeignKey(
        'PackageDispatcher',
        models.SET_NULL,
        related_name='packageReqItem',
        blank=True,
        null=True,
    )
    stockrequest = models.ForeignKey(
        'StockRequest',
        models.SET_NULL,
        related_name='reqItems',
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        'Master.Product',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    requested_qty = models.PositiveSmallIntegerField()
    delivered_qty = models.PositiveSmallIntegerField(default=4)
    accepted_qty = models.PositiveSmallIntegerField()
    barcode = models.CharField(max_length=15, blank=True)
    cost_price_excl_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    igst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cess = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    note = models.TextField(null=True, blank=True)
    ex_sp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_custom_product = models.BooleanField(default=False)
    custom_product = models.ForeignKey(
        'Store.StoreCustomProduct',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    client_created_at = models.DateTimeField(null=True)
    client_updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.ForeignKey(
        'Master.Status',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    history = HistoricalRecords()
    


