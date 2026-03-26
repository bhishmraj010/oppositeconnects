from django.contrib import admin
from django.urls import path, include
from accounts.views import home, create_profile, logout_user
from videochat.views import video_chat
from matchmaking.views import find_match
from accounts.views import logout_user

urlpatterns = [

    path('', home),

    path('admin/', admin.site.urls),

    path('profile/', create_profile),

    path('video/', video_chat),

    path('match/', find_match),

    path('accounts/', include('allauth.urls')),

   path('logout/', logout_user),

   
]