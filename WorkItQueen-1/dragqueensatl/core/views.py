from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Avg, Count, Q
from django.forms import modelformset_factory
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from .models import (
    DragQueen, Performance, Review, ProfileMedia, 
    DragGroup, GroupMembership, UserPreference, Notification
)
from .forms import (
    ProfileForm, ProfileMediaForm, PerformanceForm, ReviewForm,
    GroupForm, SearchForm, CustomUserCreationForm
)

# Keep the static data for backward compatibility
# This can be gradually phased out as you add real data
QUEENS = [
    {
        'id': 1,
        'name': 'Violet Essence',
        'bio': 'Atlanta-based drag performer specializing in glamour and high-fashion looks. Performing for 5 years with a background in ballet.',
        'image': 'images/violet.jpg',
        'instagram': 'https://instagram.com',
        'twitter': 'https://twitter.com',
        'merchandise': 'https://etsy.com',
    },
    {
        'id': 2,
        'name': 'Ruby Delight',
        'bio': 'Comedy queen bringing laughs to Atlanta for over 7 years. Known for hilarious lip-syncs and audience interaction.',
        'image': 'images/ruby.jpg',
        'instagram': 'https://instagram.com',
        'twitter': 'https://twitter.com',
        'merchandise': 'https://etsy.com',
    },
    {
        'id': 3,
        'name': 'Sapphire Divine',
        'bio': 'Pageant queen with multiple titles across the Southeast. Specializes in stunning gowns and emotional performances.',
        'image': 'images/sapphire.jpg',
        'instagram': 'https://instagram.com',
        'twitter': 'https://twitter.com',
        'merchandise': 'https://etsy.com',
    },
]

# Home page
def home(request):
    """Home page view"""
    # Get real drag queens from database
    featured_queens = DragQueen.objects.all()[:3]  
    
    # If no queens in database yet, use the static ones
    if not featured_queens:
        featured_queens = QUEENS[:3]
        
    # Get upcoming performances
    upcoming_performances = Performance.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date', 'time')[:5]
    
    return render(request, 'core/home.html', {
        'featured_queens': featured_queens,
        'upcoming_performances': upcoming_performances,
    })

# User registration and account management
def register(request):
    """Register a new user"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user preferences
            UserPreference.objects.create(user=user)
            # Log the user in
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Drag Queens Atlanta!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# Queens views
def queens_list(request):
    """List all queens"""
    # Get queens from database
    db_queens = DragQueen.objects.all()
    
    # If database has queens, use those, otherwise use static data
    if db_queens:
        queens = db_queens
    else:
        queens = QUEENS
        
    return render(request, 'core/queens_list.html', {'queens': queens})

def queen_detail(request, queen_id):
    """Show details for a specific queen"""
    # Try to get queen from database
    try:
        queen = DragQueen.objects.get(id=queen_id)
        # Get upcoming performances for this queen
        performances = Performance.objects.filter(
            queen_id=queen.id,
            date__gte=timezone.now().date()
        ).order_by('date', 'time')
        
        # Get media for this queen
        media = ProfileMedia.objects.filter(profile=queen)
        
        # Check if user is following this queen
        is_following = False
        if request.user.is_authenticated:
            try:
                is_following = request.user.preferences.favorite_queens.filter(id=queen_id).exists()
            except UserPreference.DoesNotExist:
                pass
        
        return render(request, 'core/queen_detail.html', {
            'queen': queen,
            'performances': performances,
            'media': media,
            'is_following': is_following
        })
    except DragQueen.DoesNotExist:
        # Fall back to static data
        queen = next((q for q in QUEENS if q['id'] == queen_id), None)
        performances = Performance.objects.filter(drag_queen__id=queen_id)
        
        if not queen:
            messages.error(request, "Queen not found!")
            return redirect('queens_list')
        
        return render(request, 'core/queen_detail.html', {
            'queen': queen,
            'performances': performances,
        })

# Performance views
def performances_list(request):
    """List all performances with filtering options"""
    # Create search/filter form
    form = SearchForm(request.GET)
    
    # Start with all performances
    performances = Performance.objects.all()
    
    # Apply filters if the form is valid
    if form.is_valid():
        data = form.cleaned_data
        
        if data['search']:
            performances = performances.filter(
                Q(title__icontains=data['search']) |
                Q(description__icontains=data['search']) |
                Q(queen_name__icontains=data['search']) |
                Q(venue__icontains=data['search'])
            )
        
        if data['date_from']:
            performances = performances.filter(date__gte=data['date_from'])
        
        if data['date_to']:
            performances = performances.filter(date__lte=data['date_to'])
        
        if data['venue']:
            performances = performances.filter(venue__icontains=data['venue'])
        
        if data['location']:
            performances = performances.filter(
                Q(address__icontains=data['location']) |
                Q(venue__icontains=data['location'])
            )
    
    # Get unique venues for filter dropdown
    venues = Performance.objects.values_list('venue', flat=True).distinct()
    
    return render(request, 'core/performances_list.html', {
        'performances': performances,
        'venues': venues,
        'form': form,
    })

def performance_detail(request, performance_id):
    """Show details for a specific performance including reviews"""
    performance = get_object_or_404(Performance, id=performance_id)
    
    # Try to get the queen from database first
    if performance.queen_name:
        queen = performance.queen_name
    else:
        # Fall back to static data
        queen = next((q for q in QUEENS if q['id'] == performance.queen_id), None)
    
    # Get related performances (by same queen or at same venue)
    if performance.queen_name:
        related_performances = Performance.objects.filter(
            Q(queen_name=performance.queen_name) | Q(venue=performance.venue)
        ).exclude(id=performance_id)[:3]
    else:
        related_performances = Performance.objects.filter(
            Q(queen_id=performance.queen_id) | Q(venue=performance.venue)
        ).exclude(id=performance_id)[:3]
    
    # Check if the user has already reviewed this performance
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = Review.objects.filter(
            performance=performance, 
            user=request.user
        ).exists()
    
    return render(request, 'core/performance_detail.html', {
        'performance': performance,
        'queen': queen,
        'related_performances': related_performances,
        'user_has_reviewed': user_has_reviewed,
    })

@login_required
def create_performance(request):
    """Create a new performance (for drag queens only)"""
    # Check if user has a drag queen profile
    try:
        profile = DragQueen.objects.get(user=request.user)
    except DragQueen.DoesNotExist:
        messages.error(request, "You need to create a drag queen profile first!")
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = PerformanceForm(request.POST)
        if form.is_valid():
            performance = form.save(commit=False)
            performance.drag_queen = profile
            performance.queen_id = profile.id  # For backward compatibility
            performance.queen_name = profile.name
            performance.save()
            
            messages.success(request, "Performance created successfully!")
            
            # Notify followers
            notify_followers(profile, performance)
            
            return redirect('performance_detail', performance_id=performance.id)
    else:
        form = PerformanceForm()
    
    return render(request, 'performances/create_performance.html', {'form': form})

@login_required
def edit_performance(request, performance_id):
    """Edit an existing performance"""
    performance = get_object_or_404(Performance, id=performance_id)
    
    # Check if the user is the owner of this performance
    if not request.user.is_staff:
        try:
            profile = request.user.profile
            if performance.drag_queen != profile:
                messages.error(request, "You don't have permission to edit this performance!")
                return redirect('performance_detail', performance_id=performance_id)
        except:
            messages.error(request, "You don't have permission to edit this performance!")
            return redirect('performance_detail', performance_id=performance_id)
    
    if request.method == 'POST':
        form = PerformanceForm(request.POST, instance=performance)
        if form.is_valid():
            form.save()
            messages.success(request, "Performance updated successfully!")
            return redirect('performance_detail', performance_id=performance_id)
    else:
        form = PerformanceForm(instance=performance)
    
    return render(request, 'performances/edit_performance.html', {
        'form': form,
        'performance': performance
    })

def performances_map(request):
    """Show performances on a map"""
    # Get all performances with geo coordinates
    performances = Performance.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        date__gte=timezone.now().date()
    )
    
    return render(request, 'core/performances_map.html', {
        'performances': performances,
        'api_key': 'YOUR_GOOGLE_MAPS_API_KEY'  # You'll need to set this up
    })

# Review system
@login_required
def submit_review(request, performance_id):
    """Submit a review for a performance"""
    performance = get_object_or_404(Performance, id=performance_id)
    
    # Check if user has already reviewed this performance
    if Review.objects.filter(performance=performance, user=request.user).exists():
        messages.error(request, "You have already reviewed this performance!")
        return redirect('performance_detail', performance_id=performance_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.performance = performance
            review.save()
            
            messages.success(request, "Thank you for your review!")
            
            # Notify the drag queen about the new review
            if performance.drag_queen and performance.drag_queen.user:
                Notification.objects.create(
                    user=performance.drag_queen.user,
                    notification_type='REVIEW',
                    title='New Review Received',
                    message=f'{request.user.username} left a {review.rating}-star review on your "{performance.title}" performance.',
                    related_performance=performance
                )
            
            return redirect('performance_detail', performance_id=performance_id)
    else:
        form = ReviewForm()
    
    return render(request, 'core/submit_review.html', {
        'form': form,
        'performance': performance,
    })

# Profile management
@login_required
def create_profile(request):
    """Create a new drag queen profile"""
    # Check if user already has a profile
    try:
        existing_profile = DragQueen.objects.get(user=request.user)
        if existing_profile:
            return redirect('edit_profile')
    except DragQueen.DoesNotExist:
        pass  # Continue to create profile
    
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profile created successfully!")
            return redirect('profile_detail', pk=profile.id)
    else:
        form = ProfileForm()
    
    return render(request, 'profiles/create_profile.html', {'form': form})

@login_required
def edit_profile(request):
    """Edit existing drag queen profile"""
    try:
        profile = DragQueen.objects.get(user=request.user)
    except DragQueen.DoesNotExist:
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile_detail', pk=profile.id)
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'profiles/edit_profile.html', {'form': form})

def profile_detail(request, pk):
    """Public profile view"""
    profile = get_object_or_404(DragQueen, pk=pk)
    
    
    # Get performances linked to this queen
    performances = Performance.objects.filter(
        queen_id=profile.id,
        date__gte=timezone.now().date()
    ).order_by('date', 'time')
    
    # Get past performances with reviews
    past_performances = Performance.objects.filter(
    queen_id=profile.id,
    date__lt=timezone.now().date()
    ).annotate(
        review_count=Count('reviews'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-date')
    
    # Get media for this queen
    photos = ProfileMedia.objects.filter(profile=profile, media_type='PHOTO')
    videos = ProfileMedia.objects.filter(profile=profile, media_type='VIDEO')
    
    # Check if user is following this queen
    is_following = False
    if request.user.is_authenticated:
        try:
            is_following = request.user.preferences.favorite_queens.filter(id=pk).exists()
        except UserPreference.DoesNotExist:
            pass
    
    context = {
        'profile': profile,
        'performances': performances,
        'past_performances': past_performances,
        'photos': photos,
        'videos': videos,
        'is_following': is_following,
    }
    
    return render(request, 'profiles/profile_detail.html', context)

@login_required
@login_required
def manage_media(request):
    """Manage profile photos and videos"""
    try:
        profile = DragQueen.objects.get(user=request.user)
    except DragQueen.DoesNotExist:
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = ProfileMediaForm(request.POST, request.FILES)
        if form.is_valid():
            media = form.save(commit=False)
            media.profile = profile
            media.save()
            messages.success(request, "Media added successfully!")
            return redirect('manage_media')
    else:
        form = ProfileMediaForm()
    
    # Get existing media
    photos = ProfileMedia.objects.filter(profile=profile, media_type='PHOTO')
    videos = ProfileMedia.objects.filter(profile=profile, media_type='VIDEO')
    
    return render(request, 'profiles/manage_media.html', {
        'form': form,
        'photos': photos,
        'videos': videos,
        'profile': profile, 
    })


@login_required
def delete_media(request, media_id):
    """Delete a media item"""
    media = get_object_or_404(ProfileMedia, id=media_id)
    
    # Check if user owns this media
    try:
        if media.profile.user != request.user:
            messages.error(request, "You don't have permission to delete this media!")
            return redirect('manage_media')
    except:
        messages.error(request, "You don't have permission to delete this media!")
        return redirect('manage_media')
    
    media.delete()
    messages.success(request, "Media deleted successfully!")
    return redirect('manage_media')


# Add these functions to your views.py

@login_required
def follow_queen(request, queen_id):
    """Follow a drag queen to receive notifications"""
    queen = get_object_or_404(DragQueen, id=queen_id)
    
    # Get or create user preferences
    preferences, created = UserPreference.objects.get_or_create(user=request.user)
    
    # Add queen to favorites
    preferences.favorite_queens.add(queen)
    
    # Create notification for the queen
    if queen.user:
        Notification.objects.create(
            user=queen.user,
            notification_type='FOLLOW',
            title='New Follower',
            message=f'{request.user.username} is now following you!',
        )
    
    messages.success(request, f"You are now following {queen.name}! You'll receive notifications for their performances.")
    return redirect('queen_detail', queen_id=queen_id)

@login_required
def unfollow_queen(request, queen_id):
    """Unfollow a drag queen"""
    queen = get_object_or_404(DragQueen, id=queen_id)
    
    try:
        # Remove queen from favorites
        request.user.preferences.favorite_queens.remove(queen)
        messages.success(request, f"You have unfollowed {queen.name}.")
    except:
        messages.error(request, "An error occurred.")
    
    return redirect('queen_detail', queen_id=queen_id)

@login_required
def view_notifications(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read
    if request.GET.get('mark_read'):
        notifications.update(is_read=True)
    
    return render(request, 'notifications/notifications_list.html', {
        'notifications': notifications
    })

def notify_followers(queen, performance):
    """Notify followers about a new performance"""
    # Find all users following this queen
    followers = UserPreference.objects.filter(favorite_queens=queen)
    
    for follower in followers:
        # Create notification
        Notification.objects.create(
            user=follower.user,
            notification_type='PERFORMANCE',
            title='New Performance Added',
            message=f"{queen.name} has added a new performance: {performance.title} at {performance.venue} on {performance.date.strftime('%B %d, %Y')}.",
            related_performance=performance
        )
        
        # Send email notification if enabled
        if follower.notification_email:
            try:
                subject = f"New Performance by {queen.name}"
                message = f"""
                {queen.name} has added a new performance!
                
                Title: {performance.title}
                Date: {performance.date.strftime('%B %d, %Y')} at {performance.time.strftime('%I:%M %p')}
                Venue: {performance.venue}
                Address: {performance.address}
                
                Don't miss it!
                """
                from_email = "noreply@dragqueensatl.com"
                recipient_list = [follower.user.email]
                
                send_mail(subject, message, from_email, recipient_list)
            except:
                # Log email failure but continue
                pass

@login_required
def share_performance(request, performance_id):
    """Share a performance with a friend via email"""
    performance = get_object_or_404(Performance, id=performance_id)
    
    if request.method == 'POST':
        friend_email = request.POST.get('friend_email')
        message = request.POST.get('message', '')
        
        if friend_email:
            try:
                subject = f"{request.user.username} shared a drag performance with you"
                email_message = f"""
                {request.user.username} thought you might be interested in this drag performance:
                
                {performance.title} by {performance.queen_name}
                
                Date: {performance.date.strftime('%B %d, %Y')} at {performance.time.strftime('%I:%M %p')}
                Venue: {performance.venue}
                Address: {performance.address}
                
                {message}
                
                Check it out at: http://dragqueensatl.com/performances/{performance.id}/
                """
                from_email = "noreply@dragqueensatl.com"
                recipient_list = [friend_email]
                
                send_mail(subject, email_message, from_email, recipient_list)
                messages.success(request, f"Performance shared with {friend_email} successfully!")
            except:
                messages.error(request, "Failed to send email. Please try again.")
        else:
            messages.error(request, "Please provide a valid email address.")
        
        return redirect('performance_detail', performance_id=performance_id)
    
    return render(request, 'performances/share_performance.html', {
        'performance': performance
    })


# Group-related views

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    DragQueen, DragGroup, GroupMembership, GroupEvent, 
    GroupPhoto, EventPhoto, GroupInvitation, EventAttendee
)
from .forms import GroupForm, GroupEventForm, GroupPhotoForm, EventPhotoForm


@login_required
def create_group(request):
    """Create a new drag group"""
    try:
        profile = DragQueen.objects.get(user=request.user)
    except DragQueen.DoesNotExist:
        messages.error(request, "You need to create a drag queen profile first!")
        return redirect('create_profile')
    
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save()
            
            # Add creator as admin
            GroupMembership.objects.create(
                profile=profile,
                group=group,
                role='ADMIN'
            )
            
            messages.success(request, f"Group '{group.name}' created successfully!")
            return redirect('group_detail', pk=group.pk)
    else:
        form = GroupForm()
    
    return render(request, 'groups/create_group.html', {'form': form})


def group_detail(request, pk):
    """View group details including members, events, and photos"""
    group = get_object_or_404(DragGroup, pk=pk)
    members = GroupMembership.objects.filter(group=group).select_related('profile')
    
    # Check if current user is a member
    is_member = False
    is_admin = False
    
    if request.user.is_authenticated:
        try:
            profile = DragQueen.objects.get(user=request.user)
            membership = GroupMembership.objects.filter(profile=profile, group=group).first()
            if membership:
                is_member = True
                is_admin = membership.role == 'ADMIN'
        except DragQueen.DoesNotExist:
            pass
    
    # Get upcoming events
    upcoming_events = GroupEvent.objects.filter(
        group=group,
        date__gte=timezone.now().date()
    ).order_by('date', 'time')[:3]
    
    # Get past events
    past_events = GroupEvent.objects.filter(
        group=group,
        date__lt=timezone.now().date()
    ).order_by('-date')[:3]
    
    # Get all events count
    all_events_count = GroupEvent.objects.filter(group=group).count()
    
    # Get group photos
    group_photos = GroupPhoto.objects.filter(group=group).order_by('-uploaded_at')[:6]
    group_photos_count = GroupPhoto.objects.filter(group=group).count()
    
    # Get performers if applicable (for performance groups)
    performers = []
    if hasattr(group, 'is_performance_group') and group.is_performance_group:
        performers = members.filter(profile__performance_style__isnull=False)
    
    context = {
        'group': group,
        'members': members,
        'is_member': is_member,
        'is_admin': is_admin,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'all_events_count': all_events_count,
        'group_photos': group_photos,
        'group_photos_count': group_photos_count,
        'performers': performers,
    }
    
    return render(request, 'groups/group_detail.html', context)


@login_required
def manage_group(request, pk):
    """Manage group settings (admin only)"""
    group = get_object_or_404(DragGroup, pk=pk)
    
    # Check if user is admin
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
        
        if membership.role != 'ADMIN':
            messages.error(request, "You must be an admin to manage this group.")
            return redirect('group_detail', pk=pk)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be an admin to manage this group.")
        return redirect('group_detail', pk=pk)
    
    # Get pending invitations
    pending_invitations = GroupInvitation.objects.filter(group=group, accepted=False, expired=False)
    
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f"{group.name} has been updated successfully!")
            return redirect('group_detail', pk=pk)
    else:
        form = GroupForm(instance=group)
    
    context = {
        'group': group,
        'form': form,
        'pending_invitations': pending_invitations,
    }
    
    return render(request, 'groups/manage_group.html', context)


@login_required
def join_group(request, pk):
    """Join a group"""
    group = get_object_or_404(DragGroup, pk=pk)
    
    # Check if user has a profile
    try:
        profile = DragQueen.objects.get(user=request.user)
    except DragQueen.DoesNotExist:
        messages.error(request, "You need to create a drag queen profile first!")
        return redirect('create_profile')
    
    # Check if already a member
    if GroupMembership.objects.filter(profile=profile, group=group).exists():
        messages.info(request, f"You are already a member of {group.name}!")
        return redirect('group_detail', pk=pk)
    
    # Join the group
    GroupMembership.objects.create(
        profile=profile,
        group=group,
        role='MEMBER'
    )
    
    messages.success(request, f"You have successfully joined {group.name}!")
    return redirect('group_detail', pk=pk)


@login_required
def leave_group(request, pk):
    """Leave a group"""
    group = get_object_or_404(DragGroup, pk=pk)
    
    # Check if user has a profile
    try:
        profile = DragQueen.objects.get(user=request.user)
    except DragQueen.DoesNotExist:
        messages.error(request, "You need to create a drag queen profile first!")
        return redirect('create_profile')
    
    # Check if a member
    try:
        membership = GroupMembership.objects.get(profile=profile, group=group)
    except GroupMembership.DoesNotExist:
        messages.error(request, f"You are not a member of {group.name}!")
        return redirect('group_detail', pk=pk)
    
    # Check if last admin
    if membership.role == 'ADMIN':
        admin_count = GroupMembership.objects.filter(group=group, role='ADMIN').count()
        if admin_count == 1:
            messages.error(request, "You are the only admin. Please assign another admin before leaving.")
            return redirect('group_detail', pk=pk)
    
    # Leave the group
    membership.delete()
    messages.success(request, f"You have left {group.name}.")
    
    return redirect('queens_list')  # Redirect to queens list instead of the group detail


@login_required
def change_role(request, group_id, member_id):
    """Change a member's role in a group"""
    group = get_object_or_404(DragGroup, pk=group_id)
    membership = get_object_or_404(GroupMembership, pk=member_id, group=group)
    
    # Check if admin
    try:
        profile = DragQueen.objects.get(user=request.user)
        admin_membership = GroupMembership.objects.get(profile=profile, group=group, role='ADMIN')
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be an admin to change member roles.")
        return redirect('group_detail', pk=group_id)
    
    # Get the new role from the query parameters
    new_role = request.GET.get('role', '')
    if new_role not in ('ADMIN', 'MEMBER'):
        messages.error(request, "Invalid role specified.")
        return redirect('group_detail', pk=group_id)
    
    # Update the role
    membership.role = new_role
    membership.save()
    
    messages.success(request, f"{membership.profile.name}'s role has been updated to {new_role}.")
    return redirect('group_detail', pk=group_id)


@login_required
def remove_member(request, group_id, member_id):
    """Remove a member from a group"""
    group = get_object_or_404(DragGroup, pk=group_id)
    membership = get_object_or_404(GroupMembership, pk=member_id, group=group)
    
    # Check if admin
    try:
        profile = DragQueen.objects.get(user=request.user)
        admin_membership = GroupMembership.objects.get(profile=profile, group=group, role='ADMIN')
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be an admin to remove members.")
        return redirect('group_detail', pk=group_id)
    
    # Cannot remove yourself this way
    if membership.profile == profile:
        messages.error(request, "You cannot remove yourself. Use the leave group option instead.")
        return redirect('group_detail', pk=group_id)
    
    # Remove the member
    member_name = membership.profile.name
    membership.delete()
    
    messages.success(request, f"{member_name} has been removed from {group.name}.")
    return redirect('group_detail', pk=group_id)


@login_required
def invite_member(request, group_id):
    """Invite a new member to the group"""
    group = get_object_or_404(DragGroup, pk=group_id)
    
    # Check if admin
    try:
        profile = DragQueen.objects.get(user=request.user)
        admin_membership = GroupMembership.objects.get(profile=profile, group=group, role='ADMIN')
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be an admin to invite members.")
        return redirect('group_detail', pk=group_id)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        message = request.POST.get('message', '')
        
        if not email:
            messages.error(request, "Email is required.")
            return redirect('manage_group', pk=group_id)
        
        # Check if invitation already exists
        if GroupInvitation.objects.filter(group=group, email=email, accepted=False, expired=False).exists():
            messages.info(request, f"An invitation has already been sent to {email}.")
            return redirect('manage_group', pk=group_id)
        
        # Create the invitation
        invitation = GroupInvitation.objects.create(
            group=group,
            email=email,
            message=message,
            invited_by=profile
        )
        
        # Send email invitation
        try:
            subject = f"Invitation to join {group.name} on Drag Queens Atlanta"
            email_message = f"""
            {profile.name} has invited you to join the group "{group.name}" on Drag Queens Atlanta!
            
            {message}
            
            To accept this invitation, visit: {request.build_absolute_uri('/groups/invitation/')}{invitation.token}/
            
            The invitation will expire in 7 days.
            """
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]
            
            send_mail(subject, email_message, from_email, recipient_list)
            messages.success(request, f"Invitation sent to {email} successfully!")
        except:
            messages.warning(request, f"Invitation created, but there was a problem sending the email to {email}.")
        
        return redirect('manage_group', pk=group_id)
    
    return redirect('manage_group', pk=group_id)


@login_required
def cancel_invitation(request, group_id, invitation_id):
    """Cancel a pending group invitation"""
    group = get_object_or_404(DragGroup, pk=group_id)
    invitation = get_object_or_404(GroupInvitation, pk=invitation_id, group=group)
    
    # Check if admin
    try:
        profile = DragQueen.objects.get(user=request.user)
        admin_membership = GroupMembership.objects.get(profile=profile, group=group, role='ADMIN')
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be an admin to cancel invitations.")
        return redirect('group_detail', pk=group_id)
    
    invitation.delete()
    messages.success(request, f"Invitation to {invitation.email} has been cancelled.")
    
    return redirect('manage_group', pk=group_id)


def accept_invitation(request, token):
    """Accept a group invitation using the token"""
    try:
        invitation = GroupInvitation.objects.get(token=token, accepted=False, expired=False)
    except GroupInvitation.DoesNotExist:
        messages.error(request, "This invitation is invalid or has already been used.")
        return redirect('home')
    
    # Check if invitation is expired
    if invitation.is_expired:
        invitation.expired = True
        invitation.save()
        messages.error(request, "This invitation has expired.")
        return redirect('home')
    
    # If user is not logged in, redirect to login/register
    if not request.user.is_authenticated:
        # Store invitation token in session
        request.session['invitation_token'] = str(invitation.token)
        messages.info(request, "Please log in or register to accept this invitation.")
        return redirect('login')
    
    # Check if user has a drag queen profile
    try:
        profile = DragQueen.objects.get(user=request.user)
    except DragQueen.DoesNotExist:
        # Store invitation token in session and redirect to create profile
        request.session['invitation_token'] = str(invitation.token)
        messages.info(request, "Please create a drag queen profile to accept this invitation.")
        return redirect('create_profile')
    
    # Check if already a member
    if GroupMembership.objects.filter(profile=profile, group=invitation.group).exists():
        invitation.accepted = True
        invitation.save()
        messages.info(request, f"You are already a member of {invitation.group.name}.")
        return redirect('group_detail', pk=invitation.group.id)
    
    # Add user to the group
    GroupMembership.objects.create(
        profile=profile,
        group=invitation.group,
        role='MEMBER'
    )
    
    # Mark invitation as accepted
    invitation.accepted = True
    invitation.save()
    
    messages.success(request, f"You have successfully joined {invitation.group.name}!")
    return redirect('group_detail', pk=invitation.group.id)


@login_required
def delete_group(request, group_id):
    """Delete a group (admin only)"""
    group = get_object_or_404(DragGroup, pk=group_id)
    
    # Check if admin
    try:
        profile = DragQueen.objects.get(user=request.user)
        admin_membership = GroupMembership.objects.get(profile=profile, group=group, role='ADMIN')
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be an admin to delete this group.")
        return redirect('group_detail', pk=group_id)
    
    if request.method == 'POST':
        group_name = group.name
        group.delete()
        messages.success(request, f"The group '{group_name}' has been deleted.")
        return redirect('home')
    
    return redirect('group_detail', pk=group_id)


@login_required
def update_group_settings(request, group_id):
    """Update group settings (admin only)"""
    group = get_object_or_404(DragGroup, pk=group_id)
    
    # Check if admin
    try:
        profile = DragQueen.objects.get(user=request.user)
        admin_membership = GroupMembership.objects.get(profile=profile, group=group, role='ADMIN')
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be an admin to update group settings.")
        return redirect('group_detail', pk=group_id)
    
    if request.method == 'POST':
        group.is_public = 'is_public' in request.POST
        group.allow_member_posts = 'allow_member_posts' in request.POST
        group.allow_member_events = 'allow_member_events' in request.POST
        group.save()
        
        messages.success(request, "Group settings updated successfully!")
    
    return redirect('manage_group', pk=group_id)


@login_required
def create_group_event(request, group_id):
    """Create a new group event"""
    group = get_object_or_404(DragGroup, pk=group_id)
    
    # Check if the user can create events in this group
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
        
        # Check if user is admin or if members can create events
        if membership.role != 'ADMIN' and not group.allow_member_events:
            messages.error(request, "You don't have permission to create events in this group.")
            return redirect('group_detail', pk=group_id)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be a member of this group to create events.")
        return redirect('group_detail', pk=group_id)
    
    if request.method == 'POST':
        form = GroupEventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.group = group
            event.created_by = profile
            event.save()
            
            # Add creator as an attendee
            EventAttendee.objects.create(
                event=event,
                profile=profile,
                is_going=True
            )
            
            # Notify group members
            for member in GroupMembership.objects.filter(group=group).exclude(profile=profile):
                if member.profile.user:
                    try:
                        Notification.objects.create(
                            user=member.profile.user,
                            notification_type='GROUP_EVENT',
                            title='New Group Event',
                            message=f"{profile.name} has created a new event: {event.title} for {group.name}.",
                            related_event=event
                        )
                    except:
                        # If notification creation fails, continue anyway
                        pass
            
            messages.success(request, f"Event '{event.title}' created successfully!")
            return redirect('group_event_detail', group_id=group_id, event_id=event.id)
    else:
        form = GroupEventForm()
    
    context = {
        'group': group,
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    
    return render(request, 'groups/create_group_event.html', context)


def group_event_detail(request, group_id, event_id):
    """Show group event details"""
    group = get_object_or_404(DragGroup, pk=group_id)
    event = get_object_or_404(GroupEvent, pk=event_id, group=group)
    
    # Check if private event and user has access
    if event.is_private:
        is_member = False
        if request.user.is_authenticated:
            try:
                profile = DragQueen.objects.get(user=request.user)
                is_member = GroupMembership.objects.filter(profile=profile, group=group).exists()
            except DragQueen.DoesNotExist:
                pass
        
        if not is_member:
            messages.error(request, "This is a private event. You must be a member of the group to view it.")
            return redirect('group_detail', pk=group_id)
    
    # Check if user is a member
    is_member = False
    is_admin = False
    is_attending = False
    
    if request.user.is_authenticated:
        try:
            profile = DragQueen.objects.get(user=request.user)
            membership = GroupMembership.objects.filter(profile=profile, group=group).first()
            if membership:
                is_member = True
                is_admin = membership.role == 'ADMIN'
            
            # Check if attending
            is_attending = EventAttendee.objects.filter(event=event, profile=profile).exists()
        except DragQueen.DoesNotExist:
            pass
    
    # Get event photos
    event_photos = EventPhoto.objects.filter(event=event).order_by('-uploaded_at')
    
    # Get attendees
    attendees = EventAttendee.objects.filter(event=event, is_going=True).select_related('profile')
    maybe_attending = EventAttendee.objects.filter(event=event, is_going=False).select_related('profile')
    
    context = {
        'group': group,
        'event': event,
        'is_member': is_member,
        'is_admin': is_admin,
        'is_attending': is_attending,
        'event_photos': event_photos,
        'attendees': attendees,
        'maybe_attending': maybe_attending,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    
    return render(request, 'groups/group_event_detail.html', context)


@login_required
def edit_group_event(request, group_id, event_id):
    """Edit a group event"""
    group = get_object_or_404(DragGroup, pk=group_id)
    event = get_object_or_404(GroupEvent, pk=event_id, group=group)
    
    # Check if user can edit this event
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
        
        # Only admin or the creator can edit
        if membership.role != 'ADMIN' and event.created_by != profile:
            messages.error(request, "You don't have permission to edit this event.")
            return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be a member of this group to edit events.")
        return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    
    if request.method == 'POST':
        form = GroupEventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f"Event '{event.title}' updated successfully!")
            return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    else:
        form = GroupEventForm(instance=event)
    
    context = {
        'group': group,
        'event': event,
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    
    return render(request, 'groups/edit_group_event.html', context)


@login_required
def delete_group_event(request, group_id, event_id):
    """Delete a group event"""
    group = get_object_or_404(DragGroup, pk=group_id)
    event = get_object_or_404(GroupEvent, pk=event_id, group=group)
    
    # Check if user can delete this event
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
        
        # Only admin or the creator can delete
        if membership.role != 'ADMIN' and event.created_by != profile:
            messages.error(request, "You don't have permission to delete this event.")
            return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be a member of this group to delete events.")
        return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f"Event '{event_title}' has been deleted.")
        return redirect('group_detail', pk=group_id)
    
    return redirect('group_event_detail', group_id=group_id, event_id=event_id)


@login_required
def upload_event_photo(request, group_id, event_id):
    """Upload photos for a group event"""
    group = get_object_or_404(DragGroup, pk=group_id)
    event = get_object_or_404(GroupEvent, pk=event_id, group=group)
    
    # Check if user is a member
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be a member of this group to upload photos.")
        return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    
    if request.method == 'POST':
        form = EventPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.event = event
            photo.uploaded_by = profile
            photo.save()
            
            messages.success(request, "Photo uploaded successfully!")
            return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    else:
        form = EventPhotoForm()
    
    context = {
        'group': group,
        'event': event,
        'form': form,
    }
    
    return render(request, 'groups/upload_event_photo.html', context)


@login_required
def upload_group_photo(request, group_id):
    """Upload photos for a group"""
    group = get_object_or_404(DragGroup, pk=group_id)
    
    # Check if user is a member
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be a member of this group to upload photos.")
        return redirect('group_detail', pk=group_id)
    
    if request.method == 'POST':
        form = GroupPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.group = group
            photo.uploaded_by = profile
            photo.save()
            
            messages.success(request, "Photo uploaded successfully!")
            return redirect('group_detail', pk=group_id)
    else:
        form = GroupPhotoForm()
    
    context = {
        'group': group,
        'form': form,
    }
    
    return render(request, 'groups/upload_group_photo.html', context)


@login_required
def attend_event(request, group_id, event_id):
    """Mark attendance for a group event"""
    group = get_object_or_404(DragGroup, pk=group_id)
    event = get_object_or_404(GroupEvent, pk=event_id, group=group)
    
    # Check if user is a member
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be a member of this group to attend events.")
        return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    
    # Get attendance status from query parameter
    is_going = request.GET.get('status', 'going') == 'going'
    
    # Create or update attendance
    attendance, created = EventAttendee.objects.update_or_create(
        event=event,
        profile=profile,
        defaults={'is_going': is_going}
    )
    
    if created:
        if is_going:
            messages.success(request, f"You are now attending {event.title}!")
        else:
            messages.success(request, f"You might attend {event.title}.")
    else:
        if is_going:
            messages.success(request, f"Your attendance for {event.title} has been updated to going.")
        else:
            messages.success(request, f"Your attendance for {event.title} has been updated to maybe.")
    
    return redirect('group_event_detail', group_id=group_id, event_id=event_id)


@login_required
def cancel_attendance(request, group_id, event_id):
    """Cancel attendance for a group event"""
    group = get_object_or_404(DragGroup, pk=group_id)
    event = get_object_or_404(GroupEvent, pk=event_id, group=group)
    
    try:
        profile = DragQueen.objects.get(user=request.user)
        attendance = EventAttendee.objects.get(event=event, profile=profile)
        attendance.delete()
        
        messages.success(request, f"You are no longer attending {event.title}.")
    except (DragQueen.DoesNotExist, EventAttendee.DoesNotExist):
        messages.error(request, "You were not registered as attending this event.")
    
    return redirect('group_event_detail', group_id=group_id, event_id=event_id)

def group_members(request, group_id):
    """View all members of a group"""
    group = get_object_or_404(DragGroup, pk=group_id)
    members = GroupMembership.objects.filter(group=group).select_related('profile').order_by('profile__name')
    
    # Check if user is a member or admin
    is_member = False
    is_admin = False
    
    if request.user.is_authenticated:
        try:
            profile = DragQueen.objects.get(user=request.user)
            membership = GroupMembership.objects.filter(profile=profile, group=group).first()
            if membership:
                is_member = True
                is_admin = membership.role == 'ADMIN'
        except DragQueen.DoesNotExist:
            pass
    
    # For private groups, only members can view member list
    if hasattr(group, 'is_public') and not group.is_public and not is_member:
        messages.error(request, "This is a private group. You must be a member to view the members list.")
        return redirect('group_detail', pk=group_id)
    
    context = {
        'group': group,
        'members': members,
        'is_member': is_member,
        'is_admin': is_admin,
    }
    
    return render(request, 'groups/group_members.html', context)


def group_events(request, group_id):
    """View all events for a group"""
    group = get_object_or_404(DragGroup, pk=group_id)
    
    # Check if user is a member
    is_member = False
    is_admin = False
    
    if request.user.is_authenticated:
        try:
            profile = DragQueen.objects.get(user=request.user)
            membership = GroupMembership.objects.filter(profile=profile, group=group).first()
            if membership:
                is_member = True
                is_admin = membership.role == 'ADMIN'
        except DragQueen.DoesNotExist:
            pass
    
    # Get upcoming events
    upcoming_events = GroupEvent.objects.filter(
        group=group, 
        date__gte=timezone.now().date()
    ).order_by('date', 'time')
    
    # Get past events
    past_events = GroupEvent.objects.filter(
        group=group,
        date__lt=timezone.now().date()
    ).order_by('-date', '-time')
    
    # For private events, check access
    if not is_member:
        # Filter out private events for non-members
        upcoming_events = upcoming_events.filter(is_private=False)
        past_events = past_events.filter(is_private=False)
    
    context = {
        'group': group,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'is_member': is_member,
        'is_admin': is_admin,
    }
    
    return render(request, 'groups/group_events.html', context)


def group_gallery(request, group_id):
    """View all photos for a group"""
    group = get_object_or_404(DragGroup, pk=group_id)
    
    # Check if user is a member
    is_member = False
    is_admin = False
    
    if request.user.is_authenticated:
        try:
            profile = DragQueen.objects.get(user=request.user)
            membership = GroupMembership.objects.filter(profile=profile, group=group).first()
            if membership:
                is_member = True
                is_admin = membership.role == 'ADMIN'
        except DragQueen.DoesNotExist:
            pass
    
    # For private groups, check access to photos
    if hasattr(group, 'is_public') and not group.is_public and not is_member:
        messages.error(request, "This is a private group. You must be a member to view the photo gallery.")
        return redirect('group_detail', pk=group_id)
    
    # Get photos
    photos = GroupPhoto.objects.filter(group=group).order_by('-uploaded_at')
    
    # Get event photos if requested
    event_photos = []
    if 'include_events' in request.GET:
        event_ids = GroupEvent.objects.filter(group=group)
        if not is_member:
            # Filter private events for non-members
            event_ids = event_ids.filter(is_private=False)
        
        event_photos = EventPhoto.objects.filter(event__in=event_ids).order_by('-uploaded_at')
    
    context = {
        'group': group,
        'photos': photos,
        'event_photos': event_photos,
        'is_member': is_member,
        'is_admin': is_admin,
    }
    
    return render(request, 'groups/group_gallery.html', context)


@login_required
def delete_group_photo(request, group_id, photo_id):
    """Delete a group photo"""
    group = get_object_or_404(DragGroup, pk=group_id)
    photo = get_object_or_404(GroupPhoto, pk=photo_id, group=group)
    
    # Check if user is admin or the uploader
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
        
        if membership.role != 'ADMIN' and photo.uploaded_by != profile:
            messages.error(request, "You don't have permission to delete this photo.")
            return redirect('group_gallery', group_id=group_id)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be a member of this group to delete photos.")
        return redirect('group_gallery', group_id=group_id)
    
    if request.method == 'POST':
        photo.delete()
        messages.success(request, "Photo deleted successfully!")
    
    return redirect('group_gallery', group_id=group_id)


@login_required
def delete_event_photo(request, group_id, event_id, photo_id):
    """Delete an event photo"""
    group = get_object_or_404(DragGroup, pk=group_id)
    event = get_object_or_404(GroupEvent, pk=event_id, group=group)
    photo = get_object_or_404(EventPhoto, pk=photo_id, event=event)
    
    # Check if user is admin or the uploader
    try:
        profile = DragQueen.objects.get(user=request.user)
        membership = GroupMembership.objects.get(profile=profile, group=group)
        
        if membership.role != 'ADMIN' and photo.uploaded_by != profile:
            messages.error(request, "You don't have permission to delete this photo.")
            return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    except (DragQueen.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, "You must be a member of this group to delete photos.")
        return redirect('group_event_detail', group_id=group_id, event_id=event_id)
    
    if request.method == 'POST':
        photo.delete()
        messages.success(request, "Photo deleted successfully!")
    
    return redirect('group_event_detail', group_id=group_id, event_id=event_id)


def discover_groups(request):
    """Discover public groups"""
    # Get search terms
    search_query = request.GET.get('q', '')
    
    # Start with public groups
    groups = DragGroup.objects.filter(is_public=True)
    
    # Apply search if provided
    if search_query:
        groups = groups.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Get membership counts
    groups = groups.annotate(member_count=Count('members'))
    
    # Sort by member count by default
    groups = groups.order_by('-member_count')
    
    # If user is authenticated, get their groups for comparison
    user_groups = []
    if request.user.is_authenticated:
        try:
            profile = DragQueen.objects.get(user=request.user)
            user_groups = GroupMembership.objects.filter(profile=profile).values_list('group_id', flat=True)
        except DragQueen.DoesNotExist:
            pass
    
    context = {
        'groups': groups,
        'search_query': search_query,
        'user_groups': user_groups,
    }
    
    return render(request, 'groups/discover_groups.html', context)


def my_groups(request):
    """View groups the user is a member of"""
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to view your groups.")
        return redirect('login')
    
    try:
        profile = DragQueen.objects.get(user=request.user)
    except DragQueen.DoesNotExist:
        messages.error(request, "You need to create a drag queen profile first!")
        return redirect('create_profile')
    
    # Get memberships with their roles
    memberships = GroupMembership.objects.filter(profile=profile).select_related('group')
    
    # Group by role for display
    admin_groups = [m.group for m in memberships if m.role == 'ADMIN']
    member_groups = [m.group for m in memberships if m.role == 'MEMBER']
    
    context = {
        'admin_groups': admin_groups,
        'member_groups': member_groups,
    }
    
    return render(request, 'groups/my_groups.html', context)


    # core/views.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto-login after registering
            return redirect('create_profile')  # send them to create their profile
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

from .models import Review

@login_required
def my_reviews(request):
    """View all reviews the logged-in user has written."""
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'profiles/my_reviews.html', {
        'reviews': reviews
    })
