from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('queens/', views.queens_list, name='queens_list'),
    path('queens/<int:queen_id>/', views.queen_detail, name='queen_detail'),
    path('performances/', views.performances_list, name='performances_list'),
    path('performances/<int:performance_id>/', views.performance_detail, name='performance_detail'),
    path('performances/<int:performance_id>/review/', views.submit_review, name='submit_review'),  # Add this
]



# urls.py in your app folder
from django.urls import path
from . import views

#from . import views, group_views

urlpatterns = [
    # Profile URLs
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('profile/media/', views.manage_media, name='manage_media'),
   
]
