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

# Create your views here.

#function to get user ip address
def get_ip():
    response = requests.get('https://api64.ipify.org?format=json').json()
    return response['ip']

#function to get user basic location info using ip address
def get_location():
    ip_addr = get_ip()
    response = requests.get(f'https://ipapi.co/{ip_addr}/json/').json()
    location_data = {
        'ip': ip_addr,
        'city': response.get('city'),
        'region': response.get('region'),
        'country': response.get('country_name')
    }
    return location_data

'''class UserAPIView(LoginRequiredMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    #queryset = DeviceInfo.objects.all()
    serializer_class = UserSerializer
    template_name = 'blog/post_new.html'
    #permission_classes = [IsAuthenticated]
    lookup_fields = ['request.user']


    def get_queryset(self, request):
        return DeviceInfo.objects.get(user=request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)'''


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
    user_info = get_location()
    print(user_info)
    user = request.user

    #get device type from javascript
    if request.method == 'POST':
        #global data
        data = json.loads(request.body.decode('utf-8'))
        print(data['device_type'])

        #check if user already has info stored and verify if it's same with current info
        try:
            exist = DeviceInfo.objects.get(user=user)
            if str(exist.ip_add) != str(get_ip()) or str(exist.device) != str(data['device_type']):
                print("NOTICED UNKNOWN LOCATION!")
                subject = 'Security Notice.'
                message = f'We have detected suspicious login attempt from an unrecognized ip location {get_location()}. If it was not you, click on the link to secure your account.'
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
            deviceinfo = DeviceInfo.objects.create(user=user, device=data['device_type'], ip_add=get_ip())
            deviceinfo.save()
        return render(request, 'home.html')

    return render(request, 'home.html', {'userinfo': user_info, 'user': user,})



class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(self.request, 'Logged out successfully.')
        return redirect('login')