from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Member, Income, Expense, CompanyBalance, Gallery, 
    ExecutiveCouncil, FormUpload, SecretaryAdmin
)


class CertificateStatusFilter(admin.SimpleListFilter):
    """Custom filter for certificate status"""
    title = 'Certificate Status'
    parameter_name = 'certificate_status'
    
    def lookups(self, request, model_admin):
        return (
            ('expired', 'Expired'),
            ('expiring', 'Expiring Soon'),
            ('valid', 'Valid'),
            ('no_date', 'No Expiry Date'),
        )
    
    def queryset(self, request, queryset):
        today = timezone.now().date()
        
        if self.value() == 'expired':
            return queryset.filter(
                certificate_expiry_date__lt=today
            ).exclude(certificate_expiry_date__isnull=True)
        elif self.value() == 'expiring':
            from datetime import timedelta
            expiry_threshold = today + timedelta(days=30)
            return queryset.filter(
                certificate_expiry_date__gte=today,
                certificate_expiry_date__lte=expiry_threshold
            )
        elif self.value() == 'valid':
            from datetime import timedelta
            expiry_threshold = today + timedelta(days=30)
            return queryset.filter(
                certificate_expiry_date__gt=expiry_threshold
            )
        elif self.value() == 'no_date':
            return queryset.filter(certificate_expiry_date__isnull=True)
        return queryset


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        'company_name', 'company_category', 'rc_no', 'certificate_status_badge',
        'days_until_expiry_display', 'last_renewal_date', 'renewal_count', 'created_at'
    ]
    list_filter = [
        'company_category', CertificateStatusFilter, 'last_renewal_date',
        'national_first_registered', 'enugu_first_registered', 'created_at'
    ]
    search_fields = [
        'company_name', 'rc_no', 'company_email', 'address', 'md_phone_number'
    ]
    readonly_fields = [
        'certificate_status_badge', 'days_until_expiry_display', 'new_expiry_date',
        'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Company Information', {
            'fields': (
                'company_name', 'company_email', 'company_category', 
                'address', 'rc_no', 'md_phone_number'
            )
        }),
        ('Media', {
            'fields': ('md_picture', 'certificate_picture'),
            'classes': ('collapse',)
        }),
        ('National Membership', {
            'fields': ('national_first_registered',)
        }),
        ('Certificate Information', {
            'fields': (
                'certificate_issued_date', 'certificate_expiry_date',
                'certificate_status_badge', 'days_until_expiry_display', 'new_expiry_date'
            )
        }),
        ('Renewal Information', {
            'fields': ('last_renewal_date', 'renewal_count')
        }),
        ('Enugu Membership', {
            'fields': ('enugu_first_registered',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['renew_certificates', 'mark_as_expired']
    
    def certificate_status_badge(self, obj):
        """Display certificate status with colored badge"""
        status = obj.certificate_status_display
        color_map = {
            'Expired': 'red',
            'Expiring Soon': 'orange',
            'Valid': 'green',
            'No Expiry Date': 'gray'
        }
        color = color_map.get(status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    certificate_status_badge.short_description = 'Certificate Status'
    
    def renew_certificates(self, request, queryset):
        """Admin action to renew certificates"""
        renewed_count = 0
        for member in queryset:
            if member.can_renew_certificate and member.renew_certificate():
                renewed_count += 1
        
        self.message_user(
            request,
            f"Successfully renewed {renewed_count} certificates."
        )
    renew_certificates.short_description = "Renew selected certificates"
    
    def mark_as_expired(self, request, queryset):
        """Admin action to mark certificates as expired (for testing)"""
        from datetime import date
        queryset.update(certificate_expiry_date=date.today())
        self.message_user(request, "Marked selected certificates as expired.")
    mark_as_expired.short_description = "Mark as expired (for testing)"


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount_display', 'date', 'description_short', 'created_at']
    list_filter = ['category', 'date', 'created_at']
    search_fields = ['description', 'amount']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Income Details', {
            'fields': ('category', 'amount', 'date', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def amount_display(self, obj):
        """Display amount with currency formatting"""
        return f"₦{obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def description_short(self, obj):
        """Display truncated description"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount_display', 'date', 'description_short', 'created_at']
    list_filter = ['category', 'date', 'created_at']
    search_fields = ['description', 'amount']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Expense Details', {
            'fields': ('category', 'amount', 'date', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def amount_display(self, obj):
        """Display amount with currency formatting"""
        return f"₦{obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def description_short(self, obj):
        """Display truncated description"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'


@admin.register(CompanyBalance)
class CompanyBalanceAdmin(admin.ModelAdmin):
    """Admin view for financial summary - read-only"""
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Custom changelist view to show financial summary"""
        extra_context = extra_context or {}
        financial_summary = CompanyBalance.get_financial_summary()
        extra_context['financial_summary'] = financial_summary
        return super().changelist_view(request, extra_context)


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_preview', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order', '-created_at']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Gallery Information', {
            'fields': ('title', 'description', 'image', 'order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 100px;" />')
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(ExecutiveCouncil)
class ExecutiveCouncilAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'council_type', 'order', 'is_active', 'created_at']
    list_filter = ['council_type', 'is_active', 'created_at']
    search_fields = ['name', 'position', 'company_occupation']
    ordering = ['council_type', 'order', 'name']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'company_occupation', 'council_type')
        }),
        ('Media & Social', {
            'fields': ('image', 'facebook_url', 'twitter_url', 'linkedin_url'),
            'classes': ('collapse',)
        }),
        ('Display Options', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related()


@admin.register(FormUpload)
class FormUploadAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'form_file', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Form Information', {
            'fields': ('name', 'description', 'form_file')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SecretaryAdmin)
class SecretaryAdminAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone_number', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['full_name', 'email', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Secretary Information', {
            'fields': ('user', 'full_name', 'phone_number', 'email', 'is_active')
        }),
        ('Admin Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if not set"""
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Custom admin site configuration
admin.site.site_header = "Member Management System"
admin.site.site_title = "Member Management Admin"
admin.site.index_title = "Welcome to Member Management System"

# Add custom CSS for better styling
class AdminConfig:
    """Custom admin configuration"""
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


# Optional: Create a custom admin dashboard with financial summary
class CustomAdminSite(admin.AdminSite):
    """Custom admin site with financial dashboard"""
    
    def index(self, request, extra_context=None):
        """Custom index page with financial summary"""
        extra_context = extra_context or {}
        
        # Get financial summary
        financial_summary = CompanyBalance.get_financial_summary()
        
        # Get member statistics
        today = timezone.now().date()
        from datetime import timedelta
        expiry_threshold = today + timedelta(days=30)
        
        member_stats = {
            'total_members': Member.objects.count(),
            'expired_certificates': Member.objects.filter(
                certificate_expiry_date__lt=today
            ).exclude(certificate_expiry_date__isnull=True).count(),
            'expiring_soon': Member.objects.filter(
                certificate_expiry_date__gte=today,
                certificate_expiry_date__lte=expiry_threshold
            ).count(),
            'valid_certificates': Member.objects.filter(
                certificate_expiry_date__gt=expiry_threshold
            ).count(),
        }
        
        # Get recent activities
        recent_income = Income.objects.order_by('-created_at')[:5]
        recent_expenses = Expense.objects.order_by('-created_at')[:5]
        
        extra_context.update({
            'financial_summary': financial_summary,
            'member_stats': member_stats,
            'recent_income': recent_income,
            'recent_expenses': recent_expenses,
        })
        
        return super().index(request, extra_context)


# Uncomment the following lines if you want to use the custom admin site
admin_site = CustomAdminSite(name='custom_admin')
admin_site.register(Member, MemberAdmin)
admin_site.register(Income, IncomeAdmin)
admin_site.register(Expense, ExpenseAdmin)
admin_site.register(Gallery, GalleryAdmin)
admin_site.register(ExecutiveCouncil, ExecutiveCouncilAdmin)
admin_site.register(FormUpload, FormUploadAdmin)
admin_site.register(SecretaryAdmin, SecretaryAdminAdmin)