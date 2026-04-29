from django.contrib import admin
from django.urls import path, include
from api import auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', auth_views.index_view, name='index'),
    path('login/', auth_views.login_view, name='login'),
    path('signup/', auth_views.signup_view, name='signup'),
    path('logout/', auth_views.logout_view, name='logout'),
]
