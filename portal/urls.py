from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from . import views
urlpatterns = [
    # frontend pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('redantv/', views.redantv, name='redantv'),
    path('downloadables/', views.downloadables, name='downloadables'),
    path('contact/', views.contact, name='contact'),
    # path('checkmembers/', views.checkmembers, name='checkmembers'),
    path('checkmembers/', views.checkmembers, name='checkmembers'),
    path('search-member/', views.search_member, name='search_member'),
    
    # =======================================================================
# ======================admin side start ===============================

    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('user/', views.user, name='user'),

    # Members CRUD
    
    path('members/', views.members_list, name='members_list'),
    path('members/create/', views.create_member, name='create_member'),
    path('members/<int:member_id>/', views.member_detail, name='member_detail'),
    path('members/<int:member_id>/edit/', views.edit_member, name='edit_member'),
    path('members/<int:member_id>/delete/', views.delete_member, name='delete_member'),
    path('members/<int:member_id>/renew/', views.renew_certificate, name='renew_certificate'),
    
    
    # Financial Dashboard
    path('financial/', views.financial_dashboard, name='financial_dashboard'),
    
    # Income URLs
    path('income/', views.income_list, name='income_list'),
    path('income/add/', views.add_income, name='add_income'),
    path('income/<int:income_id>/edit/', views.edit_income, name='edit_income'),
    path('income/<int:income_id>/delete/', views.delete_income, name='delete_income'),
    
    # Expense URLs
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    
    
    # Gallery
    
    # Gallery Management URLs
    path('gallery-management/', views.gallery_management, name='gallery_management'),
    path('add-gallery-image/', views.add_gallery_image, name='add_gallery_image'),
    path('edit-gallery-image/', views.edit_gallery_image, name='edit_gallery_image'),
    path('delete-gallery-image/', views.delete_gallery_image, name='delete_gallery_image'),
    
    
    # Executives
    # Main executive council management page
    path('executive-council-management/', views.executive_council_management, name='executive_council_management'),
    path('executive/add/', views.add_executive, name='add_executive'),
    path('executive/edit/', views.edit_executive, name='edit_executive'),
    path('executive/delete/', views.delete_executive, name='delete_executive'),
    path('executive/<int:executive_id>/data/', views.get_executive_data, name='get_executive_data'),
    
    # FInancial report
    path('financial-report/', views.financial_report, name='financial_report'),
    
    # Forms
    path('user/frontend-extras/forms/upload/', views.upload_form, name='upload_form'),
    path('user/frontend-extras/forms/', views.forms_list, name='forms_list'),
    path('user/frontend-extras/forms/<int:form_id>/edit/', views.edit_form, name='edit_form'),
    path('user/frontend-extras/forms/<int:form_id>/delete/', views.delete_form, name='delete_form'),
    path('forms/download/<int:form_id>/', views.download_form, name='download_form'),
    
    
    # Secretary Admin URLs
    path('secretary-admins/', views.secretary_list, name='secretary_list'),
    path('secretary-admins/create/', views.create_secretary, name='create_secretary'),
    path('secretary-admins/edit/<int:secretary_id>/', views.edit_secretary, name='edit_secretary'),
    path('secretary-admins/delete/<int:secretary_id>/', views.delete_secretary, name='delete_secretary'),
    path('secretary-admins/toggle-status/<int:secretary_id>/', views.toggle_secretary_status, name='toggle_secretary_status'),
    path('secretary-admins/reset-password/<int:secretary_id>/', views.reset_secretary_password, name='reset_secretary_password'),

    # sec
    path('secretary-dashboard/', views.secretary_dashboard, name='secretary_dashboard'),
    
    # invoiced
    path('invoice/<int:income_id>/', views.print_invoice, name='print_invoice'),
    
    
    # Email management URLs(MEMBERSHIP)
    # path('emails/', views.email_dashboard, name='email_dashboard'),
    path('emails/send/<int:member_id>/', views.send_individual_email, name='send_individual_email'),
    path('emails/bulk/', views.send_bulk_email, name='send_bulk_email'),
    path('emails/preview/', views.get_email_preview, name='get_email_preview'),
    
    # Email URLs
    path('send-email/', views.send_email_to_members, name='send_email_to_members'),
    path('get-member-email-count/', views.get_member_email_count, name='get_member_email_count'),
    

 ]
if settings.DEBUG:  # Only serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

