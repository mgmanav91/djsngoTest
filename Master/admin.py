from django.contrib.admin import ModelAdmin, register
from django.shortcuts import render, redirect
from django import forms
from import_export import resources, fields
from import_export.admin import ImportExportMixin
from simple_history.admin import SimpleHistoryAdmin
from import_export.widgets import ForeignKeyWidget
from .models import *
from express_stores.admin import admin_site

@register(Tax, site=admin_site)
class TaxAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'tax_name', 'gst_pct', 'cess_pct', 'created_at', 'updated_at')

@register(Status, site=admin_site)
class StatusAdmin(SimpleHistoryAdmin):
    list_display = ('alias', 'name', 'module')

@register(Location, site=admin_site)
class LocationAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'name', 'parent', 'created_at', 'updated_at')

class BrandResource(resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ForeignKeyWidget(Brand, 'id'))

    class Meta:
        model = Brand
        fields = ('id','name', 'parent',)

@register(Brand, site=admin_site)
class BrandAdmin(ImportExportMixin, SimpleHistoryAdmin):
    resource_class = BrandResource
    list_display = ('name', 'parent', 'created_at', 'updated_at')

class CategoryResource(resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ForeignKeyWidget(Category, 'id'))

    class Meta:
        model = Category
        fields = ('id','name', 'parent',)

@register(Category, site=admin_site)
class CategoryAdmin(ImportExportMixin, SimpleHistoryAdmin):
    resource_class = CategoryResource
    list_display = ('name', 'parent', 'created_at', 'updated_at')

class ProductResource(resources.ModelResource):
    brand = fields.Field(
        column_name='brand',
        attribute='brand',
        widget=ForeignKeyWidget(Brand, 'id'))
    tax = fields.Field(
        column_name='tax',
        attribute='tax',
        widget=ForeignKeyWidget(Tax, 'tax_name'))
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'id'))
    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'brand', 'article_code', 'hsn', 'is_barcode_available', 'images',
            'tax', 'size', 'color', 'flavour', 'uom')
        export_order = ['id', 'name', 'category', 'brand', 'article_code', 'hsn', 'is_barcode_available', 'images',
            'tax', 'size', 'color', 'flavour', 'uom']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = []
    barcode = forms.CharField()

    def save(self, commit=True):
        instance = super(ProductForm, self).save(commit=commit)
        instance.save()
        print(instance)
        print(instance.id)
        barcode = self.cleaned_data.get('barcode', None)
        if barcode and len(barcode):
            Barcodes.objects.create(barcode=barcode, product=instance)
        return instance

@register(Product, site=admin_site)
class ProductAdmin(ImportExportMixin, SimpleHistoryAdmin):
    resource_class = ProductResource
    search_fields = ('name', 'category__name', 'brand__name',)
    list_display = ('name', 'category', 'brand', 'is_barcode_available', 'created_at', 'updated_at')
    history_list_display = ['name', 'category', 'brand']
    form = ProductForm


    def response_change(self, request, obj):
        print(request.GET)
        print('stockrequestitem' in request.GET)
        if request.GET and 'stockrequestitem' in request.GET:
            print(request.GET['stockrequestitem'])
            from Stocks.models import StockRequestItem
            StockRequestItem.objects.filter(id=request.GET['stockrequestitem']).\
                    update(product_id = obj.id,
                            is_custom_product = False)
            return redirect('/admin/Stocks/stockrequestitem/?stockrequest__id__exact=' + 
                    StockRequestItem.objects.get(id=request.GET['stockrequestitem']).stockrequest.id)
        return super(ProductAdmin, self).response_change(request, obj)


class BarcodesResource(resources.ModelResource):
    barcodeproduct = fields.Field(
        column_name='product',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'id'))
    class Meta:
        model = Barcodes
        fields = ('id','barcode', 'barcodeproduct',)
        export_order = ['id','barcode', 'barcodeproduct',]


@register(Barcodes, site=admin_site)
class BarcodesAdmin(ImportExportMixin, SimpleHistoryAdmin):
    resource_class = BarcodesResource
    list_display = ('id', 'barcode', 'product')
    history_list_display = ('id', 'barcode', 'product__id', 'product__name')
    

class ProductDefaultPriceResource(resources.ModelResource):
    product = fields.Field(
        column_name='product',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'id'))
    location = fields.Field(
        column_name='location',
        attribute='location',
        widget=ForeignKeyWidget(Location, 'id'))
    class Meta:
        model = ProductDefaultPrice
        fields = ('id','product', 'location', 'mrp', 'sp',)
        export_order = ['id','product', 'location', 'mrp', 'sp']


@register(ProductDefaultPrice, site=admin_site)
class ProductDefaultPriceAdmin(ImportExportMixin, SimpleHistoryAdmin):
    resource_class = ProductDefaultPriceResource
    list_display = ('id', 'product', 'location', 'mrp', 'sp')
    history_list_display = ('id', 'product', 'location', 'mrp', 'sp')

