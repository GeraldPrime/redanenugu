from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from .models import Income, Expense, CompanyBalance, Member,Gallery, ExecutiveCouncil,FormUpload, SecretaryAdmin
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime

from django.utils import timezone
from datetime import datetime, timedelta
import os


from decimal import Decimal


from django.views.decorators.http import require_POST

# views.py
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage

import calendar

from django.http import HttpResponse, Http404
import mimetypes



from django.db import transaction
import random
import string

from functools import wraps
from .helper import admin_required, admin_or_secretary_required, secretary_required



from .utils.email_utils import send_certificate_expiry_email, send_bulk_certificate_emails, get_default_email_message
import json
import logging

from django.conf import settings
from .utils.email_utils import send_email_to_all_members, get_member_emails





# Create your views here.
logger = logging.getLogger(__name__)

def home(request):
    return render(request, "frontend/index.html")


def about(request):
    return render(request, "frontend/about.html")


def gallery(request):
    return render(request, "frontend/gallery.html")


def redantv(request):
    return render(request, "frontend/redanenugutv.html")


def downloadables (request):
    return render(request, "frontend/downloadables.html")


def contact(request):
    return render(request, "frontend/contact.html")


def checkmembers(request):
    return render(request, "frontend/members.html")



# =======================================================================
# ======================admin side start ===============================

# def signin(request):
#     if not request.user.is_authenticated and request.GET.get('next'):
#         messages.info(request, "You need to login to access this page.")

#     if request.method == 'POST':
#         form = request.POST
#         name_or_email = form.get('name')  # This can be either username or email
#         password = form.get('password')
        
#         # Check if the input is an email or username
#         user = None
#         if '@' in name_or_email:  # Email login case
#             user = authenticate(request, username=User.objects.filter(email=name_or_email).first().username, password=password)
#         else:  # Username login case
#             user = authenticate(request, username=name_or_email, password=password)
        
#         if user is not None:
#             login(request, user)
#             messages.success(request, 'Login Successful!')
#             return redirect('user')
            
#         else:
#             messages.error(request, 'Login Error: Invalid credentials')
#             return redirect('signin')

#     return render(request, "user/signin.html")



def signin(request):
    if not request.user.is_authenticated and request.GET.get('next'):
        messages.info(request, "You need to login to access this page.")

    if request.method == 'POST':
        form = request.POST
        name_or_email = form.get('name')  # This can be either username or email
        password = form.get('password')
        
        # Check if the input is an email or username
        user = None
        try:
            if '@' in name_or_email:  # Email login case
                user_obj = User.objects.filter(email=name_or_email).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            else:  # Username login case
                user = authenticate(request, username=name_or_email, password=password)
        except:
            user = None
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login Successful!')
            
            # Check if user is a secretary admin
            try:
                secretary = SecretaryAdmin.objects.get(user=user)
                if secretary.is_active:
                    return redirect('secretary_dashboard')
                else:
                    messages.error(request, 'Your secretary account is currently inactive.')
                    return redirect('signin')
            except SecretaryAdmin.DoesNotExist:
                # Regular admin user
                return redirect('user')
            
        else:
            messages.error(request, 'Login Error: Invalid credentials')
            return redirect('signin')

    return render(request, "user/signin.html")

def signout(request):
    logout(request)
    messages.success(request, 'logout successful')
    return redirect('signin')


@login_required
def user(request):
    # Redirect secretaries to their dashboard
    try:
        secretary = SecretaryAdmin.objects.get(user=request.user)
        if secretary.is_active:
            return redirect('secretary_dashboard')
    except SecretaryAdmin.DoesNotExist:
        pass  # Continue with regular admin dashboard
    
    # Get current date
    today = timezone.now().date()
    
    # Member Statistics
    total_members = Member.objects.count()
    
    # Certificate Status Statistics
    expired_certificates = Member.objects.filter(
        certificate_expiry_date__lt=today
    ).count()
    
    expiring_soon_certificates = Member.objects.filter(
        certificate_expiry_date__gte=today,
        certificate_expiry_date__lte=today + timedelta(days=30)
    ).count()
    
    valid_certificates = Member.objects.filter(
        certificate_expiry_date__gt=today + timedelta(days=30)
    ).count()
    
    # New members this month
    start_of_month = today.replace(day=1)
    new_members_this_month = Member.objects.filter(
        created_at__date__gte=start_of_month
    ).count()
    
    # Financial Summary
    financial_summary = CompanyBalance.get_financial_summary()
    
    # Recent Income (last 5 entries)
    recent_income = Income.objects.all()[:5]
    
    # Recent Expenses (last 5 entries)
    recent_expenses = Expense.objects.all()[:5]
    
    # Income by category (for charts)
    income_by_category = {}
    total_income_amount = financial_summary['total_income']
    for category_code, category_name in Income.INCOME_CATEGORIES:
        total = Income.objects.filter(category=category_code).aggregate(
            total=Sum('amount')
        )['total'] or 0
        if total > 0:
            percentage = (total / total_income_amount * 100) if total_income_amount > 0 else 0
            income_by_category[category_name] = {
                'amount': total,
                'percentage': percentage
            }
    
    # Expense by category (for charts)
    expense_by_category = {}
    total_expense_amount = financial_summary['total_expenses']
    for category_code, category_name in Expense.EXPENSE_CATEGORIES:
        total = Expense.objects.filter(category=category_code).aggregate(
            total=Sum('amount')
        )['total'] or 0
        if total > 0:
            percentage = (total / total_expense_amount * 100) if total_expense_amount > 0 else 0
            expense_by_category[category_name] = {
                'amount': total,
                'percentage': percentage
            }
    
    # Members with expiring certificates (for alerts)
    members_with_expiring_certificates = Member.objects.filter(
        certificate_expiry_date__gte=today,
        certificate_expiry_date__lte=today + timedelta(days=30)
    ).order_by('certificate_expiry_date')[:10]
    
    # Monthly trends (last 6 months) - FIXED VERSION
    monthly_income = []
    monthly_expenses = []
    
    # Get the first day of current month
    current_month = today.replace(day=1)
    
    for i in range(6):
        # Calculate month boundaries properly
        if i == 0:
            # Current month
            month_start = current_month
            month_end = today
        else:
            # Previous months
            # Go back i months from current month
            year = current_month.year
            month = current_month.month - i
            
            # Handle year rollover
            while month <= 0:
                month += 12
                year -= 1
            
            month_start = current_month.replace(year=year, month=month, day=1)
            
            # Get last day of the month
            if month == 12:
                next_month = month_start.replace(year=year + 1, month=1, day=1)
            else:
                next_month = month_start.replace(month=month + 1, day=1)
            
            month_end = next_month - timedelta(days=1)
        
        # Calculate totals for this month
        month_income = Income.objects.filter(
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_expense = Expense.objects.filter(
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Insert at beginning to maintain chronological order
        monthly_income.insert(0, {
            'month': month_start.strftime('%B %Y'),
            'amount': month_income
        })
        monthly_expenses.insert(0, {
            'month': month_start.strftime('%B %Y'),
            'amount': month_expense
        })
    
    # Calculate proper averages - FIXED VERSION
    # Method 1: Average including months with zero transactions
    total_monthly_income = sum([item['amount'] for item in monthly_income])
    total_monthly_expenses = sum([item['amount'] for item in monthly_expenses])
    average_monthly_income = total_monthly_income / len(monthly_income) if monthly_income else 0
    average_monthly_expense = total_monthly_expenses / len(monthly_expenses) if monthly_expenses else 0
    
    # Method 2: Average excluding months with zero transactions (alternative)
    # You can use this instead if you prefer to exclude zero months
    non_zero_income_months = [item['amount'] for item in monthly_income if item['amount'] > 0]
    non_zero_expense_months = [item['amount'] for item in monthly_expenses if item['amount'] > 0]
    
    # Uncomment these lines if you want to exclude zero months from averages
    # average_monthly_income = sum(non_zero_income_months) / len(non_zero_income_months) if non_zero_income_months else 0
    # average_monthly_expense = sum(non_zero_expense_months) / len(non_zero_expense_months) if non_zero_expense_months else 0
    
    context = {
        # Member Statistics
        'total_members': total_members,
        'new_members_this_month': new_members_this_month,
        'expired_certificates': expired_certificates,
        'expiring_soon_certificates': expiring_soon_certificates,
        'valid_certificates': valid_certificates,
        
        # Financial Data
        'total_income': financial_summary['total_income'],
        'total_expenses': financial_summary['total_expenses'],
        'current_balance': financial_summary['current_balance'],
        'income_count': financial_summary['income_count'],
        'expense_count': financial_summary['expense_count'],
        
        # Recent Transactions
        'recent_income': recent_income,
        'recent_expenses': recent_expenses,
        
        # Category Breakdowns
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
        
        # Alerts and Notifications
        'members_with_expiring_certificates': members_with_expiring_certificates,
        
        # Monthly Trends
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        
        # Calculated Metrics - FIXED
        'certificate_renewal_rate': (
            (expired_certificates + expiring_soon_certificates) / total_members * 100
            if total_members > 0 else 0
        ),
        'average_monthly_income': average_monthly_income,
        'average_monthly_expense': average_monthly_expense,
        
        # Additional useful metrics
        'total_months_analyzed': len(monthly_income),
        'months_with_income': len(non_zero_income_months),
        'months_with_expenses': len(non_zero_expense_months),
    }
    
    return render(request, "user/index.html", context)

# =========MEMBERSHIP===========

# @login_required
# def members_list(request):
#     """List all members with search and filter functionality"""
#     members = Member.objects.all()
    
#     # Search functionality
#     search_query = request.GET.get('search', '')
#     if search_query:
#         members = members.filter(
#             Q(company_name__icontains=search_query) |
#             Q(rc_no__icontains=search_query) |
#             Q(address__icontains=search_query) |
#             Q(md_phone_number__icontains=search_query)
#         )
    
#     # Filter by certificate status
#     status_filter = request.GET.get('status', '')
#     if status_filter == 'expired':
#         members = members.filter(certificate_expiry_date__lt=timezone.now().date())
#     elif status_filter == 'expiring':
#         members = members.filter(
#             certificate_expiry_date__lte=timezone.now().date() + timedelta(days=30),
#             certificate_expiry_date__gte=timezone.now().date()
#         )
#     elif status_filter == 'valid':
#         members = members.filter(certificate_expiry_date__gt=timezone.now().date() + timedelta(days=30))
    
#     # Filter by category
#     category_filter = request.GET.get('category', '')
#     if category_filter:
#         members = members.filter(company_category=category_filter)
    
#     # Pagination
#     paginator = Paginator(members, 10)
#     page_number = request.GET.get('page')
#     members_page = paginator.get_page(page_number)
    
#     context = {
#         'members': members_page,
#         'search_query': search_query,
#         'status_filter': status_filter,
#         'category_filter': category_filter,
#     }
#     return render(request, 'user/members_list.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import Member
from .utils.email_utils import send_certificate_expiry_email, send_bulk_certificate_emails

@login_required
def members_list(request):
    """List all members with search and filter functionality"""
    # members = Member.objects.all()
    members = Member.objects.all().order_by('-created_at')
   
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(company_name__icontains=search_query) |
            Q(rc_no__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(md_phone_number__icontains=search_query)
        )
   
    # Filter by certificate status
    status_filter = request.GET.get('status', '')
    if status_filter == 'expired':
        members = members.filter(certificate_expiry_date__lt=timezone.now().date())
    elif status_filter == 'expiring':
        members = members.filter(
            certificate_expiry_date__lte=timezone.now().date() + timedelta(days=30),
            certificate_expiry_date__gte=timezone.now().date()
        )
    elif status_filter == 'valid':
        members = members.filter(certificate_expiry_date__gt=timezone.now().date() + timedelta(days=30))
   
    # Filter by category - Updated to handle multiple categories
    category_filter = request.GET.get('category', '')
    if category_filter:
        # Use icontains to search within the comma-separated categories string
        # This will match if the category appears anywhere in the company_categories field
        members = members.filter(company_categories__icontains=category_filter)
   
    # Calculate email statistics for bulk actions
    all_members = Member.objects.filter(
        certificate_expiry_date__isnull=False,
        company_email__isnull=False
    ).exclude(company_email='')
   
    expiring_count = len([m for m in all_members if m.is_certificate_expiring_soon])
    expired_count = len([m for m in all_members if m.is_certificate_expired])
   
    # Pagination
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    members_page = paginator.get_page(page_number)
   
    context = {
        'members': members_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'expiring_count': expiring_count,
        'expired_count': expired_count,
    }
    return render(request, 'user/members_list.html', context)


@login_required
def send_individual_email(request, member_id):
    """Send individual email to a member"""
    member = get_object_or_404(Member, id=member_id)
    
    if not member.company_email:
        messages.error(request, f'No email address found for {member.company_name}')
        return redirect('members_list')
    
    try:
        success = send_certificate_expiry_email(member)
        if success:
            messages.success(request, f'Email sent successfully to {member.company_name}')
        else:
            messages.error(request, f'Failed to send email to {member.company_name}')
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
    
    return redirect('members_list')

@login_required
def send_bulk_email(request):
    """Send bulk emails to expiring or expired members"""
    email_type = request.GET.get('type')
    
    if email_type not in ['expiring', 'expired']:
        messages.error(request, 'Invalid email type specified')
        return redirect('members_list')
    
    # Get members with email addresses
    members_with_emails = Member.objects.filter(
        certificate_expiry_date__isnull=False,
        company_email__isnull=False
    ).exclude(company_email='')
    
    if email_type == 'expiring':
        target_members = [m for m in members_with_emails if m.is_certificate_expiring_soon]
        email_subject = 'expiring'
    else:  # expired
        target_members = [m for m in members_with_emails if m.is_certificate_expired]
        email_subject = 'expired'
    
    if not target_members:
        messages.warning(request, f'No members found with {email_type} certificates')
        return redirect('members_list')
    
    try:
        success_count, failed_count = send_bulk_certificate_emails(target_members, email_subject)
        
        if success_count > 0:
            messages.success(request, f'Successfully sent {success_count} emails to {email_type} members')
        if failed_count > 0:
            messages.warning(request, f'Failed to send {failed_count} emails')
            
    except Exception as e:
        messages.error(request, f'Error sending bulk emails: {str(e)}')
    
    return redirect('members_list')



# @login_required
# def create_member(request):
#     """Create a new member"""
#     if request.method == 'POST':
#         try:
#             # Get form data
#             company_name = request.POST.get('company_name')
#             company_email = request.POST.get('company_email')
#             company_categories = request.POST.getlist('company_categories')  # Changed to getlist
#             address = request.POST.get('address')
#             rc_no = request.POST.get('rc_no')
#             md_phone_number = request.POST.get('md_phone_number')
#             national_first_registered = request.POST.get('national_first_registered')
#             redan_reg_number = request.POST.get('redan_reg_number')  # New field
#             certificate_issued_date = request.POST.get('certificate_issued_date')
#             enugu_first_registered = request.POST.get('enugu_first_registered')
            
#             # Get uploaded files
#             md_picture = request.FILES.get('md_picture')
#             certificate_picture = request.FILES.get('certificate_picture')
            
#             # Validate required fields
#             if not all([company_name, company_email, address, rc_no, md_phone_number, 
#                        national_first_registered, redan_reg_number, certificate_issued_date, 
#                        enugu_first_registered, md_picture, certificate_picture]):
#                 messages.error(request, 'All fields are required.')
#                 return render(request, 'user/create_member.html')
            
#             # Validate at least one category is selected
#             if not company_categories:
#                 messages.error(request, 'Please select at least one company category.')
#                 return render(request, 'user/create_member.html')
            
#             # Check if RC number already exists
#             if Member.objects.filter(rc_no=rc_no).exists():
#                 messages.error(request, 'A member with this RC number already exists.')
#                 return render(request, 'user/create_member.html')
            
#             # Check if company email already exists
#             if Member.objects.filter(company_email=company_email).exists():
#                 messages.error(request, 'A member with this email address already exists.')
#                 return render(request, 'user/create_member.html')
            
#             # Check if REDAN Reg. Number already exists
#             if Member.objects.filter(redan_reg_number=redan_reg_number).exists():
#                 messages.error(request, 'A member with this REDAN registration number already exists.')
#                 return render(request, 'user/create_member.html')
            
#             # Create member
#             member = Member.objects.create(
#                 company_name=company_name,
#                 company_email=company_email,
#                 company_categories=','.join(company_categories),  # Join categories with comma
#                 address=address,
#                 rc_no=rc_no,
#                 md_phone_number=md_phone_number,
#                 md_picture=md_picture,
#                 certificate_picture=certificate_picture,
#                 national_first_registered=datetime.strptime(national_first_registered, '%Y-%m-%d').date(),
#                 redan_reg_number=redan_reg_number,  # New field
#                 certificate_issued_date=datetime.strptime(certificate_issued_date, '%Y-%m-%d').date(),
#                 enugu_first_registered=datetime.strptime(enugu_first_registered, '%Y-%m-%d').date(),
#             )
            
#             messages.success(request, f'Member "{company_name}" created successfully.')
#             return redirect('member_detail', member_id=member.id)
            
#         except Exception as e:
#             messages.error(request, f'Error creating member: {str(e)}')
    
#     return render(request, 'user/create_member.html')


@login_required
def create_member(request):
    """Create a new member"""
    if request.method == 'POST':
        try:
            # Get form data
            company_name = request.POST.get('company_name')
            company_email = request.POST.get('company_email')
            company_categories = request.POST.getlist('company_categories')  # Changed to getlist
            company_projects = request.POST.get('company_projects')  # New field
            address = request.POST.get('address')
            rc_no = request.POST.get('rc_no')
            md_phone_number = request.POST.get('md_phone_number')
            national_first_registered = request.POST.get('national_first_registered')
            redan_reg_number = request.POST.get('redan_reg_number')  # New field
            certificate_issued_date = request.POST.get('certificate_issued_date')
            enugu_first_registered = request.POST.get('enugu_first_registered')
            
            # Get uploaded files
            md_picture = request.FILES.get('md_picture')
            certificate_picture = request.FILES.get('certificate_picture')
            project_images = request.FILES.get('project_images')  # New field
            
            # Validate required fields
            if not all([company_name, company_email, address, rc_no, md_phone_number, 
                       national_first_registered, redan_reg_number, certificate_issued_date, 
                       enugu_first_registered, md_picture, certificate_picture]):
                messages.error(request, 'All required fields must be filled.')
                return render(request, 'user/create_member.html')
            
            # Validate at least one category is selected
            if not company_categories:
                messages.error(request, 'Please select at least one company category.')
                return render(request, 'user/create_member.html')
            
            # Check if RC number already exists
            if Member.objects.filter(rc_no=rc_no).exists():
                messages.error(request, 'A member with this RC number already exists.')
                return render(request, 'user/create_member.html')
            
            # Check if company email already exists
            if Member.objects.filter(company_email=company_email).exists():
                messages.error(request, 'A member with this email address already exists.')
                return render(request, 'user/create_member.html')
            
            # Check if REDAN Reg. Number already exists
            if Member.objects.filter(redan_reg_number=redan_reg_number).exists():
                messages.error(request, 'A member with this REDAN registration number already exists.')
                return render(request, 'user/create_member.html')
            
            # Create member
            member = Member.objects.create(
                company_name=company_name,
                company_email=company_email,
                company_categories=','.join(company_categories),  # Join categories with comma
                company_projects=company_projects,  # New field
                address=address,
                rc_no=rc_no,
                md_phone_number=md_phone_number,
                md_picture=md_picture,
                certificate_picture=certificate_picture,
                project_images=project_images,  # New field
                national_first_registered=datetime.strptime(national_first_registered, '%Y-%m-%d').date(),
                redan_reg_number=redan_reg_number,  # New field
                certificate_issued_date=datetime.strptime(certificate_issued_date, '%Y-%m-%d').date(),
                enugu_first_registered=datetime.strptime(enugu_first_registered, '%Y-%m-%d').date(),
            )
            
            messages.success(request, f'Member "{company_name}" created successfully.')
            return redirect('member_detail', member_id=member.id)
            
        except Exception as e:
            messages.error(request, f'Error creating member: {str(e)}')
    
    return render(request, 'user/create_member.html')



# @login_required
# @admin_required
# def edit_member(request, member_id):
#     """Edit member information"""
#     member = get_object_or_404(Member, id=member_id)
    
#     if request.method == 'POST':
#         try:
#             # Get form data
#             company_name = request.POST.get('company_name')
#             company_email = request.POST.get('company_email')
#             company_categories = request.POST.getlist('company_categories')  # Changed to getlist
#             address = request.POST.get('address')
#             rc_no = request.POST.get('rc_no')
#             md_phone_number = request.POST.get('md_phone_number')
#             national_first_registered = request.POST.get('national_first_registered')
#             redan_reg_number = request.POST.get('redan_reg_number')  # New field
#             certificate_issued_date = request.POST.get('certificate_issued_date')
#             enugu_first_registered = request.POST.get('enugu_first_registered')
            
#             # Validate required fields
#             if not all([company_name, company_email, address, rc_no, 
#                        md_phone_number, national_first_registered, redan_reg_number,
#                        certificate_issued_date, enugu_first_registered]):
#                 messages.error(request, 'All fields are required.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Validate at least one category is selected
#             if not company_categories:
#                 messages.error(request, 'Please select at least one company category.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Check if RC number already exists (excluding current member)
#             if Member.objects.filter(rc_no=rc_no).exclude(id=member_id).exists():
#                 messages.error(request, 'A member with this RC number already exists.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Check if company email already exists (excluding current member)
#             if Member.objects.filter(company_email=company_email).exclude(id=member_id).exists():
#                 messages.error(request, 'A member with this email address already exists.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Check if REDAN Reg. Number already exists (excluding current member)
#             if Member.objects.filter(redan_reg_number=redan_reg_number).exclude(id=member_id).exists():
#                 messages.error(request, 'A member with this REDAN registration number already exists.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Update member data
#             member.company_name = company_name
#             member.company_email = company_email
#             member.company_categories = ','.join(company_categories)  # Join categories with comma
#             member.address = address
#             member.rc_no = rc_no
#             member.md_phone_number = md_phone_number
#             member.national_first_registered = datetime.strptime(
#                 national_first_registered, '%Y-%m-%d'
#             ).date()
#             member.redan_reg_number = redan_reg_number  # New field
#             member.certificate_issued_date = datetime.strptime(
#                 certificate_issued_date, '%Y-%m-%d'
#             ).date()
#             member.enugu_first_registered = datetime.strptime(
#                 enugu_first_registered, '%Y-%m-%d'
#             ).date()
            
#             # Update files if provided
#             if request.FILES.get('md_picture'):
#                 member.md_picture = request.FILES.get('md_picture')
#             if request.FILES.get('certificate_picture'):
#                 member.certificate_picture = request.FILES.get('certificate_picture')
            
#             # The model's save method handles certificate expiry date calculation
#             member.save()
#             messages.success(request, f'Member "{member.company_name}" updated successfully.')
#             return redirect('member_detail', member_id=member.id)
            
#         except Exception as e:
#             messages.error(request, f'Error updating member: {str(e)}')
    
#     context = {
#         'member': member,
#         'today': timezone.now().date()
#     }
#     return render(request, 'user/edit_member.html', context)

@login_required
@admin_required
def edit_member(request, member_id):
    """Edit member information"""
    member = get_object_or_404(Member, id=member_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            company_name = request.POST.get('company_name')
            company_email = request.POST.get('company_email')
            company_categories = request.POST.getlist('company_categories')  # Changed to getlist
            company_projects = request.POST.get('company_projects')  # New field
            address = request.POST.get('address')
            rc_no = request.POST.get('rc_no')
            md_phone_number = request.POST.get('md_phone_number')
            national_first_registered = request.POST.get('national_first_registered')
            redan_reg_number = request.POST.get('redan_reg_number')  # New field
            certificate_issued_date = request.POST.get('certificate_issued_date')
            enugu_first_registered = request.POST.get('enugu_first_registered')
            
            # Validate required fields
            if not all([company_name, company_email, address, rc_no, 
                       md_phone_number, national_first_registered, redan_reg_number,
                       certificate_issued_date, enugu_first_registered]):
                messages.error(request, 'All fields are required.')
                return render(request, 'user/edit_member.html', {'member': member})
            
            # Validate at least one category is selected
            if not company_categories:
                messages.error(request, 'Please select at least one company category.')
                return render(request, 'user/edit_member.html', {'member': member})
            
            # Check if RC number already exists (excluding current member)
            if Member.objects.filter(rc_no=rc_no).exclude(id=member_id).exists():
                messages.error(request, 'A member with this RC number already exists.')
                return render(request, 'user/edit_member.html', {'member': member})
            
            # Check if company email already exists (excluding current member)
            if Member.objects.filter(company_email=company_email).exclude(id=member_id).exists():
                messages.error(request, 'A member with this email address already exists.')
                return render(request, 'user/edit_member.html', {'member': member})
            
            # Check if REDAN Reg. Number already exists (excluding current member)
            if Member.objects.filter(redan_reg_number=redan_reg_number).exclude(id=member_id).exists():
                messages.error(request, 'A member with this REDAN registration number already exists.')
                return render(request, 'user/edit_member.html', {'member': member})
            
            # Update member data
            member.company_name = company_name
            member.company_email = company_email
            member.company_categories = ','.join(company_categories)  # Join categories with comma
            member.company_projects = company_projects  # New field
            member.address = address
            member.rc_no = rc_no
            member.md_phone_number = md_phone_number
            member.national_first_registered = datetime.strptime(
                national_first_registered, '%Y-%m-%d'
            ).date()
            member.redan_reg_number = redan_reg_number  # New field
            member.certificate_issued_date = datetime.strptime(
                certificate_issued_date, '%Y-%m-%d'
            ).date()
            member.enugu_first_registered = datetime.strptime(
                enugu_first_registered, '%Y-%m-%d'
            ).date()
            
            # Update files if provided
            if request.FILES.get('md_picture'):
                member.md_picture = request.FILES.get('md_picture')
            if request.FILES.get('certificate_picture'):
                member.certificate_picture = request.FILES.get('certificate_picture')
            if request.FILES.get('project_images'):  # New field
                member.project_images = request.FILES.get('project_images')
            
            # The model's save method handles certificate expiry date calculation
            member.save()
            messages.success(request, f'Member "{member.company_name}" updated successfully.')
            return redirect('member_detail', member_id=member.id)
            
        except Exception as e:
            messages.error(request, f'Error updating member: {str(e)}')
    
    context = {
        'member': member,
        'today': timezone.now().date()
    }
    return render(request, 'user/edit_member.html', context)


@login_required
def member_detail(request, member_id):
    """View member details"""
    member = get_object_or_404(Member, id=member_id)
    context = {
        'member': member,
    }
    return render(request, 'user/member_detail.html', context)




# @login_required
# @admin_required
# def edit_member(request, member_id):
#     """Edit member information"""
#     member = get_object_or_404(Member, id=member_id)
    
#     if request.method == 'POST':
#         try:
#             # Get form data
#             company_name = request.POST.get('company_name')
#             company_email = request.POST.get('company_email')
#             company_categories = request.POST.getlist('company_categories')  # Changed to getlist
#             address = request.POST.get('address')
#             rc_no = request.POST.get('rc_no')
#             md_phone_number = request.POST.get('md_phone_number')
#             national_first_registered = request.POST.get('national_first_registered')
#             certificate_issued_date = request.POST.get('certificate_issued_date')
#             enugu_first_registered = request.POST.get('enugu_first_registered')
            
#             # Validate required fields
#             if not all([company_name, company_email, address, rc_no, 
#                        md_phone_number, national_first_registered, certificate_issued_date, 
#                        enugu_first_registered]):
#                 messages.error(request, 'All fields are required.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Validate at least one category is selected
#             if not company_categories:
#                 messages.error(request, 'Please select at least one company category.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Check if RC number already exists (excluding current member)
#             if Member.objects.filter(rc_no=rc_no).exclude(id=member_id).exists():
#                 messages.error(request, 'A member with this RC number already exists.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Check if company email already exists (excluding current member)
#             if Member.objects.filter(company_email=company_email).exclude(id=member_id).exists():
#                 messages.error(request, 'A member with this email address already exists.')
#                 return render(request, 'user/edit_member.html', {'member': member})
            
#             # Update member data
#             member.company_name = company_name
#             member.company_email = company_email
#             member.company_categories = ','.join(company_categories)  # Join categories with comma
#             member.address = address
#             member.rc_no = rc_no
#             member.md_phone_number = md_phone_number
#             member.national_first_registered = datetime.strptime(
#                 national_first_registered, '%Y-%m-%d'
#             ).date()
#             member.certificate_issued_date = datetime.strptime(
#                 certificate_issued_date, '%Y-%m-%d'
#             ).date()
#             member.enugu_first_registered = datetime.strptime(
#                 enugu_first_registered, '%Y-%m-%d'
#             ).date()
            
#             # Update files if provided
#             if request.FILES.get('md_picture'):
#                 member.md_picture = request.FILES.get('md_picture')
#             if request.FILES.get('certificate_picture'):
#                 member.certificate_picture = request.FILES.get('certificate_picture')
            
#             # The model's save method handles certificate expiry date calculation
#             member.save()
#             messages.success(request, f'Member "{member.company_name}" updated successfully.')
#             return redirect('member_detail', member_id=member.id)
            
#         except Exception as e:
#             messages.error(request, f'Error updating member: {str(e)}')
    
#     context = {
#         'member': member,
#         'today': timezone.now().date()
#     }
#     return render(request, 'user/edit_member.html', context)


@login_required
@admin_required 
def delete_member(request, member_id):
    """Delete a member"""
    member = get_object_or_404(Member, id=member_id)
    
    if request.method == 'POST':
        company_name = member.company_name
        
        # Delete associated files
        if member.md_picture and os.path.exists(member.md_picture.path):
            os.remove(member.md_picture.path)
        if member.certificate_picture and os.path.exists(member.certificate_picture.path):
            os.remove(member.certificate_picture.path)
        
        member.delete()
        messages.success(request, f'Member "{company_name}" deleted successfully.')
        return redirect('members_list')
    
    context = {
        'member': member,
    }
    return render(request, 'user/delete_member.html', context)

@require_POST
@login_required
def renew_certificate(request, member_id):
    """Renew member certificate"""
    member = get_object_or_404(Member, id=member_id)
    
    if not member.can_renew_certificate:
        messages.error(request, 'Certificate cannot be renewed at this time.')
        return redirect('member_detail', member_id=member.id)
    
    try:
        if member.renew_certificate():
            messages.success(request, f'Certificate for "{member.company_name}" has been renewed successfully. New expiry date: {member.certificate_expiry_date.strftime("%B %d, %Y")}')
        else:
            messages.error(request, 'Failed to renew certificate. Please contact support.')
    except Exception as e:
        messages.error(request, f'Error renewing certificate: {str(e)}')
    
    return redirect('member_detail', member_id=member.id)



# =====================FINANCES==================================
@login_required
def financial_dashboard(request):
    """Dashboard showing financial overview"""
    financial_summary = CompanyBalance.get_financial_summary()
    
    # Recent transactions
    recent_income = Income.objects.all()[:5]
    recent_expenses = Expense.objects.all()[:5]
    
    context = {
        'financial_summary': financial_summary,
        'recent_income': recent_income,
        'recent_expenses': recent_expenses,
    }
    return render(request, 'user/finance_dashboard.html', context)



@login_required
def income_list(request):
    """List all income records"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    income_records = Income.objects.all()
    
    if search_query:
        income_records = income_records.filter(
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(payer_name__icontains=search_query) |
            Q(payer_member__company_name__icontains=search_query)
        )
    
    if category_filter:
        income_records = income_records.filter(category=category_filter)
        
    payer_filter = request.GET.get('payer', '')
    if payer_filter:
        income_records = income_records.filter(payer_name__icontains=payer_filter)
    
    paginator = Paginator(income_records, 20)
    page_number = request.GET.get('page')
    income_records = paginator.get_page(page_number)
    
    context = {
        'income_records': income_records,
        'search_query': search_query,
        'category_filter': category_filter,
        'income_categories': Income.INCOME_CATEGORIES,
        'total_income': Income.get_total_income(),
    }
    return render(request, 'user/income_list.html', context)

@login_required
def add_income(request):
    """Add new income record"""
    if request.method == 'POST':
        try:
            category = request.POST.get('category')
            amount = Decimal(request.POST.get('amount'))
            date = request.POST.get('date')
            description = request.POST.get('description', '')
            
            # Handle payer information
            payer_name = None
            payer_member = None
            
            if category == 'enugu_validation':
                # For Enugu validation fee, get member from dropdown
                payer_member_id = request.POST.get('payer_member')
                if payer_member_id:
                    payer_member = get_object_or_404(Member, id=payer_member_id)
            else:
                # For other categories, get manual payer name
                payer_name = request.POST.get('payer_name', '').strip()
            
            # Validate required fields
            if not category or not amount or not date:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'user/add_income.html', {
                    'income_categories': Income.INCOME_CATEGORIES,
                    'members': Member.objects.filter(company_name__isnull=False).order_by('company_name')
                })
            
            # Create income record
            Income.objects.create(
                category=category,
                amount=amount,
                date=date,
                description=description,
                payer_name=payer_name,
                payer_member=payer_member
            )
            
            messages.success(request, f'Income record added successfully. Amount: ₦{amount:,.2f}')
            return redirect('income_list')
            
        except Exception as e:
            messages.error(request, f'Error adding income: {str(e)}')
    
    context = {
        'income_categories': Income.INCOME_CATEGORIES,
        'members': Member.objects.filter(company_name__isnull=False).order_by('company_name')
    }
    return render(request, 'user/add_income.html', context)

@login_required
def edit_income(request, income_id):
    """Edit existing income record"""
    income = get_object_or_404(Income, id=income_id)
    
    if request.method == 'POST':
        try:
            category = request.POST.get('category')
            amount = Decimal(request.POST.get('amount'))
            date = request.POST.get('date')
            description = request.POST.get('description', '')
            
            # Handle payer information
            payer_name = None
            payer_member = None
            
            if category == 'enugu_validation':
                # For Enugu validation fee, get member from dropdown
                payer_member_id = request.POST.get('payer_member')
                if payer_member_id:
                    payer_member = get_object_or_404(Member, id=payer_member_id)
            else:
                # For other categories, get manual payer name
                payer_name = request.POST.get('payer_name', '').strip()
            
            # Validate required fields
            if not category or not amount or not date:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'user/edit_income.html', {
                    'income': income,
                    'income_categories': Income.INCOME_CATEGORIES,
                    'members': Member.objects.filter(company_name__isnull=False).order_by('company_name')
                })
            
            # Update income record
            income.category = category
            income.amount = amount
            income.date = date
            income.description = description
            income.payer_name = payer_name
            income.payer_member = payer_member
            income.save()
            
            messages.success(request, f'Income record updated successfully. New Amount: ₦{amount:,.2f}')
            return redirect('income_list')
            
        except Exception as e:
            messages.error(request, f'Error updating income: {str(e)}')
    
    context = {
        'income': income,
        'income_categories': Income.INCOME_CATEGORIES,
        'members': Member.objects.filter(company_name__isnull=False).order_by('company_name')
    }
    return render(request, 'user/edit_income.html', context)

@login_required
def delete_income(request, income_id):
    """Delete income record"""
    income = get_object_or_404(Income, id=income_id)
    
    if request.method == 'POST':
        income.delete()
        messages.success(request, 'Income record deleted successfully.')
        return redirect('income_list')
    
    return render(request, 'user/delete_income.html', {'income': income})


@login_required
def expense_list(request):
    """List all expense records"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    expense_records = Expense.objects.all()
    
    if search_query:
        expense_records = expense_records.filter(
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    if category_filter:
        expense_records = expense_records.filter(category=category_filter)
    
    paginator = Paginator(expense_records, 20)
    page_number = request.GET.get('page')
    expense_records = paginator.get_page(page_number)
    
    context = {
        'expense_records': expense_records,
        'search_query': search_query,
        'category_filter': category_filter,
        'expense_categories': Expense.EXPENSE_CATEGORIES,
        'total_expenses': Expense.get_total_expenses(),
    }
    return render(request, 'user/expense_list.html', context)


@login_required
def add_expense(request):
    """Add new expense record"""
    if request.method == 'POST':
        try:
            category = request.POST.get('category')
            amount = Decimal(request.POST.get('amount'))
            date = request.POST.get('date')
            description = request.POST.get('description')
            
            # Validate required fields
            if not category or not amount or not date or not description:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'user/add_expense.html', {'expense_categories': Expense.EXPENSE_CATEGORIES})
            
            # Create expense record
            Expense.objects.create(
                category=category,
                amount=amount,
                date=date,
                description=description
            )
            
            messages.success(request, f'Expense record added successfully. Amount: ₦{amount:,.2f}')
            return redirect('expense_list')
            
        except Exception as e:
            messages.error(request, f'Error adding expense: {str(e)}')
    
    context = {
        'expense_categories': Expense.EXPENSE_CATEGORIES,
    }
    return render(request, 'user/add_expense.html', context)


@login_required
def edit_expense(request, expense_id):
    """Edit existing expense record"""
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        try:
            category = request.POST.get('category')
            amount = Decimal(request.POST.get('amount'))
            date = request.POST.get('date')
            description = request.POST.get('description')
            
            # Validate required fields
            if not category or not amount or not date or not description:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'user/edit_expense.html', {
                    'expense': expense,
                    'expense_categories': Expense.EXPENSE_CATEGORIES
                })
            
            # Update expense record (now including amount)
            expense.category = category
            expense.amount = amount
            expense.date = date
            expense.description = description
            expense.save()
            
            messages.success(request, f'Expense record updated successfully. New Amount: ₦{amount:,.2f}')
            return redirect('expense_list')
            
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')
    
    context = {
        'expense': expense,
        'expense_categories': Expense.EXPENSE_CATEGORIES,
    }
    return render(request, 'user/edit_expense.html', context)


@login_required
def delete_expense(request, expense_id):
    """Delete expense record"""
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense record deleted successfully.')
        return redirect('expense_list')
    
    return render(request, 'user/delete_expense.html', {'expense': expense})


# =============================Gallery==========================================

# @login_required
@login_required
@admin_required
def gallery_management(request):
    """View to display all gallery images for management"""
    gallery_images = Gallery.objects.all().order_by('order', '-created_at')
    
    context = {
        'gallery_images': gallery_images,
    }
    return render(request, 'user/gallery_management.html', context)


@login_required
@admin_required
def add_gallery_image(request):
    """View to add a new gallery image"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')
        order = request.POST.get('order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        if not image:
            messages.error(request, 'Please select an image to upload.')
            return redirect('gallery_management')
        
        try:
            # Create new gallery image
            gallery_image = Gallery.objects.create(
                title=title if title else None,
                description=description if description else None,
                image=image,
                order=int(order),
                is_active=is_active
            )
            
            messages.success(request, 'Gallery image added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding gallery image: {str(e)}')
    
    return redirect('gallery_management')


@login_required
@admin_required
def edit_gallery_image(request):
    """View to edit an existing gallery image"""
    if request.method == 'POST':
        image_id = request.POST.get('image_id')
        
        try:
            gallery_image = get_object_or_404(Gallery, id=image_id)
            
            # Update fields
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            order = request.POST.get('order', 0)
            is_active = request.POST.get('is_active') == 'on'
            new_image = request.FILES.get('image')
            
            gallery_image.title = title if title else None
            gallery_image.description = description if description else None
            gallery_image.order = int(order)
            gallery_image.is_active = is_active
            
            # Update image if new one is provided
            if new_image:
                gallery_image.image = new_image
            
            gallery_image.save()
            
            messages.success(request, 'Gallery image updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating gallery image: {str(e)}')
    
    return redirect('gallery_management')


@login_required
@admin_required
def delete_gallery_image(request):
    """View to delete a gallery image"""
    if request.method == 'POST':
        image_id = request.POST.get('image_id')
        
        try:
            gallery_image = get_object_or_404(Gallery, id=image_id)
            
            # Delete the image file from storage
            if gallery_image.image:
                gallery_image.image.delete(save=False)
            
            # Delete the database record
            gallery_image.delete()
            
            messages.success(request, 'Gallery image deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting gallery image: {str(e)}')
    
    return redirect('gallery_management')



# =============================Leadership===================================

@login_required
@admin_required
def executive_council_management(request):
    """Main view for managing executive council members"""
    executives = ExecutiveCouncil.objects.all()
    
    # Group executives by council type for better organization
    state_executives = executives.filter(council_type='state')
    zonal_executives = executives.filter(council_type='zonal')
    national_executives = executives.filter(council_type='national')
    
    context = {
        'executives': executives,
        'state_executives': state_executives,
        'zonal_executives': zonal_executives,
        'national_executives': national_executives,
        'council_types': ExecutiveCouncil.COUNCIL_TYPES,
    }
    
    return render(request, 'user/executive_council.html', context)

@require_http_methods(["POST"])
@login_required
@admin_required
def add_executive(request):
    """Add a new executive council member"""
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '').strip()
        company_occupation = request.POST.get('company_occupation', '').strip()
        council_type = request.POST.get('council_type', 'state')
        order = request.POST.get('order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        # Social media URLs
        facebook_url = request.POST.get('facebook_url', '').strip()
        twitter_url = request.POST.get('twitter_url', '').strip()
        linkedin_url = request.POST.get('linkedin_url', '').strip()
        
        # Validation
        if not name:
            messages.error(request, 'Name is required.')
            return redirect('executive_council_management')
        
        if not position:
            messages.error(request, 'Position is required.')
            return redirect('executive_council_management')
        
        # Create new executive
        executive = ExecutiveCouncil.objects.create(
            name=name,
            position=position,
            company_occupation=company_occupation,
            council_type=council_type,
            order=int(order) if order else 0,
            is_active=is_active,
            facebook_url=facebook_url if facebook_url else None,
            twitter_url=twitter_url if twitter_url else None,
            linkedin_url=linkedin_url if linkedin_url else None,
        )
        
        # Handle image upload
        if 'image' in request.FILES:
            executive.image = request.FILES['image']
            executive.save()
        
        messages.success(request, f'Executive "{name}" added successfully!')
        
    except Exception as e:
        messages.error(request, f'Error adding executive: {str(e)}')
    
    return redirect('executive_council_management')


@require_http_methods(["POST"])
@login_required
@admin_required
def edit_executive(request):
    """Edit an existing executive council member"""
    try:
        executive_id = request.POST.get('executive_id')
        executive = ExecutiveCouncil.objects.get(id=executive_id)
        
        # Update fields
        executive.name = request.POST.get('name', '').strip()
        executive.position = request.POST.get('position', '').strip()
        executive.company_occupation = request.POST.get('company_occupation', '').strip()
        executive.council_type = request.POST.get('council_type', 'state')
        executive.order = int(request.POST.get('order', 0))
        executive.is_active = request.POST.get('is_active') == 'on'
        
        # Update social media URLs
        executive.facebook_url = request.POST.get('facebook_url', '').strip() or None
        executive.twitter_url = request.POST.get('twitter_url', '').strip() or None
        executive.linkedin_url = request.POST.get('linkedin_url', '').strip() or None
        
        # Handle image upload
        if 'image' in request.FILES:
            # Delete old image if exists
            if executive.image:
                default_storage.delete(executive.image.path)
            executive.image = request.FILES['image']
        
        executive.save()
        messages.success(request, f'Executive "{executive.name}" updated successfully!')
        
    except ExecutiveCouncil.DoesNotExist:
        messages.error(request, 'Executive not found.')
    except Exception as e:
        messages.error(request, f'Error updating executive: {str(e)}')
    
    return redirect('executive_council_management')


@require_http_methods(["POST"])
@login_required
@admin_required
def delete_executive(request):
    """Delete an executive council member"""
    try:
        executive_id = request.POST.get('executive_id')
        executive = ExecutiveCouncil.objects.get(id=executive_id)
        
        # Delete image file if exists
        if executive.image:
            default_storage.delete(executive.image.path)
        
        executive_name = executive.name
        executive.delete()
        
        messages.success(request, f'Executive "{executive_name}" deleted successfully!')
        
    except ExecutiveCouncil.DoesNotExist:
        messages.error(request, 'Executive not found.')
    except Exception as e:
        messages.error(request, f'Error deleting executive: {str(e)}')
    
    return redirect('executive_council_management')


@login_required
@require_http_methods(["GET"])
def get_executive_data(request, executive_id):
    """Get executive data for AJAX requests (for modal population)"""
    try:
        executive = ExecutiveCouncil.objects.get(id=executive_id)
        data = {
            'id': executive.id,
            'name': executive.name,
            'position': executive.position,
            'company_occupation': executive.company_occupation or '',
            'council_type': executive.council_type,
            'order': executive.order,
            'is_active': executive.is_active,
            'facebook_url': executive.facebook_url or '',
            'twitter_url': executive.twitter_url or '',
            'linkedin_url': executive.linkedin_url or '',
        }
        return JsonResponse(data)
    except ExecutiveCouncil.DoesNotExist:
        return JsonResponse({'error': 'Executive not found'}, status=404)
    
    
# ====================FInancial Report==================================



@login_required
def financial_report(request):
    """
    Generate comprehensive financial report with filtering capabilities
    """
    # Get filter parameters
    transaction_type = request.GET.get('transaction_type', '')
    category_filter = request.GET.get('category', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    period = request.GET.get('period', '')
    search_query = request.GET.get('search', '')
    
    # Handle period shortcuts
    today = timezone.now().date()
    
    if period == 'this_month':
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    elif period == 'last_month':
        first_day_last_month = today.replace(day=1) - timedelta(days=1)
        start_date = first_day_last_month.replace(day=1)
        end_date = first_day_last_month
    elif period == 'this_year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    elif period == 'last_year':
        last_year = today.year - 1
        start_date = today.replace(year=last_year, month=1, day=1)
        end_date = today.replace(year=last_year, month=12, day=31)
    
    # Convert string dates to date objects
    if start_date and isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date and isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get all transactions and combine them
    income_queryset = Income.objects.all()
    expense_queryset = Expense.objects.all()
    
    # Apply filters
    if category_filter:
        income_queryset = income_queryset.filter(category=category_filter)
        expense_queryset = expense_queryset.filter(category=category_filter)
    
    if start_date:
        income_queryset = income_queryset.filter(date__gte=start_date)
        expense_queryset = expense_queryset.filter(date__gte=start_date)
    
    if end_date:
        income_queryset = income_queryset.filter(date__lte=end_date)
        expense_queryset = expense_queryset.filter(date__lte=end_date)
    
    if search_query:
        income_queryset = income_queryset.filter(
            Q(description__icontains=search_query) | 
            Q(category__icontains=search_query)
        )
        expense_queryset = expense_queryset.filter(
            Q(description__icontains=search_query) | 
            Q(category__icontains=search_query)
        )
    
    # Create unified transaction list
    transactions = []
    
    # Add income transactions
    if transaction_type != 'expense':
        for income in income_queryset:
            transactions.append({
                'date': income.date,
                'type': 'income',
                'category': income.category,
                'category_display': income.get_category_display(),
                'description': income.description,
                'amount': income.amount,
                'created_at': income.created_at,
            })
    
    # Add expense transactions
    if transaction_type != 'income':
        for expense in expense_queryset:
            transactions.append({
                'date': expense.date,
                'type': 'expense',
                'category': expense.category,
                'category_display': expense.get_category_display(),
                'description': expense.description,
                'amount': expense.amount,
                'created_at': expense.created_at,
            })
    
    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: (x['date'], x['created_at']), reverse=True)
    
    # Calculate running balance
    total_income = Income.get_total_income()
    total_expenses = Expense.get_total_expenses()
    current_balance = total_income - total_expenses
    
    running_balance = current_balance
    for transaction in transactions:
        transaction['running_balance'] = running_balance
        if transaction['type'] == 'income':
            running_balance -= transaction['amount']
        else:
            running_balance += transaction['amount']
    
    # Calculate period totals
    period_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    period_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    period_net = period_income - period_expenses
    
    # Get all categories for filter dropdown
    income_categories = Income.INCOME_CATEGORIES
    expense_categories = Expense.EXPENSE_CATEGORIES
    all_categories = list(income_categories) + list(expense_categories)
    
    # Get summary data
    financial_summary = CompanyBalance.get_financial_summary()
    
    context = {
        'filtered_transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': current_balance,
        'total_transactions': len(transactions),
        'period_income': period_income,
        'period_expenses': period_expenses,
        'period_net': period_net,
        'all_categories': all_categories,
        'transaction_type': transaction_type,
        'category_filter': category_filter,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
        'period': period,
        'search_query': search_query,
        'current_date': timezone.now(),
        'financial_summary': financial_summary,
    }
    
    return render(request, 'user/financial_report.html', context)



# =====================FORMS==========================
@login_required
@admin_required
def upload_form(request):
    """View for uploading a new form"""
    # Get 5 most recent forms for display
    recent_forms = FormUpload.objects.all().order_by('-created_at')[:5]
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        form_file = request.FILES.get('form_file')
        
        if not form_file:
            messages.error(request, "Please select a file to upload.")
            return redirect('upload_form')
        
        # Create new form upload
        form_upload = FormUpload(
            name=name,
            description=description,
            form_file=form_file
        )
        form_upload.save()
        
        messages.success(request, f"Form '{name}' has been uploaded successfully!")
        return redirect('forms_list')
    
    return render(request, "user/forms_upload.html", {
        'recent_forms': recent_forms
    })

@login_required
@admin_required
def forms_list(request):
    """View to display all uploaded forms"""
    forms = FormUpload.objects.all().order_by('-created_at')
    
    return render(request, "user/forms_list.html", {
        'forms': forms
    })

@login_required
@admin_required
def edit_form(request, form_id):
    """View for editing an existing form"""
    form = get_object_or_404(FormUpload, id=form_id)
    
    if request.method == 'POST':
        # Extract form data
        form.name = request.POST.get('name')
        form.description = request.POST.get('description')
        
        # Handle file upload if new file is provided
        if 'form_file' in request.FILES:
            form.form_file = request.FILES['form_file']
            
        form.save()
        messages.success(request, f"Form '{form.name}' updated successfully.")
        return redirect('forms_list')
    
    return render(request, 'user/form_edit.html', {'form': form})

@login_required
@admin_required
def delete_form(request, form_id):
    """View for deleting a form"""
    if request.method == 'POST':
        form = get_object_or_404(FormUpload, id=form_id)
        form_name = form.name
        form.delete()
        messages.success(request, f"Form '{form_name}' has been deleted.")
    
    return redirect('forms_list')


@login_required
def download_form(request, form_id):
    """Download a form file"""
    form = get_object_or_404(FormUpload, id=form_id)
    
    # Check if form has a file and the file exists
    if form.form_file and form.form_file.name:
        file_path = form.form_file.path
        
        if os.path.exists(file_path):
            # Get the file's content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Read the file
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type=content_type)
                
                # Get the original filename or use the form name with extension
                original_filename = os.path.basename(form.form_file.name)
                if not original_filename:
                    original_filename = f"{form.name}.{form.file_type.lower()}"
                
                response['Content-Disposition'] = f'attachment; filename="{original_filename}"'
                return response
        else:
            raise Http404("File not found on disk")
    else:
        raise Http404("No file associated with this form")






# ========================SECRETARY ADMIN=================================
# Add these views to your views.py file


@login_required
@admin_required
def secretary_list(request):
    """List all secretary admins"""
    secretaries = SecretaryAdmin.objects.all().order_by('-created_at')
    return render(request, 'user/secretary_list.html', {'secretaries': secretaries})

@login_required
@admin_required
def create_secretary(request):
    """Create a new secretary admin"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Validate required fields
        if not all([full_name, email, username, password]):
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'user/create_secretary.html')
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'user/create_secretary.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'user/create_secretary.html')
        
        try:
            with transaction.atomic():
                # Create user account
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=full_name.split()[0],
                    last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
                )
                
                # Create secretary admin profile
                secretary = SecretaryAdmin.objects.create(
                    user=user,
                    full_name=full_name,
                    email=email,
                    phone_number=phone_number,
                    created_by=request.user
                )
                
                messages.success(request, f'Secretary admin "{full_name}" created successfully!')
                return redirect('secretary_list')
                
        except Exception as e:
            messages.error(request, f'Error creating secretary admin: {str(e)}')
    
    return render(request, 'user/create_secretary.html')

@login_required
@admin_required
def edit_secretary(request, secretary_id):
    """Edit secretary admin details"""
    secretary = get_object_or_404(SecretaryAdmin, id=secretary_id)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        username = request.POST.get('username')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validate required fields
        if not all([full_name, email, username]):
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'user/edit_secretary.html', {'secretary': secretary})
        
        # Check if username or email already exists (excluding current user)
        if User.objects.filter(username=username).exclude(id=secretary.user.id).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'user/edit_secretary.html', {'secretary': secretary})
        
        if User.objects.filter(email=email).exclude(id=secretary.user.id).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'user/edit_secretary.html', {'secretary': secretary})
        
        try:
            with transaction.atomic():
                # Update user account
                secretary.user.username = username
                secretary.user.email = email
                secretary.user.first_name = full_name.split()[0]
                secretary.user.last_name = ' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
                secretary.user.is_active = is_active
                secretary.user.save()
                
                # Update secretary profile
                secretary.full_name = full_name
                secretary.email = email
                secretary.phone_number = phone_number
                secretary.is_active = is_active
                secretary.save()
                
                messages.success(request, f'Secretary admin "{full_name}" updated successfully!')
                return redirect('secretary_list')
                
        except Exception as e:
            messages.error(request, f'Error updating secretary admin: {str(e)}')
    
    return render(request, 'user/edit_secretary.html', {'secretary': secretary})

@login_required
@admin_required
def delete_secretary(request, secretary_id):
    """Delete secretary admin"""
    secretary = get_object_or_404(SecretaryAdmin, id=secretary_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                secretary.user.delete()  # This will also delete the secretary profile
                messages.success(request, f'Secretary admin "{secretary.full_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting secretary admin: {str(e)}')
    
    return redirect('secretary_list')

@login_required
@admin_required
def toggle_secretary_status(request, secretary_id):
    """Toggle secretary admin active status"""
    secretary = get_object_or_404(SecretaryAdmin, id=secretary_id)
    
    try:
        secretary.is_active = not secretary.is_active
        secretary.user.is_active = secretary.is_active
        secretary.save()
        secretary.user.save()
        
        status = "activated" if secretary.is_active else "deactivated"
        messages.success(request, f'Secretary admin "{secretary.full_name}" {status} successfully!')
    except Exception as e:
        messages.error(request, f'Error updating secretary status: {str(e)}')
    
    return redirect('secretary_list')

def generate_random_password(length=8):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@login_required
@admin_required
def reset_secretary_password(request, secretary_id):
    """Reset secretary admin password"""
    secretary = get_object_or_404(SecretaryAdmin, id=secretary_id)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        
        if not new_password:
            messages.error(request, 'New password is required.')
            return redirect('secretary_list')
        
        try:
            secretary.user.set_password(new_password)
            secretary.user.save()
            messages.success(request, f'Password reset for "{secretary.full_name}" successfully!')
        except Exception as e:
            messages.error(request, f'Error resetting password: {str(e)}')
    
    return redirect('secretary_list')



# ===========================secretary dashboard================================
@login_required
def secretary_dashboard(request):
    """Secretary-specific dashboard with limited access"""
    try:
        secretary = SecretaryAdmin.objects.get(user=request.user)
        if not secretary.is_active:
            messages.error(request, 'Your secretary account is inactive.')
            return redirect('signin')
    except SecretaryAdmin.DoesNotExist:
        messages.error(request, 'Access denied. You are not a secretary admin.')
        return redirect('user')
    
    # Get statistics for secretary dashboard
    from django.db.models import Sum
    
    total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    income_count = Income.objects.count()
    expense_count = Expense.objects.count()
    
    # Recent transactions
    recent_income = Income.objects.all()[:5]
    recent_expenses = Expense.objects.all()[:5]
    
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'income_count': income_count,
        'expense_count': expense_count,
        'recent_income': recent_income,
        'recent_expenses': recent_expenses,
        'secretary': secretary,
    }
    
    return render(request, 'user/secretary_dashboard.html', context)



def print_invoice(request, income_id):
    income = get_object_or_404(Income, id=income_id)
    return render(request, 'user/invoice_template.html', {'income': income})










@login_required
@admin_required
def send_individual_email(request, member_id):
    """Send individual email to a specific member"""
    member = get_object_or_404(Member, id=member_id)
    
    if not member.company_email:
        messages.error(request, f"Member {member.company_name} has no email address.")
        return redirect('members_list')
    
    if request.method == 'POST':
        custom_message = request.POST.get('custom_message', '').strip()
        
        success, message = send_certificate_expiry_email(member, custom_message)
        
        if success:
            messages.success(request, f"Email sent successfully to {member.company_name}")
        else:
            messages.error(request, f"Failed to send email: {message}")
        
        return redirect('members_list')
    
    # GET request - show email form
    email_type = "expired" if member.is_certificate_expired else "expiring"
    default_message = get_default_email_message(email_type, member)
    
    context = {
        'member': member,
        'email_type': email_type,
        'default_message': default_message,
    }
    
    return render(request, 'emails/send_individual.html', context)


@login_required
@admin_required
def send_bulk_email(request):
    """Send bulk emails to multiple members"""
    if request.method == 'POST':
        email_type = request.POST.get('email_type')  # 'expiring' or 'expired'
        custom_message = request.POST.get('custom_message', '').strip()
        
        # Get appropriate members based on email type
        if email_type == 'expiring':
            members = Member.objects.filter(
                certificate_expiry_date__isnull=False,
                company_email__isnull=False
            ).exclude(company_email='')
            members = [m for m in members if m.is_certificate_expiring_soon]
        elif email_type == 'expired':
            members = Member.objects.filter(
                certificate_expiry_date__isnull=False,
                company_email__isnull=False
            ).exclude(company_email='')
            members = [m for m in members if m.is_certificate_expired]
        else:
            messages.error(request, "Invalid email type selected.")
            return redirect('members_list')
        
        if not members:
            messages.warning(request, f"No members found with {email_type} certificates.")
            return redirect('members_list')
        
        # Send bulk emails
        results = send_bulk_certificate_emails(members, custom_message)
        
        # Show results
        success_count = len(results['success'])
        failed_count = len(results['failed'])
        
        if success_count > 0:
            messages.success(request, f"Successfully sent {success_count} emails.")
        
        if failed_count > 0:
            messages.error(request, f"Failed to send {failed_count} emails.")
        
        return redirect('members_list')
    
    # GET request - show bulk email form
    email_type = request.GET.get('type', 'expiring')
    
    # Get sample member for default message
    if email_type == 'expiring':
        members = Member.objects.filter(certificate_expiry_date__isnull=False)
        sample_member = next((m for m in members if m.is_certificate_expiring_soon), None)
    else:
        members = Member.objects.filter(certificate_expiry_date__isnull=False)
        sample_member = next((m for m in members if m.is_certificate_expired), None)
    
    default_message = get_default_email_message(email_type, sample_member)
    
    context = {
        'email_type': email_type,
        'default_message': default_message,
    }
    
    return render(request, 'emails/send_bulk.html', context)


@login_required
@admin_required
@require_http_methods(["GET"])
def get_email_preview(request):
    """AJAX endpoint to get email preview"""
    member_id = request.GET.get('member_id')
    email_type = request.GET.get('email_type', 'expiring')
    
    try:
        member = Member.objects.get(id=member_id) if member_id else None
        default_message = get_default_email_message(email_type, member)
        
        return JsonResponse({
            'success': True,
            'message': default_message
        })
    except Member.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Member not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })




# ==================MEMBERS EMAILING=========================


@login_required
@admin_required
def send_email_to_members(request):
    """View to display email form and handle sending emails to all members"""
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Simple validation
        if not subject or not message:
            messages.error(request, 'Both subject and message are required.')
            return render(request, 'user/send_email.html')
        
        # Use utils to send email
        success, result_message = send_email_to_all_members(subject, message)
        
        if success:
            messages.success(request, result_message)
            return redirect('send_email_to_members')
        else:
            messages.error(request, result_message)
            return render(request, 'user/send_email.html')
    
    # GET request - show form with member count
    member_emails = get_member_emails()
    member_count = len(member_emails)
    
    context = {
        'member_count': member_count,
    }
    
    return render(request, 'emails/send_email.html', context)

@login_required
@admin_required
@require_http_methods(["GET"])
def get_member_email_count(request):
    """Get current member email count"""
    member_emails = get_member_emails()
    member_count = len(member_emails)
    
    return JsonResponse({
        'count': member_count,
        'message': f'{member_count} members will receive this email'
    })

# Preview function removed - not needed