

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Performance(models.Model):
    title = models.CharField(max_length=200)
    queen_id = models.IntegerField()  # Temporary, until we add a model for the baddies (Drag Queens)
    queen_name = models.CharField(max_length=100)
    venue = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField()

    def __str__(self):
        return self.title

class Review(models.Model):
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars to rate da huzz
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user} for {self.performance}"


class DragQueen(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    #image = models.ImageField(upload_to=, blank=True)  #############IMAGE THINGY
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    merchandise = models.CharField(max_length=100)
    # create a list of performances objects, initialize a struct them and filter for reviews for said queen

class DragGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    #logo = models.ImageField(upload_to='group_logos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(DragQueen, through='GroupMembership')
    
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
