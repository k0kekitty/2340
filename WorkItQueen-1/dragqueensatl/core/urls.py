# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main views
    path('', views.home, name='home'),
    path('queens/', views.queens_list, name='queens_list'),
    path('queens/<int:queen_id>/', views.queen_detail, name='queen_detail'),
    path('queens/<int:queen_id>/follow/', views.follow_queen, name='follow_queen'),
    path('queens/<int:queen_id>/unfollow/', views.unfollow_queen, name='unfollow_queen'),
    
    # Performance URLs
    path('performances/', views.performances_list, name='performances_list'),
    path('performances/map/', views.performances_map, name='performances_map'),
    path('performances/create/', views.create_performance, name='create_performance'),
    path('performances/<int:performance_id>/', views.performance_detail, name='performance_detail'),
    path('performances/<int:performance_id>/edit/', views.edit_performance, name='edit_performance'),
    path('performances/<int:performance_id>/review/', views.submit_review, name='submit_review'),
    path('performances/<int:performance_id>/share/', views.share_performance, name='share_performance'),
    
    # Profile URLs
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('profile/media/', views.manage_media, name='manage_media'),
    path('profile/media/<int:media_id>/delete/', views.delete_media, name='delete_media'),
    
    # Group URLs
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/', views.my_groups, name='my_groups'),
    path('groups/discover/', views.discover_groups, name='discover_groups'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/manage/', views.manage_group, name='manage_group'),
    path('groups/<int:pk>/join/', views.join_group, name='join_group'),
    path('groups/<int:pk>/leave/', views.leave_group, name='leave_group'),
    path('groups/<int:group_id>/member/<int:member_id>/role/', views.change_role, name='change_role'),
    path('groups/<int:group_id>/member/<int:member_id>/remove/', views.remove_member, name='remove_member'),
    path('groups/<int:group_id>/invite/', views.invite_member, name='invite_member'),
    path('groups/<int:group_id>/invitation/<int:invitation_id>/cancel/', views.cancel_invitation, name='cancel_invitation'),
    path('groups/invitation/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
    path('groups/<int:group_id>/settings/', views.update_group_settings, name='update_group_settings'),
    path('groups/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    path('groups/<int:group_id>/members/', views.group_members, name='group_members'),
    path('groups/<int:group_id>/events/', views.group_events, name='group_events'),
    path('groups/<int:group_id>/gallery/', views.group_gallery, name='group_gallery'),
    
    # Group Event URLs
    path('groups/<int:group_id>/events/create/', views.create_group_event, name='create_group_event'),
    path('groups/<int:group_id>/events/<int:event_id>/', views.group_event_detail, name='group_event_detail'),
    path('groups/<int:group_id>/events/<int:event_id>/edit/', views.edit_group_event, name='edit_group_event'),
    path('groups/<int:group_id>/events/<int:event_id>/delete/', views.delete_group_event, name='delete_group_event'),
    path('groups/<int:group_id>/events/<int:event_id>/attend/', views.attend_event, name='attend_event'),
    path('groups/<int:group_id>/events/<int:event_id>/cancel/', views.cancel_attendance, name='cancel_attendance'),
    
    # Photo URLs
    path('groups/<int:group_id>/photos/upload/', views.upload_group_photo, name='upload_group_photo'),
    path('groups/<int:group_id>/photos/<int:photo_id>/delete/', views.delete_group_photo, name='delete_group_photo'),
    path('groups/<int:group_id>/events/<int:event_id>/photos/upload/', views.upload_event_photo, name='upload_event_photo'),
    path('groups/<int:group_id>/events/<int:event_id>/photos/<int:photo_id>/delete/', views.delete_event_photo, name='delete_event_photo'),
    path('api/check-performances/', views.check_upcoming_performances, name='check_upcoming_performances'),
    # Notifications
    path('notifications/', views.view_notifications, name='view_notifications'),
    path('performances/<int:performance_id>/delete/', views.delete_performance, name='delete_performance'),
    path('register/', views.register, name='register'),

    path('my_reviews/', views.my_reviews, name='my_reviews'),

    path('profile/update_picture/', views.update_profile_picture, name='update_profile_picture'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),


]