from django.contrib.admin import ModelAdmin, register
from django.contrib import messages
from django.forms import ModelForm
from django.db.models import Q
from import_export import resources
from import_export.admin import ImportExportMixin, ExportMixin
from simple_history.admin import SimpleHistoryAdmin
from django.utils.safestring import mark_safe
from .models import *
from django.urls import path
from django import forms
from django.shortcuts import render, redirect
from django.contrib.admin import AdminSite
from django.http import HttpResponse
from express_stores.admin import admin_site
from django.contrib.admin import SimpleListFilter
from Stocks.config import status_matrix

@register(StockRequest, site=admin_site)
class StockRequestAdmin(ModelAdmin):
    class Media:
        css = {
                'all': ('/static/custom_admin/admin.css',)
                }
        js = (
                '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
                '/static/custom_admin/request_stock.js'
                )
    list_filter = ('store',)
    list_display = ('store', 'get_status', 'client_created_at', 'updated_at', 'item_list')
    ordering = ('-client_created_at',)
    statuses = Status.objects.filter(module='request_stock').values('alias', 'id')

    def get_status(self, obj):
        return mark_safe("<select class='select_status' data-id='request_stock' id='" + obj.id + "'>" + 
                "".join(list(map(lambda x: \
                "<option value='" + str(x['id']) + "' " +
                ("selected" if obj.status and x['id'] == obj.status.id else "") + ">" +
                x['alias'] + "</option>", self.statuses))) + "</select>")
        get_status.short_description = 'Status'


    def item_list(self, obj):
        print(obj.id)
        print(obj.reqItems.values('product__name', 'requested_qty', 
            'is_custom_product', 'custom_product__name','status',))
        return mark_safe("<table><thead><tr><th>Product</th><th>Requested Qty</th><th>Status</th></tr></thead>" + 
            "<tbody>" + "".join(map(lambda x: "<tr><td>" + (x['product__name'] \
            if not x['is_custom_product'] and x['product__name'] else x['custom_product__name'] \
            if x['custom_product__name'] else "") + 
            ("<span class='tag-package tag tag-success'>Package</span>" if x['packageId__id'] \
                    else "") +
            "</td><td>" + (str(x['requested_qty']) if x['requested_qty'] else "") + 
            "</td><td>"+ (x['status__alias'] if x['status__alias'] else "Requested")  + "</td></tr>",
            obj.reqItems.values('product__name', 'requested_qty', 'is_custom_product', 'custom_product__name',
                'status__alias', 'packageId__id'))) + 
            "</tbody></table><br>"+
            "<a class='btn-info btn btn-round btn-sm float-xs-right' \
                    href='/admin/Stocks/stockrequestitem/?stockrequest__id__exact=" +
                    str(obj.id) + "'>Manage Items</a>") 
    item_list.short_description = 'Requested Items'

class PKForm(ModelForm):
    class Meta:
        model = StockRequestItem
        fields = ["id", "packageId", "product_price", "delivered_qty", "status"]

class RequestItemFilter(SimpleListFilter):
    title = 'Status'
    parameter_name = 'reqitem_status'
    
    def lookups(self, request, model_admin):
        return [(st.id, st.alias) for st in Status.objects.filter(module='request_stock_item')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status__id__exact=self.value())


@register(StockRequestItem, site=admin_site)
class StockRequestItemAdmin(ModelAdmin):
    class Media:
        css = {
                'all': ('/static/custom_admin/admin.css',)
                }
        js = (
            '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            '/static/custom_admin/request_stock.js'
        )
    change_list_template = 'admin/stocks_change_list.html'
    list_filter = ('stockrequest__store', 'is_custom_product', RequestItemFilter)
    search_filter = ('product__name', 'custom_product__name')
    list_display = ('get_store', 'get_product', 'requested_qty', 'select_package',
            'total_amount', 'accepted_qty', 'client_created_at', 'updated_at',)
    statuses = Status.objects.filter(module='request_stock_item').values('alias', 'id')
    ordering = ('-client_created_at',)
    actions = ['status_confirmed',
            'status_shipped',
            'status_delivered',
            'status_delivery_denied',
            'status_cancelled']

    def status_change(self, queryset, change_status):
        messages = {}
        allowed_status = status_matrix[change_status]
        denied_status = queryset.filter(~Q(status__name__in = allowed_status))
        rows_updated = queryset.filter(status__name__in = allowed_status).\
                update(status=Status.objects.get(name=change_status,
                    module='request_stock_item'))
        messages['success'] = "%s Items marked as Confirmed." % rows_updated
        if denied_status.count():
            messages['error'] = "%s Items status are not updated :<br>%s<br>\
                    <a href='/admin/Stocks/stockrequestitem/?id__in=%s'>Change manually</a>"%(denied_status.count(),
                            "<br>".join(map(lambda x: "%s - %s(already marked)"%(
                                x['product__name'] if x['product__name'] else x['custom_product__name'],
                                x['status__alias']),
                                denied_status.values('product__name', 'custom_product__name', 'status__alias'))),
                            ",".join(map(lambda x: str(x['id']), denied_status.values('id'))))
        return messages

    def status_confirmed(self, request, queryset):
        # Check if any custom product is not linked to barcode transferred to "Shipped" status
        # Check if Status is Placed or Confirmed but not Shipped and Above
        action_messages = self.status_change(queryset, 'request_stock_item_confirmed')
        self.message_user(request, action_messages['success'], level=messages.SUCCESS)
        if 'error' in action_messages.keys():
            self.message_user(request, mark_safe(action_messages['error']), level=messages.ERROR)
    status_confirmed.short_description = "Mark Items as Confirmed"

    def status_shipped(self, request, queryset):
        # Check if any custom product is not linked to a product before shipping
        # Check if Status is Placed or Confirmed but not Shipped and Above
        action_messages = self.status_change(queryset, 'request_stock_item_shipped')
        self.message_user(request, action_messages['success'], level=messages.SUCCESS)
        if 'error' in action_messages.keys():
            self.message_user(request, mark_safe(action_messages['error']), level=messages.ERROR)
    status_shipped.short_description = "Mark Items as Shipped"

    def status_delivered(self, request, queryset):
        # Check if any custom product is not linked to a product before shipping
        # Check if Status is Placed or Confirmed but not Shipped and Above
        action_messages = self.status_change(queryset, 'request_stock_item_delivered')
        self.message_user(request, action_messages['success'], level=messages.SUCCESS)
        if 'error' in action_messages.keys():
            self.message_user(request, mark_safe(action_messages['error']), level=messages.ERROR)
    status_delivered.short_description = "Mark Items as Delivered"
    
    def status_deliverydenied(self, request, queryset):
        # Check if any custom product is not linked to a product before shipping
        # Check if Status is Placed or Confirmed but not Shipped and Above
        action_messages = self.status_change(queryset, 'request_stock_item_deliverydenied')
        self.message_user(request, action_messages['success'], level=messages.SUCCESS)
        if 'error' in action_messages.keys():
            self.message_user(request, mark_safe(action_messages['error']), level=messages.ERROR)
    status_deliverydenied.short_description = "Mark Items as Delivery Denied"
    
    def status_cancelled(self, request, queryset):
        # Check if any custom product is not linked to a product before shipping
        # Check if Status is Placed or Confirmed but not Shipped and Above
        action_messages = self.status_change(queryset, 'request_stock_item_cancelled')
        self.message_user(request, action_messages['success'], level=messages.SUCCESS)
        if 'error' in action_messages.keys():
            self.message_user(request, mark_safe(action_messages['error']), level=messages.ERROR)
    status_cancelled.short_description = "Mark Items as Cancelled"

    def response_change(self, request, obj):
        return redirect(('/admin/Stocks/stockrequestitem/?stockrequest__id__exact=' + obj.stockrequest.id) \
                if obj.stockrequest else '/admin/Stocks/stockrequestitem/')

    def select_package(self, obj):
        pkform = PKForm(instance=obj)
        pkform.fields['id'].widget = forms.HiddenInput()
        print(obj.stockrequest)
        print(obj.stockrequest.store)
        print(PackageDispatcher.objects.filter(store=obj.stockrequest.store).values('status__name'))
        if obj.stockrequest:
            pkform.fields["packageId"].queryset = PackageDispatcher.objects.filter(store=obj.stockrequest.store,\
                    status__name__in = ["stock_transfer_pacakge_created", "stock_transfer_in_transit"])
            pkform.fields["status"].queryset = Status.objects.filter(module='request_stock_item')
        return mark_safe(pkform.as_p())
    select_package.short_description = 'Package'


    def delivered_quantity(self, obj):
        return mark_safe("<input type='text' class='edit_col' data-id='"+ obj.id +"'\
                 data-module='request_stock_item' \
                 data-col='delivered_qty' value='"+ (str(obj.delivered_qty) \
                 if obj.delivered_qty else '0') +"' />")
    delivered_quantity.short_description = 'Delivered Quantity'
    
    def get_store(self, obj):
        return obj.stockrequest.store.shop_name if obj.stockrequest and obj.stockrequest.store else ""
    get_store.short_description = 'Store'

    def get_status(self, obj):
        return mark_safe("<select class='select_status' data-id='request_stock_item' id='" + obj.id + "'>" + 
                "".join(list(map(lambda x: \
                "<option value='" + str(x['id']) + "' " + 
                ("selected" if obj.status and x['id'] == obj.status.id else "") + ">" + 
                x['alias'] + "</option>", self.statuses))) + "</select>")
    get_status.short_description = 'Status'

    def tracking_ids(self, obj):
        return mark_safe("<div class='center'><a href=''>Request ID: "+ str(obj.stockrequest.clientId) +"</a></div>"+
            "<div class='center'><a href=''>Dispatch ID: "+ str(obj.packageId) +"</a></div>")
    tracking_ids.short_description = 'IDs'
   
    def get_product(self, obj):
        product_html = "<h5>" + ( obj.product.name \
                if not obj.is_custom_product and obj.product \
                else (obj.custom_product.name + '<div><span class="tag tag-warning">Custom Product</span></div>') \
                if obj.custom_product else "-" ) + "</h5>"
        if obj.is_custom_product and obj.custom_product:
            if obj.custom_product.linked_product:
                product_html += "<div>Linked Product</div>\
                        <a href='/admin/Master/product/?id=%s'>%s</a>\
                        <a href='/admin/Store/storecustomproduct/?id=%s' \
                        class='btn btn-warning btn-round btn-sm float-xs-center'>Change Linked Product</a>\
                        <a href='/admin/Stocks/stockrequestitem/%s' \
                        class='btn btn-info btn-round btn-sm float-xs-center'>Change Product</a>"%(
                        obj.custom_product.linked_product.id,
                        obj.custom_product.linked_product.name,
                        obj.custom_product.linked_product.id,
                        obj.id)
            else:
                print(obj.custom_product.id)
                product_html += "<div class='red-text'>No Product Attached</div>\
                        <a href='/admin/Store/storecustomproduct/%s' \
                        class='btn btn-warning btn-round btn-sm float-xs-center'>Link To Product</a>\
                        <a href='/admin/Stocks/stockrequestitem/%s' \
                        class='btn btn-info btn-round btn-sm float-xs-center'>Change Product</a>\
                        <a href='/admin/Master/product/add/?stockrequestitem=%s' \
                        class='btn btn-success btn-round btn-sm float-xs-center'>Add New Product</a>"%(
                                obj.custom_product.id.replace("_", "_5F"),
                                obj.id.replace("_", "_5F"),
                                obj.id)
        else:
            product_html += "<a href='/admin/Stocks/stockrequestitem/%s' \
                    class='btn btn-info btn-round btn-sm float-xs-center'>Change Product</a>"%(obj.id,)
        return mark_safe(product_html)
    get_product.short_description = "Product"



class PackageDispatcherForm(ModelForm):
    class Meta:
        model = PackageDispatcher
        fields = ['store', 'delivered_at', 'total_amount']

class PackageFilter(SimpleListFilter):
    title = 'Status'
    parameter_name = 'pack_status'

    def lookups(self, request, model_admin):
        return [(st.id, st.alias) for st in Status.objects.filter(module='stock_transfer')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status__id__exact=self.value())


@register(PackageDispatcher, site=admin_site)
class PackageDispatcherAdmin(ModelAdmin):
    class Media:
        css = {
                'all': ('/static/custom_admin/admin.css',)
                }
        js = (
                '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
                '/static/custom_admin/request_stock.js'
                )
    change_list_template = 'admin/package_change_list.html'
    form = PackageDispatcherForm
    list_filter = ('store', PackageFilter)
    list_display = ('store', 'created_at', 'total_amount', 'get_status', 
            'updated_at', 'item_list', 'delivered_at', 'accepted_at')
    statuses = Status.objects.filter(module='stock_transfer').values('alias', 'id')

    def get_status(self, obj):
        return mark_safe("<select class='select_status' data-id='request_stock_item' id='" + str(obj.id) + "'>" +
                "".join(list(map(lambda x: \
                        "<option value='" + str(x['id']) + "' " +
                        ("selected" if obj.status and x['id'] == obj.status.id else "") + ">" +
                        x['alias'] + "</option>", self.statuses))) + "</select>")
    get_status.short_description = 'Status'

    def item_list(self, obj):
        return mark_safe("<table><thead><tr>\
                <th>Product</th>\
                <th>Requested Qty</th>\
                <th>Delivered Qty</th>\
                <th>Accepted Qty</th>\
                <th>Express Store SP</th>\
                <th>Total Amount</th>\
                <th>Status</th></tr></thead>" + 
            "<tbody>" + "".join(map(lambda x: "<tr><td>" + (x['product__name'] \
            if not x['is_custom_product'] and x['product__name'] else x['custom_product__name']) +
            "</td><td>" + str(x['requested_qty']) + "</td><td>"+ str(x['delivered_qty']) + "</td><td>" + 
            str(x['accepted_qty']) + "</td><td>" + str(x['product_price']) + "</td><td>" + 
            (str(x['total_amount']) if x['total_amount'] else "") + "</td><td>" + 
            (x['status__alias'] if x['status__alias'] else "") + 
            "</td></tr>",
            obj.packageReqItem.values('product__name', 'requested_qty', 'is_custom_product', 
                'custom_product__name','status__alias',
                'product_price', 'delivered_qty', 'accepted_qty', 'total_amount'))) +
            "</tbody></table>" + 
            "<a class='btn-info btn btn-round btn-sm float-xs-right' \
                    href='/admin/Stocks/stockrequestitem/?packageId__id__exact=" +
                    str(obj.id) + "'>Manage Items</a>")
    item_list.short_description = 'Dispatched Items'
