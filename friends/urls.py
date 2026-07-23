from django.urls import path
from . import views

urlpatterns = [
    path("", views.friends_list, name="friends_list"),
    path("request/<str:username>/", views.send_request, name="send_friend_request"),
    path("respond/<int:request_id>/", views.respond_request, name="respond_friend_request"),
    path("message/<str:username>/", views.message_thread, name="message_thread"),
    path("online/", views.online_status, name="online_status"),
    path("heartbeat/", views.heartbeat, name="heartbeat"),
]