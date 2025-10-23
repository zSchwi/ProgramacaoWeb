from django.urls import path
from .views import CustomLoginView, register_view
from .views import logout_view

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
]
