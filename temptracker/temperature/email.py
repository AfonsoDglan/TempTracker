from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_email_alert(local_name, temp, data, email, id, temp_limit):
    subject = f'Alerta de Temperatura elevada em {local_name}'
    html_message = render_to_string('Email.html', {'local': local_name,
                                                   'temp': temp,
                                                   'data': data,
                                                   'id': id,
                                                   'temp_limit': temp_limit})
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = email
    email = EmailMultiAlternatives(subject, plain_message, from_email, [to])
    email.attach_alternative(html_message, 'text/html')
    email.send()
