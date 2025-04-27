from django.db import models
from django.contrib.auth.models import User
import uuid

class Performance(models.Model):
    title = models.CharField(max_length=200)
    queen_id = models.IntegerField()  # Temporary, until we add a model for the baddies (Drag Queens)
    queen_name = models.CharField(max_length=100)
    venue = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    ticket_link = models.URLField(blank=True)
    
    def __str__(self):
        return self.title

class Review(models.Model):
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user} for {self.performance}"

class DragQueen(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', null=True, blank=True)
    name = models.CharField(max_length=100)
    bio = models.TextField()
    performance_style = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    merchandise = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    
    def __str__(self):
        return self.name
    
    def average_rating(self):
        performances = Performance.objects.filter(queen_id=self.id)
        reviews = Review.objects.filter(performance__in=performances)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0

class DragGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.ImageField(upload_to='group_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(DragQueen, through='GroupMembership')
    is_public = models.BooleanField(default=True)
    allow_member_posts = models.BooleanField(default=False)
    allow_member_events = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    ROLES = (
        ('ADMIN', 'Administrator'),
        ('MEMBER', 'Member'),
    )
    
    profile = models.ForeignKey(DragQueen, on_delete=models.CASCADE)
    group = models.ForeignKey(DragGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default='MEMBER')
    joined_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('profile', 'group')
        
    def __str__(self):
        return f"{self.profile.name} - {self.group.name} - {self.get_role_display()}"

class ProfileMedia(models.Model):
    MEDIA_TYPES = (
        ('PHOTO', 'Photo'),
        ('VIDEO', 'Video'),
    )
    
    profile = models.ForeignKey(DragQueen, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=5, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='profile_media/')
    youtube_url = models.URLField(blank=True)
    caption = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.profile.name} - {self.get_media_type_display()}"

class GroupEvent(models.Model):
    group = models.ForeignKey(DragGroup, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    venue = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='group_events/', blank=True, null=True)
    ticket_url = models.URLField(blank=True)
    is_private = models.BooleanField(default=False)
    created_by = models.ForeignKey(DragQueen, on_delete=models.SET_NULL, null=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.group.name} ({self.date})"

class GroupPhoto(models.Model):
    group = models.ForeignKey(DragGroup, on_delete=models.CASCADE, related_name='photos')
    file = models.ImageField(upload_to='group_photos/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(DragQueen, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.group.name} Photo ({self.id})"

class EventPhoto(models.Model):
    event = models.ForeignKey(GroupEvent, on_delete=models.CASCADE, related_name='photos')
    file = models.ImageField(upload_to='event_photos/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(DragQueen, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event.title} Photo ({self.id})"

class GroupInvitation(models.Model):
    group = models.ForeignKey(DragGroup, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    message = models.TextField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    invited_by = models.ForeignKey(DragQueen, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    accepted = models.BooleanField(default=False)
    expired = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.group.name}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.created_at + timezone.timedelta(days=7)

class EventAttendee(models.Model):
    event = models.ForeignKey(GroupEvent, on_delete=models.CASCADE, related_name='event_attendees')
    profile = models.ForeignKey(DragQueen, on_delete=models.CASCADE, related_name='attending_events')
    is_going = models.BooleanField(default=True)  # True for going, False for maybe
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('event', 'profile')
    
    def __str__(self):
        return f"{self.profile.name} - {self.event.title}"

class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    favorite_queens = models.ManyToManyField(DragQueen, related_name='followers', blank=True)
    notification_email = models.BooleanField(default=True)
    notification_24h = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('PERFORMANCE', 'Performance Reminder'),
        ('REVIEW', 'New Review'),
        ('FOLLOW', 'New Follower'),
        ('GROUP_EVENT', 'Group Event'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    related_performance = models.ForeignKey(Performance, on_delete=models.CASCADE, null=True, blank=True)
    related_event = models.ForeignKey(GroupEvent, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"