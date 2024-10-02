"""
url mapping for user api
"""
from django.urls import path

from user import views

app_name = 'user' # used for reverse mapping
# as_view() =  drf convert class based view to django supported view
# name='create' - used fro reverse mapping
urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),
]

