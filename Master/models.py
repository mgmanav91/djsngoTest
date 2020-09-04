from django.utils.translation import gettext_lazy as _
from django.db import models
from simple_history.models import HistoricalRecords


class ProductFieldType(models.Model):
    class FieldType(models.TextChoices):
        INT = 'I', _('Integer')
        DECIMAL = 'D', _('Decimal / Float')
        STRING = 'S', _('String(<50 characters)')
        TEXT = 'T', _('Text')
    field_name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=150)
    field_type = models.CharField(
        max_length=2,
        choices=FieldType.choices,
        default=FieldType.STRING,
    )


class Status(models.Model):
    class Meta():
        index_together = [['name']]
    name = models.CharField(max_length=50)
    alias = models.CharField(max_length=50)
    module = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.alias

class TxnType(models.Model):
    name = models.CharField(max_length=50)
    alias = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.alias

class Tax(models.Model):
    tax_name = models.CharField(max_length=100)
    gst_pct = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    cess_pct = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

class Location(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'Location',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
       return '%s %s'%(self.name, "(%s)"%self.parent.name if self.parent else "")

class Brand(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'Brand',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
       return '%s %s'%(self.name, "(%s)"%self.parent.name if self.parent else "")

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'Category',
	models.SET_NULL,
        related_name='child',
	blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
       return '%s %s'%(self.name, "(%s)"%self.parent.name if self.parent else "")

class ProductFieldCategoryRelationship(models.Model):
    category = models.ForeignKey(
        'Category',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    product_field_type = models.ForeignKey(
        'ProductFieldType',
        models.SET_NULL,
        blank=True,
        null=True,
    )

class ProductGroup(models.Model):
    name = models.CharField(max_length=100)

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        'Category',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    brand = models.ForeignKey(
        'Brand',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    product_group = models.ForeignKey(
        'ProductGroup',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    article_code = models.CharField(max_length=100, blank=True)
    hsn = models.CharField(max_length=100, blank=True)
    is_barcode_available = models.BooleanField(default=True)
    images = models.TextField(default='default.png')
    tax = models.ForeignKey(
        'Tax',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    size = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=20, blank=True)
    flavour = models.CharField(max_length=20, blank=True)
    uom = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
       return self.name


class ProductFieldCategoryRelationship(models.Model):
    product_field_type = models.ForeignKey(
        'ProductFieldType',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    product = models.ForeignKey(
        'Product',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    product_field_value = models.CharField(max_length=100)



class Barcodes(models.Model):
    id = models.AutoField(primary_key=True)
    barcode = models.CharField(max_length=15)
    product = models.ForeignKey(
        'Product',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()


class ProductDefaultPrice(models.Model):
    product = models.ForeignKey(
        'Product',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    location = models.ForeignKey(
        'Location',
        models.SET_NULL,
        blank=True,
        null=True,
    )
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()



