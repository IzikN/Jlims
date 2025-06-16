from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@receiver(post_save, sender=Client)
def send_client_token_email(sender, instance, created, **kwargs):
    if created and instance.email:
        subject = "🔐 Your JaaGee Lab Portal Access"
        context = {
            'name': instance.name,
            'client_id': instance.client_id,
            'access_token': instance.access_token,
            'url': f"https://your-domain.com/results/{instance.access_token}/",  # update with actual domain
        }

        html_message = render_to_string("emails/client_token_email.html", context)
        plain_message = strip_tags(html_message)

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instance.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
