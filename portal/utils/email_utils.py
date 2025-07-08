from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_certificate_expiry_email(member, custom_message=None):
    """Send email notification for certificate expiry"""
    try:
        if not member.company_email:
            return False, "Member has no email address"
        
        # Determine email type based on certificate status
        if member.is_certificate_expired:
            subject = "Urgent: Certificate Renewal Required"
            email_type = "expired"
        elif member.is_certificate_expiring_soon:
            subject = "Certificate Renewal Reminder"
            email_type = "expiring"
        else:
            return False, "Certificate is not expiring or expired"
        
        # Prepare email context
        context = {
            'member': member,
            'company_name': member.company_name or "Valued Member",
            'days_remaining': member.days_until_expiry,
            'expiry_date': member.certificate_expiry_date,
            'email_type': email_type,
            'custom_message': custom_message,
        }
        
        # Render email content
        html_message = render_to_string('emails/certificate_renewal.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        success = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member.company_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if success:
            logger.info(f"Email sent successfully to {member.company_email}")
            return True, "Email sent successfully"
        else:
            logger.error(f"Failed to send email to {member.company_email}")
            return False, "Failed to send email"
            
    except Exception as e:
        logger.error(f"Error sending email to {member.company_email}: {str(e)}")
        return False, f"Error: {str(e)}"


def send_bulk_certificate_emails(members, custom_message=None):
    """Send bulk emails to multiple members"""
    results = {
        'success': [],
        'failed': [],
        'total': len(members)
    }
    
    for member in members:
        success, message = send_certificate_expiry_email(member, custom_message)
        if success:
            results['success'].append({
                'member': member.company_name or f"Member {member.id}",
                'email': member.company_email
            })
        else:
            results['failed'].append({
                'member': member.company_name or f"Member {member.id}",
                'email': member.company_email,
                'error': message
            })
    
    return results


def get_default_email_message(email_type, member=None):
    """Get default email message based on type"""
    if email_type == "expired":
        return f"""Dear {member.company_name if member else '[Company Name]'},

We hope this message finds you well.

This is to inform you that your certificate has expired. To continue enjoying our services and maintain your membership status, please contact our administration office immediately to renew your certificate.

Your prompt attention to this matter is highly appreciated.

Best regards,
REDAN Enugu State Chapter
Administration Team"""
    
    elif email_type == "expiring":
        days_text = f"{member.days_until_expiry} days" if member and member.days_until_expiry else "[X days]"
        return f"""Dear {member.company_name if member else '[Company Name]'},

We hope this message finds you well.

This is a friendly reminder that your certificate is set to expire in {days_text}. To avoid any disruption in your membership status, we kindly urge you to renew your certificate before the expiry date.

Please contact our administration office to complete your renewal process.

Thank you for your continued partnership with us.

Best regards,
REDAN Enugu State Chapter
Administration Team"""
    
    return ""



# utils/email_utils.py
from django.core.mail import EmailMessage
from django.conf import settings
from ..models import Member

def get_member_emails():
    """Get all valid member email addresses"""
    members = Member.objects.filter(
        company_email__isnull=False
    ).exclude(company_email='')
    
    return [member.company_email for member in members if member.company_email]

def send_email_to_all_members(subject, message):
    """Send email to all members - simple version"""
    try:
        recipient_emails = get_member_emails()
        
        if not recipient_emails:
            return False, "No members with valid email addresses found"
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            bcc=recipient_emails,
        )
        
        email.send()
        return True, f"Email sent to {len(recipient_emails)} members"
        
    except Exception as e:
        return False, f"Error sending email: {str(e)}"