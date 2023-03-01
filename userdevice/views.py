from django.shortcuts import render, redirect
from .models import DeviceInfo
import requests
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.views.generic.edit import FormView
from django.views.generic import View
from . forms import UserRegistrationForm
from django.contrib.auth import logout
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
import json
from django.core.mail import send_mail
from django.conf import settings
from .utils import get_ip_address
from django.contrib.gis.geoip2 import GeoIP2

# Create your views here..
class RegisterPage(FormView):
    template_name = 'register.html'
    form_class = UserRegistrationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            username = form.cleaned_data.get('username')
            messages.success(self.request, f'Account created for {username}.')
            return redirect('login')
            #login(self.request, user)
        return super(RegisterPage, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('login')
        return super(RegisterPage, self).get(*args, **kwargs)


class LoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    fields = ['username', 'password']

    def get_success_url(self):
        return reverse_lazy('home')


@login_required
def home(request):
    #get user ip info
    ip = get_ip_address(request)
    print(ip)
    user = request.user
    
    #get location with geoIP
    g = GeoIP2()
    location = g.city(ip)
    location_country = location["country_name"]
    location_city = location["city"]

    #get other device information with user_agent
    device_type = ""

    browser_type = ""
    browser_version = ""
    os_type = ""
    os_version = ""
    
    browser_type = request.user_agent.browser.family
    browser_version = request.user_agent.browser.version_string
    os_type = request.user_agent.os.family
    os_version = request.user_agent.os.version_string

    if request.user_agent.is_mobile:
        device_type = "Mobile"
    if request.user_agent.is_tablet:
        device_type = "Tablet"
    if request.user_agent.is_pc:
        device_type = "PC"

    context = {
        'user': user,
        'ip': ip,
        'device_type': device_type,
        'browser_type': browser_type,
        'browser_version': browser_version,
        'os_type': os_type,
        'os_version': os_version,
        'location_country': location_country,
        'location_city': location_city,
    }

    #check if user already has info stored and verify if it's same with current info
    try:
        exist = DeviceInfo.objects.get(user=user)
        if str(exist.ip_add) != str(ip) or str(exist.device) != str(device_type):
            print("NOTICED UNKNOWN LOCATION!")
            subject = 'Security Notice.'
            message = f'We have detected suspicious login attempt from an unrecognized ip location {location_country} {device_type} {os_type} {browser_version}. If it was not you, click on the link to secure your account.'
            to_email = exist.user.email
            from_email = settings.DEFAULT_FROM_EMAIL
            print(to_email, from_email)

            send_mail(
                subject,
                message,
                from_email,
                [to_email],
                fail_silently=False
            )

    except DeviceInfo.DoesNotExist:
        #save current info to model
        device  = device_type +" "+ os_type
        deviceinfo = DeviceInfo.objects.create(user=user, device=device, ip_add=ip)
        deviceinfo.save()
        return render(request, 'home.html', context)

    return render(request, 'home.html', context)


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(self.request, 'Logged out successfully.')
        return redirect('login')
