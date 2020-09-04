from django.contrib.admin import ModelAdmin, register, RelatedOnlyFieldListFilter
from django import forms
from pytz import timezone
from import_export import resources, fields
from import_export.admin import ImportExportMixin
from import_export.widgets import ForeignKeyWidget
from simple_history.admin import SimpleHistoryAdmin
from django.utils.safestring import mark_safe
from .models import *
from express_stores.admin import admin_site

class StoreResource(resources.ModelResource):
    location = fields.Field(
        column_name='location',
        attribute='location',
        widget=ForeignKeyWidget(Location, 'id'))
    store_id = fields.Field(
        column_name='id',
        attribute='id',
        widget=ForeignKeyWidget(User, 'id'))
    class Meta:
        model = Store
        fields = ('store_id','shop_name', 'registered_phone_number', 'address', 'geolocation', 'location', 'is_gst_mandatory')
        #exclude = ('id',)
        #import_id_fields = ('product', 'store')
        export_order = ('store_id','shop_name', 'registered_phone_number', 'address', 'geolocation', 'location', 'is_gst_mandatory')

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['shop_name', 'registered_phone_number', 'location', 'address', 'geolocation',
            'model_type', 'is_gst_mandatory', 'gst_number']

@register(Store, site=admin_site)
class StoreAdmin(ImportExportMixin, SimpleHistoryAdmin):
    resource_class = StoreResource
    search_fields =  ('shop_name', 'registered_phone_number')
    list_display = ('shop_name', 'registered_phone_number', 'location', 'is_gst_mandatory', 'created_at', 'updated_at')
    form = StoreForm


@register(StoreCustomer, site=admin_site)
class StoreCustomerAdmin(ModelAdmin):
    search_fields =  ('name', 'phone_number')
    list_filter = ('store',)
    list_display = ('name', 'phone_number', 'gender', 'store', 'credit_balance', 'created_at')

@register(StoreCustomProduct, site=admin_site)
class StoreCustomProductAdmin(ModelAdmin):
    search_fields =  ('name', 'barcode')
    list_filter = ('store',
            ('brand', RelatedOnlyFieldListFilter),
            ('category', RelatedOnlyFieldListFilter))
    list_display = ('name', 'barcode', 'brand', 'category')

    def response_add(self, request, obj):
        print(request.GET)
        print(request.META['HTTP_REFERER'])
        print('stockrequestitem' in request.GET)
        if request.GET and 'stockrequestitem' in request.GET:
            print(request.GET['stockrequestitem'])
            return redirect('/admin/Stocks/stockrequestitem/?stockrequest__id__exact=' +
                    StockRequestItem.objects.get(id=request.GET['stockrequestitem']).stockrequest.id)
        return super(StoreCustomProductAdmin, self).response_add(request, obj)


class StoreInventoryResource(resources.ModelResource):
    product = fields.Field(
        column_name='product',
        attribute='product',
        widget=ForeignKeyWidget(Product, 'id'))
    store = fields.Field(
        column_name='store',
        attribute='store',
        widget=ForeignKeyWidget(Store, 'user__id'))
    class Meta:
        model = StoreInventory
        fields = ('id','product', 'store', 'mrp', 'sp', 'inventory')
        #exclude = ('id',)
        #import_id_fields = ('product', 'store')
        export_order = ('id', 'product', 'store', 'mrp', 'sp', 'inventory')

    def before_save_instance(self, instance, using_transactions, dry_run):
        saved_price_vals = ProductDefaultPrice.objects.filter(product_id = instance.product__id).values('mrp', 'sp') \
            if instance.mrp == "" or instance.sp == "" else []
        if len(saved_price_vals):
            saved_price_vals = saved_price_vals[0]
            if instance.mrp == "":
                instance.mrp = saved_price_vals['mrp']
            if instance.sp == "":
                instance.sp = saved_price_vals['sp']
        return instance

@register(StoreInventory, site=admin_site)
class StoreInventoryAdmin(ImportExportMixin, SimpleHistoryAdmin):
    resource_class = StoreInventoryResource
    search_fields =  ('product',)
    list_filter = ('store',)
    list_display = ('id', 'product', 'store', 'mrp', 'sp', 'inventory', 'created_at', 'updated_at')
    export_order = ('id', 'product', 'store', 'mrp', 'sp', 'inventory')

@register(StoreSale, site=admin_site)
class StoreSaleAdmin(ModelAdmin):
    class Media:
        css = {
                'all': ('/static/custom_admin/admin.css',)
                }
    search_fields =  ('customer__name', 'customer__phone_number', 'invoice')
    list_filter = ('store', 'paymentmethod', 'is_gst')
    list_display = ('store', 'customer', 'invoice', 'items', 'txn_amount', 'paymentmethod', 'order_time')
    ordering = ('-client_created_at',)

    def order_time(self, obj):
        print(obj.client_created_at)
        print(obj.client_created_at.astimezone(timezone('Asia/Kolkata')))
        return obj.client_created_at.astimezone(timezone('Asia/Kolkata'))
    order_time.short_description = 'Order Time'

    def txn_amount(self, obj):
        amt_html = "<div class='badge-container'><span class='badge'>GST</span></div>" if obj.is_gst else ""
        amt_html += "<table class='inline-table'><thead><tr><th></th><th>Rs.</th></thead><tbody>\
                <tr><td>SP Total</td><td>" + str(obj.special_price_total) + "</td></tr>\
                <tr><td>MRP Total</td><td>" + str(obj.mrp_total) + "</td></tr>" + \
                (("<tr><td>SGST</td><td>" + str(obj.sgst) + "</td></tr>" +
                        "<tr><td>CGST</td><td>" + str(obj.cgst) + "</td></tr>" +
                        "<tr><td>CESS</td><td>" + str(obj.cess) + "</td></tr>") if obj.is_gst else "") + \
                "<tr><td>Discount</td><td>" + str(obj.cart_discount_total) + "</td></tr>\
                <tr><td>Paid Amount</td><td>" + str(obj.paid_amount_total) + "</td></tr>" +\
                ("<tr><td>Credit</td><td>" + str(obj.credit_amount) + "</td></tr>" \
                if obj.credit_amount != 0 else "") + \
                "</tbody></table>"
        return mark_safe(amt_html)
    txn_amount.short_description = 'Txn Details'


    def items(self, obj):
        return mark_safe("<table><thead><tr><th>Product</th><th>Qty</th><th>MRP</th><th>SP</th></tr></thead><tbody>" + 
                " ".join(["<tr><td>%s</td><td>%s</td><td>Used: %s<br>Saved: %s</td><td>Used: %s<br>Saved: %s</td></tr>"%(
                        item.product.name if item.product else item.cproduct.name,
                        item.quantity,
                        item.mrp_used,
                        item.mrp_saved,
                        item.sp_used,
                        item.sp_saved) for item in obj.saleitems.all()]) + 
                #"<table><thead><tr><th>Product</th><th>Qty</th><th>MRP</th><th>SP</th></tr></thead><tbody>" +
                #" ".join(["<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(item.name,
                #item.quantity, item.mrp, item.sp) for item in obj.salecustomitems.all() ]) +
                "</tbody></table>")
    items.short_description = 'Items'





