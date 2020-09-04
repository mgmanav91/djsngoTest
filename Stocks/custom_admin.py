from django.http import JsonResponse, HttpResponse
from decimal import Decimal
from Store.models import *
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt
from Stocks.models import *

@csrf_exempt
def StockItemStatus(request):
    data = request.POST
    print(data)
    if data['module'] == 'request_stock_item':
        StockRequestItem.objects.filter(id = data['id']).update(status_id=data['status'])
    elif data['module'] == 'request_stock':
        StockRequest.objects.filter(id = data['id']).update(status_id=data['status'])
    elif data['module'] == 'stock_transfer':
        PackageDispatcher.filter(id = data['id']).update(status_id=data['status'])

    return JsonResponse({'status': "Success", 'msg': "Status Updated !"})

@csrf_exempt
def StockItemChange(request):
    data = request.POST
    print(data)
    if len(list(set(['product_price', 'delivered_qty', 'accepted_qty']) - set([data['col']]))) != 3 \
            or [data['col']] == 'status':
        streq = StockRequestItem.objects.get(id = data['id'])
        setattr(streq, data['col'], Decimal(data['val']))
        streq.total_amount = round(Decimal(streq.delivered_qty) * Decimal(streq.product_price),2) \
                if streq.accepted_qty == 0 \
                else streq.accepted_qty * streq.product_price
        streq.save()
        acceptable_status = ["request_stock_item_confirmed",
                "request_stock_item_shipped", 
                "request_stock_item_delivered"]
        if streq.packageId and streq.status.name in acceptable_status:
            total_items = list(StockRequestItem.objects.filter(packageId_id = streq.packageId.id,
                status__name__in = acceptable_status)\
                        .values('product_price', 'delivered_qty', 'accepted_qty', 'status__name'))
            total_amount = sum(map(lambda x: x['product_price']*(\
                    x['delivered_qty'] if x['status__name'] != 'request_stock_item_delivered' \
                    else x['accepted_qty']), total_items))
            total_item_count = len(total_items)
            PackageDispatcher.objects.filter(id = streq.packageId.id).update(total_amount=total_amount,
                    total_items=total_item_count)
        return JsonResponse({'status': "Success",
            'msg': "%s and Total Amount Updated !"%(data['col'],),
            'total_amount': streq.total_amount})
    else:
        StockRequestItem.objects.filter(id = data['id']).update(**{data['col']:data['val']})
    return JsonResponse({'status': "Success", 'msg': "%s Updated !"%(data['col'],)})

