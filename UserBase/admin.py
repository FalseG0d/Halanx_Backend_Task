from django.contrib import admin
from django.contrib.admin.models import LogEntry

from Halanx.admin import halanx_admin, halanxhomes_admin
from UserBase.models import Picture, Customer, UserInterest, Education, UserLocation, Contact, SpamReport, Work, OTP, \
    EmailOTP


class PictureTabular(admin.TabularInline):
    model = Picture
    extra = 0
    ordering = ('-timestamp',)


@admin.register(Customer, site=halanxhomes_admin)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'phone_no', 'region', 'is_registered',
                    'get_profile_pic_html', 'profile_completion')
    search_fields = ('user__username', 'user__first_name')
    list_filter = ('region', 'is_registered', 'is_email_verified', 'last_visit', 'gender')
    ordering = ('-id',)
    readonly_fields = ('get_profile_pic_html',)
    raw_id_fields = ('user', 'referrer', 'user_interests', 'favorite_items', 'favorite_places', 'follows',
                     'followed_by')
    inlines = [
        PictureTabular,
    ]

    @staticmethod
    def username(obj):
        return str(obj.user.username)

    class Meta:
        model = Customer


@admin.register(
    OTP, site=halanx_admin)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('phone_no', 'password')
    search_fields = ('phone_no',)


@admin.register(EmailOTP, site=halanx_admin)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'password')
    search_fields = ('password',)



class UserInterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'priority')
    ordering = ('-priority',)

    class Meta:
        model = UserInterest


class EducationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'school')
    search_fields = ('customer__user__username',)

    class Meta:
        model = Education


class WorkAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'company')
    search_fields = ('customer__user__username',)

    class Meta:
        model = Work


class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'timestamp')
    search_fields = ('customer__user__username',)

    class Meta:
        model = UserLocation


class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'phone_no', 'name')
    search_fields = ('name', 'phone_no')
    raw_id_fields = ('customer',)

    class Meta:
        model = Contact

    @staticmethod
    def username(obj):
        return "{} {} [{}]".format(obj.customer.user.first_name, obj.customer.user.last_name, obj.customer.phone_no)


class MonitorLog(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'change_message', 'action_flag')
    list_filter = ('action_time', 'content_type')
    search_fields = ('user__username',)
    ordering = ('-action_time',)

    def has_delete_permission(self, request, obj=None):
        return False


class SpamReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'spammer', '_reporter')
    search_fields = ('customer__user__username', 'customer__phone_no')
    list_filter = ('verified',)

    class Meta:
        model = SpamReport

    @staticmethod
    def spammer(obj):
        return "{} {} [{}]".format(obj.customer.user.first_name, obj.customer.user.last_name, obj.customer.phone_no)

    @staticmethod
    def _reporter(obj):
        return "{} {} [{}]".format(obj.reporter.user.first_name, obj.reporter.user.last_name, obj.reporter.phone_no)


admin.site.register(LogEntry, MonitorLog)
halanx_admin.register(Customer, CustomerAdmin)
halanx_admin.register(UserInterest, UserInterestAdmin)
halanx_admin.register(Education, EducationAdmin)
halanx_admin.register(Work, WorkAdmin)
halanx_admin.register(Contact, ContactAdmin)
halanx_admin.register(UserLocation, UserLocationAdmin)
halanx_admin.register(SpamReport, SpamReportAdmin)
# admin.site.disable_action('delete_selected')
