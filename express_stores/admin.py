from django.contrib.admin import AdminSite
from .forms import PackageForm
from django.shortcuts import render, redirect
from django.contrib import admin
import csv
import time

current_milli_time = lambda: int(round(time.time() * 1000))


class MyAdminSite(AdminSite):
    site_header = 'Express Stores - Admin'

    def create_package(self, request):
        if request.method == "POST":
            print(request.POST)
            csv_file = request.FILES["import_file"]
            store = request.POST['store']
            print(csv_file)
            csv_content = csv_file.read().decode("utf-8").split("\n")
            print(csv_content)
            csv_headers = csv_content[0].split(",")
            valid_headers = ['product', 'barcode', 'quantity', 'unit_price']
            if len(set(valid_headers) - set(csv_headers)):
                return render(
                        request,
                        template_name="admin/csv_form.html",
                        context=dict(
                            self.each_context(request),                        
                            form=form,
                            error="Missing Header :" + ", ".join(list(set(valid_headers) - set(csv_headers))))
                        )
            csv_headers = {csv_headers[i]: i for i in range(0, len(csv_headers))}
            # Validating Values
            error = ""
            for row in csv_content:
                items = row.split(",")
                if (not (items[csv_headers['product']] and item[csv_headers['product']] !="") \
                        and not (items[csv_headers['barcode']] and item[csv_headers['barcode']] !="")):
                    error += "\nMissing both Product ID and Barcode : " + ", ".join(items)
                if not (items[csv_headers['quantity']] and item[csv_headers['quantity']] !=""):
                    error += "\nMissing Quantity : " + ", ".join(items)
                if not (items[csv_headers['unit_price']] and item[csv_headers['unit_price']] !=""):
                    error += "\nMissing Unit Price : " + ", ".join(items)
            if len(error) !=0:
                return render(
                        request,
                        template_name="admin/csv_form.html",
                        context=dict(
                            self.each_context(request),
                            form=form,
                            error=error))
            product_items = list(set(map(lambda x: x.split(",")[csv_headers['product']], csv_content)) - set([None,]))
            barcode_items = list(set(map(lambda x: x.split(",")[csv_headers['barcode']], csv_content)) - set([None,]))
            barcode_product_items = {x['barcode']: x['product_id'] for x in \
                    Barcodes.objects.filter(barcode__in = barcode_items).values('product_id', 'barcode')}
            barcode_custom_items = {x['barcode']: x['id'] for x in \
                    StoreCustomProduct.objects.filter(barcode__in = barcode_items,
                        store=store).values('id', 'barcode')}
            pck_client_id = int(packageDispatch.objects.filter(store=store).\
                    aggregate(Max('clientId'))['clientId__max']) + 1
            created, status = Status.objects.get_or_create(name="stock_transfer_pacakge_created",
                    module="stock_transfer", defaults={'alias':"Package Created"})
            packageDispatch = PackageDispatcher.objects.create(id="%s_%s"%(store.user_id, pck_client_id),
                    clientId=pck_client_id,
                    store=store,
                    status=status
                    )
            requestStockItems = StockRequestItem.objects.filter(packageId__isnull=True,
                    status__name="request_stock_item_confirmed").values('id',
                            'product_id',
                            'cproduct_id',
                            'barcode',
                            'requested_qty').order_by('id')
            status_stockitem_confirmed, created = Status.objects.get_or_create(name = 'request_stock_item_confirmed',
                    module='request_stock_item',
                    defaults={'alias': 'Confirmed'})
            new_requeststock = False
            new_requeststockItems = []
            total_amount = 0
            total_items = 0
            for row in csv_content:
                product_id = None
                cproduct_id = None
                # If Barcode Present
                if row[csv_headers['barcode']] and len(row[csv_headers['barcode']]) != 0:
                    # Check Barcode in Master Table
                    if row[csv_headers['barcode']] in barcode_product_items.keys():
                        product_id = barcode_product_items[row[csv_headers['barcode']]]
                    # Check Barcode in Store Custom Products
                    elif row[csv_headers['barcode']] in barcode_custom_items.keys():
                        cproduct_id = barcode_custom_items[row[csv_headers['barcode']]]
                elif row[csv_headers['product']] and len(row[csv_headers['product']]) != 0:
                    # If Product ID is present
                    product_id = row[csv_headers['product']]
                # FIFO 
                stockItems = list(filter(lambda x: x['product_id'] == product_id if product_id \
                        else x['cproduct_id'] if x['cproduct_id'] == cproduct_id else False, requestStockItems))
                if len(stockItems):
                    # Check if 
                    remaining_qty = row[csv_headers['quantity']]
                    while remaining_qty != 0 and len(stockItems):
                        # If StockItem requested quantity is greater than remaining qty 
                        if stockItems[0]['requested_qty'] > remaining_qty:
                            delivered_qty = remaining_qty
                            remaining_qty = 0
                        # If Remaining Qty > StockItem Requested Qty
                        else:
                            delivered_qty = stockItems[0]['requested_qty']
                            remaining_qty -= stockItems[0]['requested_qty']
                        StockRequestItem.objects.filter(id = stockItems[0]['id']).\
                                update(delivered_qty = delivered_qty,
                                        packageId = packageDispatch)
                        del stockItems[0]
                    # If Quantity Delivered is more than Requested Quantity => Create New StockRequest
                    if remaining_qty != 0 and len(stockItems) == 0:
                        new_requeststock = True
                        new_requeststockItemsID = current_milli_time()
                        cu_date = datetime.now()
                        new_requeststockItems.append(
                                StockRequestItem.objects.create(id = "%s_%s"%(store, new_requeststockItemsID),
                                    clientID = new_requeststockItemsID,
                                    packageId = packageDispatch,
                                    delivered_qty = remaining_qty,
                                    product_id = product_id if product_id else None,
                                    is_custom_product = False if product_id else True,
                                    cproduct_id = cproduct_id if cproduct_id else None,
                                    product_price = row[csv_headers['unit_price']],
                                    status = status_stockitem_confirmed,
                                    total_amount = row[csv_headers['unit_price']] * remaining_qty,
                                    created_at = cu_date,
                                    updated_at = cu_date,
                                    client_created_at = cu_date,
                                    client_updated_at = cu_date,
                                    ))

            return redirect('/admin/Stocks/packagedispatcher/?id=' + packageDispatch.id)

        form = PackageForm()
        return render(
            request,
            template_name="admin/csv_form.html",
            context=dict(
                    self.each_context(request),
                    form=form)
                )

    def get_urls(self):
        from django.conf.urls import url
        urls = super(MyAdminSite, self).get_urls()
        urls += [
                url(r'^createPackage/$', self.admin_view(self.create_package))
                ]
        return urls


admin_site = MyAdminSite(name='exps_admin')
