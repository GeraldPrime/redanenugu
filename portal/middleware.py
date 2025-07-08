from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import SecretaryAdmin

class SecretaryAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if user is a secretary admin
        if request.user.is_authenticated:
            try:
                secretary = SecretaryAdmin.objects.get(user=request.user)
                request.is_secretary = True
                
                # Check if secretary account is active
                if not secretary.is_active:
                    messages.error(request, 'Your secretary account is inactive.')
                    return redirect('signin')
                
                # Define allowed URL patterns for secretary
                allowed_patterns = [
                    'secretary_dashboard',
                    'financial_dashboard',      # Added finance dashboard
                    'financial_report',         # Added financial report
                    'income_list',
                    'add_income',
                    'edit_income',
                    'delete_income',
                    'expense_list',
                    'add_expense',
                    'edit_expense',
                    'delete_expense',
                    'signout',
                    'members_list',
                    'create_member',
                    'member_detail',
                    # 'edit_member',
                    # 'delete_member',
                    'renew_certificate',
                    
                ]
                
                # Define allowed URL paths for secretary
                allowed_paths = [
                    '/members/',
                    '/financial/',              # Added finance dashboard path
                    '/financial-report/',       # Added financial report path
                    '/income/',
                    '/expenses/',
                    '/secretary-dashboard/',
                    '/signout/',
                    '/admin/signout/',  # In case you have admin prefix
                ]
                
                current_path = request.path
                current_url_name = None
                
                # Try to get current URL name
                try:
                    from django.urls import resolve
                    current_url_name = resolve(current_path).url_name
                except:
                    current_url_name = None
                
                # Check if current URL is allowed
                is_allowed = (
                    current_url_name in allowed_patterns or
                    any(current_path.startswith(path) for path in allowed_paths) or
                    current_path == '/'  # Allow home page
                )
                
                # If not allowed, redirect to secretary dashboard
                if not is_allowed:
                    messages.warning(request, 'You only have access to financial management.')
                    return redirect('secretary_dashboard')
                
            except SecretaryAdmin.DoesNotExist:
                request.is_secretary = False
        else:
            request.is_secretary = False
        
        response = self.get_response(request)
        return response