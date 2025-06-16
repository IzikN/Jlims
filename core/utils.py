from core.models import TestAssignment
from core.models import AuditTrail
import os
from django.conf import settings
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Invoice


def save_audit(user, action, details=""):
    AuditTrail.objects.create(user=user, action=action, details=details)



def calculate_total_price(client):
    assignments = TestAssignment.objects.filter(sample__client=client)
    total = sum(assign.parameter.price for assign in assignments)
    return total

def generate_invoice_pdf_and_email(invoice_id, request_user=None):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    template = get_template('core/invoice_template.html')
    html = template.render({'invoice': invoice})

    # Save PDF to media directory
    pdf_path = os.path.join(settings.MEDIA_ROOT, f'invoices/Invoice_{invoice.invoice_number}.pdf')
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    with open(pdf_path, "wb") as pdf_file:
        pisa.CreatePDF(html, dest=pdf_file)

    # Send email
    if invoice.client.email:
        email = EmailMessage(
            subject=f"Invoice #{invoice.invoice_number} from JaaGee Lab",
            body=f"Dear {invoice.client.name},\n\nPlease find attached your invoice for laboratory services.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invoice.client.email],
        )
        email.attach_file(pdf_path)
        email.send()

    # Optional audit
    if request_user:
        save_audit(request_user, "Generated and Emailed Invoice PDF", f"Invoice #{invoice.invoice_number}")

    return pdf_path

