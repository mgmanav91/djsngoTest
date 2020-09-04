from django.http import JsonResponse, HttpResponse
from Store.models import *
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt 
def sendOTP(request):
    if request.method == "POST":
        phone_number = request.POST['phone_number']
        # Send OTP, Setting it 1234
        store_obj = Store.objects.filter(registered_phone_number = phone_number)
        if not len(store_obj):
            return JsonResponse({'error_msg': "Not Registered"})
        store_obj.update(**{'otp': 1234})
        return JsonResponse({'status': 'success'})

@csrf_exempt
def login(request):
    if request.method == "POST":
        phone_number = request.POST['phone_number']
        otp = request.POST['otp']
        store_obj = Store.objects.filter(registered_phone_number = phone_number).values('otp', 'user__id',
            'shop_name', 'address', 'registered_phone_number', 'gst_number', 'is_gst_mandatory')
        if not len(store_obj):
            return JsonResponse({'error_msg': "Not Registered"})
        if store_obj[0]['otp'] == otp:
            store_obj = store_obj[0]
            print(store_obj['user__id'])
            authentication_token = Token.objects.get_or_create(user_id=store_obj['user__id'])[0].key
            #User.objects.filter(id = store_obj['user__id']).update(last_login = datetime.datetime.now())
            return JsonResponse({'store_name': store_obj['shop_name'],
                'store_sub_name': "Departmental Store",
                'store_address': store_obj['address'],
                'store_phone': store_obj['registered_phone_number'],
                'store_gst_number': store_obj['gst_number'],
                'store_registered_name': store_obj['shop_name'],
                'store_cin_no': "CIN Number",
                'authentication_token': authentication_token,
                'is_gst_mandatory': store_obj['is_gst_mandatory'],
                'status': 'success'
            })
        else:
            return HttpResponse(status=401)




