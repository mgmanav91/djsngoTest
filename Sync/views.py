from django.db.models import Q, F, Count, Sum
#from django.db import transaction
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from Master.models import *
from Store.models import *
from Stocks.models import *
from Sync.models import *
from Sync.utils import get_status

@api_view(['GET'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsAuthenticated])
def syncBackend(request):
    print(request.user)
    store = request.user.store
    # Updation Query Initialization
    upd_query = Q()
    last_sync_time = datetime.datetime(1991, 1, 1)
    newSync = False
    customProducts = []
    customers= []
    orders = []
    orderItems=[]
    refundItems = []
    creditLogs = []
    orderRefunds = []
    barcode_upd = []
    product_upd = []
    category_id = []
    requestStocks = []
    requestStockItems = []
    packageDispatches = []
    if 'get_all_data' in request.GET:
        last_sync_time = datetime.datetime(1991, 1, 1)
        print("\nNew Sync\n")
        newSync = True
    else:
        last_sync_time = StoreSync.objects.filter(store = store)
        if last_sync_time.count():
            last_sync_time = last_sync_time.latest('-created_at')
            print("\nLast Sync Time: ",last_sync_time)
            last_sync_time = last_sync_time.created_at
            upd_query = Q(updated_at__gte = last_sync_time)
    product_upd = StoreInventory.objects.filter(Q(store=store) & \
            Q(Q(product__brand__updated_at__gte = last_sync_time) |\
            Q(product__tax__updated_at__gte = last_sync_time) |\
            Q(updated_at__gte = last_sync_time))).\
            annotate(itemid=F('id'), name=F('product__name'), category_id=F('product__category_id'),
                    hsn = F('product__hsn'),
                    cess=F('product__tax__cess_pct'), cgst=F('product__tax__gst_pct')/2,
                    sgst=F('product__tax__gst_pct')/2, brand=F('product__brand__name'), uom=F('product__uom'),
                    is_barcode_available=F('product__is_barcode_available'), size=F('product__size'), color=F('product__color'))\
                            .values('product__id', 'name', 'itemid',
                                    'category_id', 'cess', 'cgst', 'sgst', 'brand', 'is_barcode_available',
                                    'mrp', 'sp', 'inventory', 'hsn', 'uom', 'size', 'color').annotate(id=F('product__id'))
    # Checking Tax, Products, Categories, Brand and Barcode Updation
    category_upd = list(StoreInventory.objects.filter(Q(store=store) & Q(product__category__updated_at__gte = last_sync_time)).distinct('product__category__id').\
            values('product__category__id', 'product__category__name',
                    'product__category__parent_id').\
                            annotate(id=F('product__category__id'), name=F('product__category__name'),
                                    parent_id=F('product__category__parent_id')).\
                                            values('id', 'name', 'parent_id'))
    cat_ids = list(map(lambda x: x['id'], category_upd))
    parent_cat_ids = list(map(lambda x: x['parent_id'], category_upd))
    while len(parent_cat_ids):
        temp_cat_data = Category.objects.filter(id__in = parent_cat_ids).distinct('id').values('id', 'name', 'parent_id')
        temp_cat_ids = list(set(map(lambda x: x['id'], temp_cat_data)) - set(cat_ids))
        category_upd.extend(filter(lambda x: x['id'] in temp_cat_ids, temp_cat_data))
        parent_cat_ids = list(map(lambda x: x['parent_id'], temp_cat_data))
        print("\nparent cat ids : \n",parent_cat_ids)
    category_upd = Category.objects.filter(Q(id__in = cat_ids) |\
            Q(child__id__in = cat_ids) |\
            Q(child__child__id__in = cat_ids) |\
            Q(child__child__child__id__in = cat_ids)).distinct('id').values('id', 'name', 'parent_id')
    barcode_upd = Barcodes.objects.filter(upd_query)\
        .annotate(product_name=F("product__name"))\
        .values("id", "barcode", "product_id", "product_name")
    print("\nproduct_upd :   \n",product_upd)
    print("\ncategory_upd: \n",category_upd)
    # Sync Orders Update
    if newSync:
        orders = list(map(lambda x: dict(x, **{'customer_id': x['customer_id'].split('_')[1] \
                if x['customer_id'] else None,
            'isGst': 1 if x['is_gst'] else 0,
            'is_receipt_printed': 1 if x['is_receipt_printed'] else 0}), 
            StoreSale.objects.filter(Q(store=store) & \
            Q(upd_query | Q(saleitems__updated_at__gte = last_sync_time))).\
            distinct('id').\
            annotate(sid=F('id'),
                sstatus=F('status'),
                spTotal=F('special_price_total'),
                payment_method=F('paymentmethod__name'),
                cart_total=F('mrp_total'),
                cc_at=F('created_at'),
                cu_at=F('updated_at')).\
            values('sid', 'clientId', 
                'store',
                'cc_at',
                'cu_at',
                'client_created_at',
                'client_updated_at',
                'customer_id',
                'invoice',
                'cart_total',
                'spTotal',
                'is_gst',
                'cart_discount_total',
                'paid_amount_total',
                'credit_amount',
                'payment_method',
                'cgst',
                'sgst',
                'cess',
                'is_receipt_printed',
                'sstatus',
                'status__name').\
            annotate(id=F('clientId'), status=F('status__name'),
                created_at=F('client_created_at'),
                updated_at=F('client_updated_at'))))
        orderItems = list(map(lambda x: dict(x, **{'order_id': x['order_id'].split('_')[1],
            'name': x['cproduct__name'] if x['cproduct__name'] else x['product__name'],
            'custom_product_id': x['custom_product_id'].split('_')[1] if x['custom_product_id'] else None}),
            StoreSaleItem.objects.filter(Q(storesale__store=store)).\
            annotate(sid=F('id'),
                    order_id=F('storesale_id'),
                    mrp=F('mrp_used'),
                    sp=F('sp_used'),
                    custom_product_id=F('cproduct_id')).\
            values('sid', 'clientId',
                    'order_id',
                    'mrp',
                    'sp',
                    'cgst',
                    'sgst',
                    'cess',
                    'quantity',
                    'barcode',
                    'custom_product_id',
                    'product_id',
                    'cproduct__name',
                    'product__name').\
            annotate(id=F('clientId'),)))
        # Customer Data
        customers = list(StoreCustomer.objects.filter(Q(store=store)).\
            annotate(sid=F('id')).\
            values(
            'clientId',
            'store',
            'name',
            'gender',
            'phone_number',
            'credit_balance',
            'total_orders',
            'total_spent',
            'average_spent',
            'total_discount',
            'avg_discount_per_order').\
            annotate(id=F('clientId')))
        customProducts = list(StoreCustomProduct.objects.filter(store=store).\
                annotate(sid=F('id')).\
                values(
                        'clientId',
                        'store',
                        'name',
                        'barcode',
                        'mrp',
                        'sp',
                        'cgst',
                        'sgst',
                        'cess',
                        'uom',
                        'to_be_saved').\
                annotate(id=F('clientId')))
        orderRefunds = list(map(lambda x: dict(x, **{'order_id': x['order_id'].split('_')[1],
            'is_receipt_printed': 1 if x['is_receipt_printed'] else 0}),
            StoreRefund.objects.filter(storesale__store=store).\
                        annotate(sid=F('id'),
                            order_id=F('storesale_id'),
                            payment_method=F('paymentmethod__name'),
                            cc_at=F('created_at'),
                            cu_at=F('updated_at')).\
                        values('sid',
                        'clientId',
                        'total_amount_refunded',
                        'total_quantity_refunded',
                        'paid_amount_total',
                        'payment_method',
                        'order_id',
                        'is_receipt_printed',
                        'cc_at',
                        'cu_at',
                        'client_created_at',
                        'client_updated_at').\
                        annotate(id=F('clientId'),
                            created_at=F('client_created_at'),
                            updated_at=F('client_updated_at'))))
        creditLogs = list(map(lambda x: dict(x, **{'order_id': x['order_id'].split('_')[1] if x['order_id'] else None,
            'customer_id': x['customer_id'].split('_')[1]}),
                StoreCredit.objects.filter(storesale__store=store).\
                annotate(sid=F('id'),
                    order_id=F('storesale_id'),
                    payment_method=F('paymentmethod__name'),
                    cc_at=F('created_at'),
                    cu_at=F('updated_at')).\
                values('sid',
                    'clientId',
                    'customer_id',
                    'order_id',
                    'payment_method',
                    'amount',
                    'cc_at',
                    'cu_at',
                    'client_created_at',
                    'client_updated_at').\
                annotate(id=F('clientId'),
                    created_at=F('client_created_at'),
                    updated_at=F('client_updated_at'))))
        refundItems = list(map(lambda x: dict(x, **{'orderItems_id': x['orderItems_id'].split('_')[1],
            'refund_id': x['refund_id'].split('_')[1]}),
            StoreRefundItem.objects.filter(storesaleitem__storesale__store=store).\
                annotate(sid=F('id'),
                        orderItems_id=F('storesaleitem_id'),
                        refund_qty=F('quantity'),
                        refunded_item_refund_amount=F('amount'),
                        cc_at=F('created_at'),                   
                        cu_at=F('updated_at')).\
                values('sid',
                        'clientId',
                        'orderItems_id',
                        'refund_id',
                        'refund_qty',
                        'refunded_item_refund_amount',
                        'cc_at',
                        'cu_at',
                        'client_created_at',
                        'client_updated_at',
                        'invoice').\
                annotate(id=F('clientId'),
                    created_at=F('client_created_at'),                  
                    updated_at=F('client_updated_at'))))
        
    # Request Stocks update
    print("\nupd_query :\n",upd_query)
    requestStocks = StockRequest.objects.filter(Q(store=store) & \
        Q(upd_query | Q(reqItems__updated_at__gte = last_sync_time)))\
        .annotate(sid=F('id'), sstatus=F('status'), cc_at=F('created_at'),
                cu_at=F('updated_at'),
                total_quantity=Sum('reqItems__requested_qty'))\
        .values("sid", 'clientId', 'status__name', 'sstatus', 'total_items', 'total_quantity',
        "cc_at", 'cu_at', "total_amount", "delivered_at", "accepted_at",
        'client_created_at', 'client_updated_at')\
        .annotate(id=F('clientId'),
                status=F('status__name'),
                created_at=F('client_created_at'),      
                updated_at=F('client_updated_at'))
    requestStockItems = list(map(lambda x: dict(x, **{'custom_product_id' : int(x['custom_product_id'].split('_')[1])\
                    if x['custom_product_id'] else None}),
        StockRequestItem.objects.filter(Q(stockrequest__store=store) & \
        upd_query)\
        .annotate(stock_request_id=F('stockrequest__clientId'), sid=F("id"), pkid=F('packageId'),
            cc_at=F('created_at'),
            cu_at=F('updated_at'))\
        .values("sid", "clientId", "total_amount", "product_id", "requested_qty", "delivered_qty", "accepted_qty", 
        "stock_request_id", "barcode", "is_custom_product", "custom_product_id", "cc_at", "cu_at", "note",
        "product_price", "pkid", 'client_created_at', 'client_updated_at')\
        .annotate(id=F('clientId'), packageId=F('pkid'),
            created_at=F('client_created_at'),               
            updated_at=F('client_updated_at'))))
    print("\n===============================")
    print("\nrequestStockItems : \n",requestStockItems)
    packageDispatches = []
    packageDispatches = PackageDispatcher.objects.filter(Q(store=store) & \
        Q(upd_query | Q(packageReqItem__updated_at__gte = last_sync_time)))\
        .annotate(sstatus=F('status'),
                cc_at=F('created_at'),           
                cu_at=F('updated_at'),
                total_quantity=Sum('packageReqItem__delivered_qty'))\
        .values("id",
                "cc_at", "cu_at",
                'client_created_at', 'client_updated_at',
                "sstatus", "total_amount", "delivered_at", "accepted_at",
        "status__name", "total_items", 'total_quantity')\
        .annotate(status=F('status__name'),
                created_at=F('client_created_at'),           
                updated_at=F('client_updated_at'))
    print("\n===============================")
    print("\npackageDispatches : \n",packageDispatches)
    StoreSync.objects.create(store = store)
    #print("\ncustomers : \n",customers)
    #print("\norders : \n",orders)
    #print("\norderItems : \n",orderItems)
    return Response({
        "customProducts": customProducts,
        "customers": customers,
        "orders": orders,
        "orderitems": orderItems,
        "refundItems": refundItems,
        "creditLogs": creditLogs,
        "orderRefunds": orderRefunds,
        "barcode": barcode_upd,
        "products": product_upd,
        "categories": category_upd,
        "requestStocks": requestStocks,
        "requestStockItems": requestStockItems,
        "packageDispatch": packageDispatches})


def formatCurrency(curr):
    return "{:.2f}".format(min(float(abs(curr)), 10000)) if curr and len(str(curr)) else 0


@api_view(['POST'])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsAuthenticated])
#@transaction.atomic
def syncClientData(request):
    store = request.user.store
    print("\nstore : \n",store)
    post_data = request.data
    print("\npost_data.keys : \n",post_data.keys())
    paymentMethods = {x['name']: x['id'] for x in TxnType.objects.all().values('id', 'name')}
    # If Custom Products present
    if 'customProducts' in post_data:
        for cpItems in post_data['customProducts']:
            print(cpItems)
            StoreCustomProduct.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                'id': "%s_%s"%(store.user_id, cpItems['id']),
                'clientId': int(cpItems['id']),
                'store': store,
                'name': cpItems['name'],
                'barcode': cpItems['barcode'][:15] if cpItems['barcode'] else "",
                'mrp': formatCurrency(cpItems['mrp']),
                'sp': formatCurrency(cpItems['sp']),
                'cgst': cpItems['cgst'],
                'sgst': cpItems['sgst'],
                'cess': cpItems['cess'],
                'uom': cpItems['uom'] if cpItems['uom'] else "",
                'to_be_saved': True if cpItems['to_be_saved'] == "true" else False
            })
    # if Customers present
    if 'customers' in post_data:
        for cpItems in post_data['customers']:
            StoreCustomer.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                'id': "%s_%s"%(store.user_id, cpItems['id']),
                'clientId': int(cpItems['id']),
                'store': store,
                'name': cpItems['name'],
                'gender': cpItems['gender'],
                'phone_number': cpItems['phone_number'],
                'credit_balance': cpItems['credit_balance'],
                'total_orders': cpItems['total_orders'],
                'total_spent': cpItems['total_spent'],
                'average_spent': cpItems['average_spent'],
                'total_discount': cpItems['total_discount'],
                'avg_discount_per_order': cpItems['avg_discount_per_order']
            })
    # if Orders present
    if 'orders' in post_data:
        statuses = list(map(lambda x: x['status'], post_data['orders']))
        db_statuses = get_status(statuses, 'order')
        for cpItems in post_data['orders']:
            print(cpItems)
            #status, created = Status.objects.get_or_create(name = cpItems['status'])
            StoreSale.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                'id': "%s_%s"%(store.user_id, cpItems['id']),
                'clientId': int(cpItems['id']),
                'store': store,
                'client_created_at': cpItems['created_at'],
                'client_updated_at': cpItems['updated_at'],
                'customer_id': "%s_%s"%(store.user_id, cpItems['customer_id']) \
                        if cpItems['customer_id'] != None else None,
                'invoice': cpItems['invoice'],
                'mrp_total': cpItems['cart_total'],
                'special_price_total': cpItems['spTotal'],
                'is_gst': True if cpItems['isGst'] == 1 else False,
                'cart_discount_total': formatCurrency(cpItems['cart_discount_total']),
                'paid_amount_total': formatCurrency(cpItems['paid_amount_total']),
                'credit_amount': cpItems['credit_amount'] if 'credit_amount' in cpItems else 0,
                'paymentmethod_id': paymentMethods[cpItems['payment_method']] if cpItems['payment_method'] else None,
                'cgst': cpItems['cgst'],
                'sgst': cpItems['sgst'],
                'cess': cpItems['cess'],
                'is_receipt_printed': cpItems['is_receipt_printed'],
                'status_id': db_statuses[cpItems['status']] if cpItems['status'] else None
            })
    # if Order Items present
    #if 1:#try:
    if 'orderItems' in post_data:
        product_mrp_sp = {y['product_id']: [y['mrp'], y['sp']] for y in \
                StoreInventory.objects.filter(product_id__in = map(lambda x: x['product_id'], post_data['orderItems']),
                    store=store).values('product_id', 'mrp', 'sp')}
        for cpItems in post_data['orderItems']:
            print(cpItems)
            StoreSaleItem.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                'id': "%s_%s"%(store.user_id, cpItems['id']),
                'clientId': int(cpItems['id']),
                'storesale_id': "%s_%s"%(store.user_id, cpItems['order_id']),
                'mrp_used': formatCurrency(cpItems['mrp']),
                'sp_used': formatCurrency(cpItems['sp']),
                'mrp_saved': product_mrp_sp[cpItems['product_id']][0] \
                        if cpItems['product_id'] and cpItems['product_id'] in product_mrp_sp.keys() \
                        else formatCurrency(cpItems['mrp']),
                'sp_saved': product_mrp_sp[cpItems['product_id']][1] \
                        if cpItems['product_id'] and cpItems['product_id'] in product_mrp_sp.keys() \
                        else formatCurrency(cpItems['sp']),
                'cgst': cpItems['cgst'] if cpItems['cgst'] != 'null' else 0,
                'sgst': cpItems['sgst'] if cpItems['cgst'] != 'null' else 0,
                'cess': cpItems['cess'] if cpItems['cgst'] != 'null' else 0,
                'quantity': cpItems['quantity'],
                'barcode': cpItems['barcode'],
                'is_custom_product': True if cpItems['custom_product_id'] != None else False,
                'cproduct_id': "%s_%s"%(store.user_id, cpItems['custom_product_id']) \
                        if cpItems['custom_product_id'] != None else None,
                'product_id': cpItems['product_id']
            })
    #except:
    #    print("Error")
    # if Request Stocks present
    if 'requestStocks' in post_data:
        print("\n=============== Request STocks ===============")
        print("\npost_data[requestStocks]\n",post_data['requestStocks'])
        statuses = list(map(lambda x: x['status'], post_data['requestStocks']))
        db_statuses = get_status(statuses, 'request_stock')
        for cpItems in post_data['requestStocks']:
            StockRequest.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                'id': "%s_%s"%(store.user_id, cpItems['id']),
                'clientId': int(cpItems['id']),
                'store': store,
                'client_created_at': cpItems['created_at'],
                'client_updated_at': cpItems['updated_at'],
                'total_items': cpItems['total_items'],
                'status_id': db_statuses[cpItems["status"]] if cpItems['status'] else None,
                'total_amount': cpItems['total_amount'],
                'delivered_at': cpItems['delivered_at'] \
                        if cpItems['delivered_at'] and len(cpItems['delivered_at']) > 0 else None,
                'accepted_at': cpItems['accepted_at'] \
                        if cpItems['accepted_at'] and len(cpItems['accepted_at']) > 0 else None
             })
    # if Package Dispatch present
    if 'packageDispatchList' in post_data and len(post_data['packageDispatchList']):
        print("\n=============== Packages ===============")
        print("\npost_data['packageDispatch']  :\n",post_data['packageDispatchList'])
        statuses = list(map(lambda x: x['status'], post_data['packageDispatchList']))
        db_statuses = get_status(statuses, 'stock_transfer')
        print(db_statuses)
        for cpItems in post_data['packageDispatchList']:
            PackageDispatcher.objects.update_or_create(id=int(cpItems['id']), defaults={
                'id': int(cpItems['id']),
                'store': store,
                'client_created_at': cpItems['created_at'],
                'client_updated_at': cpItems['updated_at'],
                'status_id': db_statuses[cpItems["status"]] if cpItems['status'] \
                        else None,
                'total_amount': cpItems['total_amount'],
                'total_items': cpItems['total_items'],
                'delivered_at': cpItems['delivered_at'] if cpItems['delivered_at'] else None,
                'accepted_at': cpItems['accepted_at'] if cpItems['accepted_at'] else None
            })
    # if Request Stock Items present
    if 1:#try:
      if 'requestStockItems' in post_data:
        for cpItems in post_data['requestStockItems']:
            print("\nif Request Stock Items present : cpItems : \n",cpItems)
            stk, created = StockRequestItem.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                'id': "%s_%s"%(store.user_id, cpItems['id']),
                'clientId': int(cpItems['id']),
                #'packageId_id': "%s_%s"%(store.user_id, cpItems['packageId']) if cpItems['packageId'] else None,
                'product_id': cpItems['product_id'] if cpItems['product_id'] else None,
                'requested_qty': cpItems['requested_qty'],
                'barcode': cpItems['barcode'],
                'custom_product_id': "%s_%s"%(store.user_id, cpItems['custom_product_id']) \
                        if cpItems['custom_product_id'] and isinstance(cpItems['custom_product_id'], int) \
                        else cpItems['custom_product_id'] \
                        if cpItems['custom_product_id'] and '_' in cpItems['custom_product_id'] \
                        else None,
                'is_custom_product': False if cpItems['product_id'] else True,
                'stockrequest_id': "%s_%s"%(store.user_id, cpItems['stock_request_id']),
                #'delivered_qty': cpItems['delivered_qty'],
                'accepted_qty': cpItems['accepted_qty'],
                'client_created_at': cpItems['created_at'],
                'client_updated_at': cpItems['updated_at'],
                'note': cpItems['note'],
                #'product_price': cpItems['product_price']
            })
            if cpItems['packageId']:
                try:
                    stk.packageId_id = "%s_%s"%(store.user_id, cpItems['packageId'])
                    stk.save()
                except:
                    print("Error")

    #except:
    #  print("Error")
    # if CreditLogs present
    if 'creditLogs' in post_data:
        for cpItems in post_data['creditLogs']:
            StoreCredit.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                'id': "%s_%s"%(store.user_id, cpItems['id']),
                'clientId': int(cpItems['id']),
                'customer_id': "%s_%s"%(store.user_id, cpItems['customer_id']),
                'storesale_id': "%s_%s"%(store.user_id, cpItems['order_id']) \
                        if cpItems['order_id'] and cpItems['order_id'] != 0 else None,
                'amount': cpItems['amount'],
                'paymentmethod_id': paymentMethods[cpItems['payment_method']] if cpItems['payment_method'] else None,
                'client_created_at': cpItems['created_at'],
                'client_updated_at': cpItems['updated_at']
            })
    # if orderRefunds is present
    if 'orderRefundList' in post_data:
        print("\nStore Refunds -------------------------")
        print("\npost_data['orderRefundList'] : \n",post_data['orderRefundList'])
        for cpItems in post_data['orderRefundList']:
            StoreRefund.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                'id': "%s_%s"%(store.user_id, cpItems['id']),
                'clientId': int(cpItems['id']),
                'total_amount_refunded': cpItems['total_amount_refunded'],
                'total_quantity_refunded': cpItems['total_quantity_refunded'],
                'paid_amount_total': cpItems['paid_amount_total'],
                'paymentmethod_id': paymentMethods[cpItems['payment_method']] if cpItems['payment_method'] else None,
                'storesale_id': "%s_%s"%(store.user_id, cpItems['order_id']),
                'is_receipt_printed': cpItems['is_receipt_printed'],
                'client_created_at': cpItems['created_at'],
                'client_updated_at': cpItems['updated_at']
            })
     # if Refund Items present
    if 'refund_items' in post_data:
        for cpItems in post_data['refund_items']:
            try:
                StoreRefundItem.objects.update_or_create(id='%s_%s'%(store.user_id, cpItems['id']), defaults={
                    'id': "%s_%s"%(store.user_id, cpItems['id']),
                    'clientId': int(cpItems['id']),
                    'storesaleitem_id': "%s_%s"%(store.user_id, cpItems['orderItems_id']),
                    'refund_id': "%s_%s"%(store.user_id, cpItems['refund_id']),
                    'quantity': cpItems['refund_qty'],
                    'amount': cpItems['refunded_item_refund_amount'],
                    'client_created_at': cpItems['created_at'],
                    'client_updated_at': cpItems['updated_at'],
                    'invoice': cpItems['order_id']
                    })
            except:
                print("\nif Refund Items present : cpItems : \n",cpItems)
    return Response({'status': "success"})

