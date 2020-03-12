from django.conf.urls import url

from Transaction import views

urlpatterns = [
    url(r'^payu/generate_hash/web/$', views.generate_payu_hash_view_web),
    url(r'^payu/generate_hash/android/(?P<pk>[0-9]+)/$', views.generate_payu_hash_view_android),
    url(r'^paytm/generate_hash/android/$', views.generate_paytm_hash_view_android),

    # RazorPay
    url(r'razorpay/generate_orderid/android/$', views.generate_razorpay_orderid_view_android),
]
