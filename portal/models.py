from django.db import models
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
import os
from django.contrib.auth.models import User


def upload_md_picture(instance, filename):
    return f'members/md_pictures/{instance.id}_{filename}'

def upload_certificate_picture(instance, filename):
    return f'members/certificates/{instance.id}_{filename}'

class Category(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name



class Member(models.Model):
    # Company Categories Choices
    CATEGORY_CHOICES = [
        ('building_development', 'Building Development'),
        ('site_and_services', 'Site and Services'),
        ('neighbourhood_estate', 'Neighbourhood Estate'),
        ('engineering_construction', 'Engineering/Construction'),
        ('surveying', 'Surveying'),
        ('contractor', 'Contractor'),
        ('realtor', 'Realtor'),
        ('student', 'Student'),
    ]
    
    # Basic Company Information
    company_name = models.CharField(max_length=200, blank=True, null=True)
    company_email = models.EmailField(max_length=254, verbose_name="Company Email", blank=True, null=True)
    company_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name="Company Category", blank=True, null=True)
    # company_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    rc_no = models.CharField(max_length=50, unique=True, verbose_name="RC Number", blank=True, null=True)
    md_phone_number = models.CharField(max_length=20, verbose_name="MD Phone Number", blank=True, null=True)
    md_picture = models.ImageField(upload_to=upload_md_picture, verbose_name="MD Picture", blank=True, null=True)
    certificate_picture = models.ImageField(upload_to=upload_certificate_picture, verbose_name="Certificate Picture", blank=True, null=True)
    
    # National Membership
    national_first_registered = models.DateField(verbose_name="Date of First Year Registered (National)", blank=True, null=True)
    
    # Certificate Information
    certificate_issued_date = models.DateField(verbose_name="Certificate Issued Date", blank=True, null=True)
    certificate_expiry_date = models.DateField(verbose_name="Certificate Expiry Date", blank=True, null=True)
    
    # Renewal Information
    last_renewal_date = models.DateField(verbose_name="Last Renewal Date", blank=True, null=True)
    renewal_count = models.PositiveIntegerField(default=0, verbose_name="Number of Renewals")
    
    # Enugu Membership
    enugu_first_registered = models.DateField(verbose_name="Date of First Registration (Enugu)", blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['company_name']
    
    def __str__(self):
        return self.company_name or f"Member {self.id}"
    
    @property
    def get_category_display_name(self):
        """Get human-readable category name"""
        return dict(self.CATEGORY_CHOICES).get(self.company_category, 'Unknown')
    
    # @property
    # def get_category_display_name(self):
    #     """Get human-readable category name"""
    #     return self.company_category.name if self.company_category else 'Unknown'
    
    @property
    def is_certificate_expiring_soon(self):
        """Check if certificate expires within 30 days"""
        if not self.certificate_expiry_date:
            return False
        
        today = timezone.now().date()
        days_until_expiry = (self.certificate_expiry_date - today).days
        return 0 <= days_until_expiry <= 30
    
    @property
    def is_certificate_expired(self):
        """Check if certificate has expired"""
        if not self.certificate_expiry_date:
            return False
        
        today = timezone.now().date()
        return self.certificate_expiry_date < today
    
    @property
    def days_until_expiry(self):
        """Get days until certificate expiry"""
        if not self.certificate_expiry_date:
            return None
        
        today = timezone.now().date()
        return (self.certificate_expiry_date - today).days
    
    @property
    def certificate_status(self):
        """Get certificate status"""
        if not self.certificate_expiry_date:
            return "no_date"
        
        if self.is_certificate_expired:
            return "expired"
        elif self.is_certificate_expiring_soon:
            return "expiring"
        else:
            return "valid"
    
    @property
    def certificate_status_display(self):
        """Get human-readable certificate status"""
        status = self.certificate_status
        status_map = {
            'expired': 'Expired',
            'expiring': 'Expiring Soon',
            'valid': 'Valid',
            'no_date': 'No Expiry Date'
        }
        return status_map.get(status, 'Unknown')
    
    @property
    def certificate_status_class(self):
        """Get CSS class for certificate status"""
        status = self.certificate_status
        class_map = {
            'expired': 'badge badge-danger',
            'expiring': 'badge badge-warning',
            'valid': 'badge badge-success',
            'no_date': 'badge badge-secondary'
        }
        return class_map.get(status, 'badge badge-secondary')
    
    @property
    def can_renew_certificate(self):
        """Check if certificate can be renewed (expired or expiring soon)"""
        return self.certificate_expiry_date and (self.is_certificate_expired or self.is_certificate_expiring_soon)
    
    @property
    def days_until_expiry_display(self):
        """Get human-readable days until expiry"""
        days = self.days_until_expiry
        if days is None:
            return "No expiry date set"
        elif days < 0:
            return f"Expired {abs(days)} days ago"
        elif days == 0:
            return "Expires today"
        elif days == 1:
            return "Expires tomorrow"
        else:
            return f"{days} days remaining"
    
    @property
    def new_expiry_date(self):
        """Calculate what the new expiry date would be after renewal"""
        if self.certificate_expiry_date:
            return self.certificate_expiry_date + timedelta(days=365)
        return None
    
    def renew_certificate(self):
        """Renew the certificate for another year"""
        if not self.certificate_expiry_date:
            return False
        
        try:
            # Set new expiry date to 1 year from current expiry date
            # This ensures no gap in coverage even if renewed early
            self.certificate_expiry_date = self.certificate_expiry_date + timedelta(days=365)
            self.last_renewal_date = timezone.now().date()
            self.renewal_count += 1
            self.save()
            return True
        except Exception as e:
            print(f"Error renewing certificate: {e}")
            return False
    
    def save(self, *args, **kwargs):
        # Auto-generate certificate expiry date only if:
        # 1. This is a new instance (no pk), OR
        # 2. There's a certificate issued date but no expiry date, OR
        # 3. The certificate issued date has changed from what's in the database
        if self.certificate_issued_date:
            should_update_expiry = False
            
            if not self.pk:
                # New instance - always set expiry date
                should_update_expiry = True
            elif not self.certificate_expiry_date:
                # No expiry date exists - set it
                should_update_expiry = True
            else:
                # Check if certificate issued date has changed
                try:
                    original = Member.objects.get(pk=self.pk)
                    if original.certificate_issued_date != self.certificate_issued_date:
                        should_update_expiry = True
                except Member.DoesNotExist:
                    # This shouldn't happen, but if it does, treat as new
                    should_update_expiry = True
            
            if should_update_expiry:
                self.certificate_expiry_date = self.certificate_issued_date + timedelta(days=365)
        
        super().save(*args, **kwargs)

# =======================================finances========================================
# class Income(models.Model):
#     INCOME_CATEGORIES = [
#         ('national_rebate', 'National rebate(registration)'),
#         ('enugu_validation', 'Enugu validation fee'),
#         ('donations', 'Donations'),
#         ('other_sources', 'Other sources'),
#     ]
    
#     category = models.CharField(max_length=50, choices=INCOME_CATEGORIES)
#     amount = models.DecimalField(max_digits=15, decimal_places=2)
#     date = models.DateField()
#     description = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-date', '-created_at']
    
#     def __str__(self):
#         return f"{self.get_category_display()} - ₦{self.amount:,.2f}"
    
#     @classmethod
#     def get_total_income(cls):
#         """Get total income"""
#         return cls.objects.aggregate(total=Sum('amount'))['total'] or 0


# Updated Income model with payer field
class Income(models.Model):
    INCOME_CATEGORIES = [
        ('national_rebate', 'National rebate(registration)'),
        ('enugu_validation', 'Enugu validation fee'),
        ('donations', 'Donations'),
        ('other_sources', 'Other sources'),
    ]
    
    category = models.CharField(max_length=50, choices=INCOME_CATEGORIES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    
    # New payer fields
    payer_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Payer Name")
    payer_member = models.ForeignKey(
        'Member', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        verbose_name="Payer (Member Company)",
        help_text="Select member company for Enugu validation fees"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()} - ₦{self.amount:,.2f}"
    
    @property
    def get_payer_display(self):
        """Get the appropriate payer name to display"""
        if self.category == 'enugu_validation' and self.payer_member:
            return self.payer_member.company_name
        return self.payer_name or "Not specified"
    
    @classmethod
    def get_total_income(cls):
        """Get total income"""
        return cls.objects.aggregate(total=Sum('amount'))['total'] or 0


class Expense(models.Model):
    EXPENSE_CATEGORIES = [
        ('rent', 'Rent'),
        ('electricity', 'Electricity'),
        ('furnitures', 'Furnitures'),
        ('stationaries', 'Stationaries'),
        ('fuel_diesel', 'Fuel/Diesel'),
        ('salary', 'Salary'),
        ('events', 'Events'),
        ('exco8_meetings', 'Exco8 meetings hosting'),
        ('general_meeting', 'General meeting expenses'),
        ('logistics', 'Logistics'),
        ('outreach', 'Outreach/Social responsibility'),
        ('advertising', 'Advertising and publicity'),
        ('office_maintenance', 'Office maintenance'),
        ('office_equipments', 'Office equipments'),
        ('internet_subscription', 'Internet subscription'),
        ('miscellaneous', 'Miscellaneous'),
    ]
    
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()} - ₦{self.amount:,.2f}"
    
    @classmethod
    def get_total_expenses(cls):
        """Get total expenses"""
        return cls.objects.aggregate(total=Sum('amount'))['total'] or 0


class CompanyBalance(models.Model):
    """Model to track company balance"""
    
    @classmethod
    def get_current_balance(cls):
        """Calculate current balance (Total Income - Total Expenses)"""
        total_income = Income.get_total_income()
        total_expenses = Expense.get_total_expenses()
        return total_income - total_expenses
    
    @classmethod
    def get_financial_summary(cls):
        """Get complete financial summary"""
        total_income = Income.get_total_income()
        total_expenses = Expense.get_total_expenses()
        current_balance = total_income - total_expenses
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'current_balance': current_balance,
            'income_count': Income.objects.count(),
            'expense_count': Expense.objects.count(),
        }
        

# ================GAllery=====================

class Gallery(models.Model):
    """Model for storing gallery images displayed on the frontend"""
    
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    order = models.PositiveIntegerField(default=0, help_text="Display order in gallery")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'
    
    def __str__(self):
        return self.title if self.title else f"Gallery Image {self.id}"
    
    
    
# ===============leadership ========================


class ExecutiveCouncil(models.Model):
    """Model for storing executive council members information"""
    
    COUNCIL_TYPES = [
        ('state', 'State Executive'),
        ('zonal', 'Zonal Representative'),
        ('national', 'National Executive'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255, help_text="e.g., State Chairman, Vice Chairman, etc.")
    company_occupation = models.CharField(max_length=500, blank=True, null=True, help_text="Company or occupation details")
    
    # Council Classification
    council_type = models.CharField(max_length=20, choices=COUNCIL_TYPES, default='state')
    
    # Image and Social Media
    image = models.ImageField(upload_to='executives/', blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    
    # Display Options
    order = models.PositiveIntegerField(default=0, help_text="Display order within council type")
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['council_type', 'order', 'name']
        verbose_name = 'Executive Council Member'
        verbose_name_plural = 'Executive Council Members'
    
    def __str__(self):
        return f"{self.name} - {self.position}"
    
    def get_council_type_display_verbose(self):
        """Get a more detailed display name for council type"""
        type_mapping = {
            'state': 'State Executive Council',
            'zonal': 'Zonal Representatives',
            'national': 'National Executive Council'
        }
        return type_mapping.get(self.council_type, self.get_council_type_display())
    
    
class FormUpload(models.Model):
    """Model for storing uploaded forms that can be downloaded from the frontend"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    form_file = models.FileField(upload_to='forms/')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def file_type(self):
        """Returns the file extension of the uploaded form"""
        _, extension = os.path.splitext(self.form_file.name)
        return extension.upper()[1:] if extension else 'N/A'
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Form Upload'
        verbose_name_plural = 'Form Uploads'
        
        

class SecretaryAdmin(models.Model):
    """Model for secretary admin accounts"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_secretaries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Secretary Admin'
        verbose_name_plural = 'Secretary Admins'
        
    def __str__(self):
        return f"{self.full_name} - {self.email}"