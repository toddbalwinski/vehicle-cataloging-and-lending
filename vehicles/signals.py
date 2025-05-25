from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.shortcuts import redirect

@receiver(user_logged_in)
def check_profile_completion(sender, user, request, **kwargs):
    if not user.username or not user.first_name or not user.last_name:
        return redirect('/complete_profile')  # Replace with your profile completion URL name