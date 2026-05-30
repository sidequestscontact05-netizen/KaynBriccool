import random
import sys
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import VerificationRecord


def generate_verification_code():
    return f'{random.randint(100000, 999999)}'


def send_verification_email(user, code):
    subject = _('SideQuest — Votre code de vérification')
    message = _(
        f'Bonjour {user.full_name},\n\n'
        f'Votre code de vérification SideQuest est : {code}\n\n'
        f'Ce code expire dans 10 minutes.\n\n'
        f'Si vous n\'avez pas demandé ce code, ignorez cet email.\n\n'
        f'— L\'équipe SideQuest'
    )
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        # Fallback: Print to console for server logs visibility
        print(f"\n[EMAIL FALLBACK] Code for {user.email}: {code} | Error: {e}", file=sys.stderr)
        # Also print to stdout to ensure it appears in standard logs
        print(f"\n========================================\n"
              f"CODE DE VÉRIFICATION POUR {user.email}: {code}\n"
              f"========================================\n", file=sys.stdout)


def create_phone_verification(user):
    code = generate_verification_code()
    expires_at = timezone.now() + timedelta(minutes=10)

    VerificationRecord.objects.filter(
        user=user,
        type=VerificationRecord.TypeChoices.PHONE,
        is_used=False,
    ).delete()

    verification = VerificationRecord.objects.create(
        user=user,
        type=VerificationRecord.TypeChoices.PHONE,
        code=code,
        expires_at=expires_at,
    )

    send_verification_email(user, code)
    return verification


def verify_phone_code(user, code):
    try:
        verification = VerificationRecord.objects.get(
            user=user,
            type=VerificationRecord.TypeChoices.PHONE,
            is_used=False,
            code=code,
        )
    except VerificationRecord.DoesNotExist:
        return False

    if verification.expires_at < timezone.now():
        return False

    verification.is_used = True
    verification.save(update_fields=['is_used'])

    user.phone_verified = True
    user.save(update_fields=['phone_verified'])

    return True


def create_email_verification(user):
    code = generate_verification_code()
    expires_at = timezone.now() + timedelta(minutes=10)

    VerificationRecord.objects.filter(
        user=user,
        type=VerificationRecord.TypeChoices.EMAIL,
        is_used=False,
    ).delete()

    verification = VerificationRecord.objects.create(
        user=user,
        type=VerificationRecord.TypeChoices.EMAIL,
        code=code,
        expires_at=expires_at,
    )

    subject = _('SideQuest — Vérifiez votre email')
    message = _(
        f'Bonjour {user.full_name},\n\n'
        f'Bienvenue sur SideQuest ! Pour activer votre compte, '
        f'utilisez le code de vérification suivant :\n\n'
        f'Code de vérification : {code}\n\n'
        f'Ce code expire dans 10 minutes.\n\n'
        f'Si vous n\'avez pas créé de compte SideQuest, ignorez cet email.\n\n'
        f'— L\'équipe SideQuest'
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"\n[EMAIL FALLBACK] Code for {user.email}: {code} | Error: {e}", file=sys.stderr)
        print(f"\n========================================\n"
              f"CODE DE VÉRIFICATION EMAIL POUR {user.email}: {code}\n"
              f"========================================\n", file=sys.stdout)

    return verification


def verify_email_code(user, code):
    try:
        verification = VerificationRecord.objects.get(
            user=user,
            type=VerificationRecord.TypeChoices.EMAIL,
            is_used=False,
            code=code,
        )
    except VerificationRecord.DoesNotExist:
        return False

    if verification.expires_at < timezone.now():
        return False

    verification.is_used = True
    verification.save(update_fields=['is_used'])

    user.email_verified = True
    user.save(update_fields=['email_verified'])

    return True


def send_form_email(user):
    form_url = 'https://docs.google.com/forms/d/e/1FAIpQLSfSttWHmdBFooMw9BNYwvBWdsUrEPT8qI12WuT5GvSVPW4jmw/viewform?usp=publish-editor'

    subject = _('SideQuest — Formulaire à remplir')
    message = _(
        f'Bonjour {user.full_name},\n\n'
        f'Merci de remplir ce formulaire SideQuest :\n'
        f'{form_url}\n\n'
        f'Votre réponse nous aidera à améliorer la plateforme.\n\n'
        f'— L\'équipe SideQuest'
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"\n[EMAIL FALLBACK] Form email for {user.email} | Error: {e}", file=sys.stderr)


def send_password_reset_email(user, reset_url):
    subject = _('SideQuest — Réinitialisation de votre mot de passe')
    message = _(
        f'Bonjour {user.full_name},\n\n'
        f'Vous avez demandé à réinitialiser votre mot de passe.\n\n'
        f'Cliquez sur le lien suivant pour définir un nouveau mot de passe :\n\n'
        f'{reset_url}\n\n'
        f'Ce lien expire dans 1 heure.\n\n'
        f'Si vous n\'avez pas demandé cette réinitialisation, ignorez cet email.\n\n'
        f'— L\'équipe SideQuest'
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
