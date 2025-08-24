from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import (
    Category, Member, Income, Expense, CompanyBalance, 
    Gallery, ExecutiveCouncil, FormUpload, SecretaryAdmin,RedanTVVideo
)


# Custom filters for Member model
class CertificateStatusFilter(admin.SimpleListFilter):
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
        thirty_days_from_now = today + timedelta(days=30)
        
        if self.value() == 'expired':
            return queryset.filter(certificate_expiry_date__lt=today)
        elif self.value() == 'expiring':
            return queryset.filter(
                certificate_expiry_date__gte=today,
                certificate_expiry_date__lte=thirty_days_from_now
            )
        elif self.value() == 'valid':
            return queryset.filter(certificate_expiry_date__gt=thirty_days_from_now)
        elif self.value() == 'no_date':
            return queryset.filter(certificate_expiry_date__isnull=True)


class CompanyCategoryFilter(admin.SimpleListFilter):
    title = 'Company Category'
    parameter_name = 'company_category'

    def lookups(self, request, model_admin):
        return Member.CATEGORY_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(company_categories__icontains=self.value())


# Admin configurations
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    ordering = ('name',)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'company_name', 'get_categories_display_short', 'rc_no', 
        'certificate_status_badge', 'days_until_expiry_display',
        'created_at'
    )
    list_filter = (
        CertificateStatusFilter,
        CompanyCategoryFilter,
        'created_at',
        'certificate_issued_date',
        'last_renewal_date',
    )
    search_fields = (
        'company_name', 'company_email', 'rc_no', 
        'redan_reg_number', 'md_phone_number'
    )
    readonly_fields = (
        'certificate_status_badge', 'days_until_expiry_display',
        'renewal_count', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Company Information', {
            'fields': (
                'company_name', 'company_email', 'company_categories',
                'address', 'rc_no', 'md_phone_number'
            )
        }),
        ('Project Information', {
            'fields': ('company_projects', 'project_images'),
            'classes': ('collapse',)
        }),
        ('Media Files', {
            'fields': ('md_picture', 'certificate_picture'),
            'classes': ('collapse',)
        }),
        ('National Membership', {
            'fields': (
                'national_first_registered', 'redan_reg_number'
            ),
            'classes': ('collapse',)
        }),
        ('Certificate Information', {
            'fields': (
                'certificate_issued_date', 'certificate_expiry_date',
                'certificate_status_badge', 'days_until_expiry_display'
            )
        }),
        ('Renewal Information', {
            'fields': (
                'last_renewal_date', 'renewal_count'
            ),
            'classes': ('collapse',)
        }),
        ('Enugu Membership', {
            'fields': ('enugu_first_registered',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['renew_certificates', 'export_members']
    
    def get_categories_display_short(self, obj):
        """Display categories in a shortened format"""
        categories = obj.get_categories_display
        if len(categories) > 2:
            return f"{', '.join(categories[:2])}... (+{len(categories)-2} more)"
        return ', '.join(categories)
    get_categories_display_short.short_description = 'Categories'
    
    def certificate_status_badge(self, obj):
        """Display certificate status with color coding"""
        status = obj.certificate_status
        status_colors = {
            'expired': '#dc3545',
            'expiring': '#ffc107',
            'valid': '#28a745',
            'no_date': '#6c757d'
        }
        color = status_colors.get(status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.certificate_status_display
        )
    certificate_status_badge.short_description = 'Status'
    
    def renew_certificates(self, request, queryset):
        """Bulk action to renew certificates"""
        renewed_count = 0
        for member in queryset:
            if member.can_renew_certificate and member.renew_certificate():
                renewed_count += 1
        
        self.message_user(
            request,
            f'Successfully renewed {renewed_count} certificates.'
        )
    renew_certificates.short_description = 'Renew selected certificates'
    
    def export_members(self, request, queryset):
        """Export selected members (placeholder)"""
        self.message_user(
            request,
            f'Export functionality can be implemented for {queryset.count()} members.'
        )
    export_members.short_description = 'Export selected members'


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        'category', 'amount_display', 'get_payer_display', 
        'date', 'created_at'
    )
    list_filter = ('category', 'date', 'created_at')
    search_fields = ('description', 'payer_name', 'payer_member__company_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Income Details', {
            'fields': ('category', 'amount', 'date', 'description')
        }),
        ('Payer Information', {
            'fields': ('payer_name', 'payer_member'),
            'description': 'For Enugu validation fees, select the member company. For other income types, use payer name.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def amount_display(self, obj):
        """Display amount with currency formatting"""
        return f"₦{obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on category"""
        form = super().get_form(request, obj, **kwargs)
        return form


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'category', 'amount_display', 'description_short', 
        'date', 'created_at'
    )
    list_filter = ('category', 'date', 'created_at')
    search_fields = ('description',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Expense Details', {
            'fields': ('category', 'amount', 'date', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def amount_display(self, obj):
        """Display amount with currency formatting"""
        return f"₦{obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def description_short(self, obj):
        """Display shortened description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'image_preview', 'order', 'is_active', 
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('order', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    
    fieldsets = (
        ('Gallery Item', {
            'fields': ('title', 'description', 'image', 'image_preview')
        }),
        ('Display Options', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_preview(self, obj):
        """Display image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(ExecutiveCouncil)
class ExecutiveCouncilAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'position', 'council_type', 'image_preview', 
        'order', 'is_active'
    )
    list_filter = ('council_type', 'is_active', 'created_at')
    search_fields = ('name', 'position', 'company_occupation')
    list_editable = ('order', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'position', 'company_occupation', 'council_type')
        }),
        ('Image and Social Media', {
            'fields': (
                'image', 'image_preview',
                'facebook_url', 'twitter_url', 'linkedin_url'
            )
        }),
        ('Display Options', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_preview(self, obj):
        """Display image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit: cover; border-radius: 50%;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Photo'


@admin.register(FormUpload)
class FormUploadAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'file_type', 'description_short', 
        'created_at'
    )
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'file_type')
    
    fieldsets = (
        ('Form Details', {
            'fields': ('name', 'description', 'form_file', 'file_type')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def description_short(self, obj):
        """Display shortened description"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return "No description"
    description_short.short_description = 'Description'


@admin.register(SecretaryAdmin)
class SecretaryAdminAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'email', 'phone_number', 
        'is_active', 'created_by', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('full_name', 'email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Secretary Information', {
            'fields': ('user', 'full_name', 'email', 'phone_number')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user for new objects"""
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Custom admin site configuration
admin.site.site_header = "REDAN Enugu Admin"
admin.site.site_title = "REDAN Enugu"
admin.site.index_title = "Welcome to REDAN Enugu Administration"


# Add custom dashboard info (optional)
class CustomAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Add some statistics
        extra_context['total_members'] = Member.objects.count()
        extra_context['expiring_certificates'] = Member.objects.filter(
            certificate_expiry_date__lte=timezone.now().date() + timedelta(days=30),
            certificate_expiry_date__gte=timezone.now().date()
        ).count()
        extra_context['expired_certificates'] = Member.objects.filter(
            certificate_expiry_date__lt=timezone.now().date()
        ).count()
        
        financial_summary = CompanyBalance.get_financial_summary()
        extra_context['financial_summary'] = financial_summary
        
        return super().index(request, extra_context)



@admin.register(RedanTVVideo)
class RedanTVVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'thumbnail_preview', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'youtube_url']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'youtube_url', 'order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def thumbnail_preview(self, obj):
        """Show thumbnail preview in admin"""
        thumbnail_url = obj.get_thumbnail_url()
        if thumbnail_url:
            return format_html(
                '<img src="{}" width="80" height="45" style="border-radius: 4px;" />',
                thumbnail_url
            )
        return "No thumbnail"
    
    thumbnail_preview.short_description = "Thumbnail"
    
    def save_model(self, request, obj, form, change):
        """Custom save to handle ordering"""
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)  # Optional: for custom styling
        }

# Optional: Inline JavaScript for better UX
admin.site.site_header = "Redan TV Admin"
admin.site.site_title = "Redan TV"
admin.site.index_title = "Welcome to Redan TV Administration"