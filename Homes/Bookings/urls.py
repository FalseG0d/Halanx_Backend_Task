from django.conf.urls import url
from Homes.Bookings.api import views

urlpatterns = (
    url(r'^$', views.BookingListCreateView.as_view()),
    url(r'^current/$', views.CurrentBookingRetrieveView.as_view()),
    url(r'complete/$', views.CompleteBookingsListView.as_view()),
    url(r'^(?P<pk>[0-9]+)/$', views.BookingDetailView.as_view()),

    # move in process
    url(r'^facilities/verify_assets/$', views.MoveInBookingFacilityQuantityAcknowledgementAPIView.as_view()),
    url(r'^upload_sign/$', views.BookingMoveInDigitalSignatureUploadView.as_view()),
    url(r'^rent_agreement/$', views.rent_agreement_for_current_booking_view),
    # move in process end

    url(r'^advance/$', views.AdvanceBookingListCreateView.as_view()),
    # url(r'^advance/(?P<pk>[0-9]+)/$', views.AdvanceBookingDetailView.as_view()),
)
