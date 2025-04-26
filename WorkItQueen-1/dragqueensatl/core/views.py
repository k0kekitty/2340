# core/views.py
from django.shortcuts import render, get_object_or_404, redirect  # Updated import
from django.contrib.auth.decorators import login_required
from core.models import Performance, Review, DragQueen
from django import forms
from .forms import ProfileForm
#from .forms import ProfileForm, ProfileMediaForm, ProductForm
from django.contrib import messages
from django.forms import modelformset_factory


# Static data for queens
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

# Static data for performances
PERFORMANCES = [
    {
        'id': 1,
        'title': 'Glitter & Gold Showcase',
        'queen_id': 1,
        'queen_name': 'Violet Essence',
        'venue': 'Starlight Lounge',
        'address': '123 Peachtree St, Atlanta, GA',
        'date': '2025-04-15',
        'time': '20:00',
        'description': 'A dazzling performance featuring the best of Atlanta drag.',
        'reviews': [
            {'user': 'DragFan22', 'rating': 5, 'comment': 'Amazing performance! Violet really knows how to work a crowd.'},
            {'user': 'AtlantaQueen', 'rating': 4, 'comment': 'Great energy and fantastic costumes.'},
        ]
    },
    {
        'id': 2,
        'title': 'Comedy Night Extravaganza',
        'queen_id': 2,
        'queen_name': 'Ruby Delight',
        'venue': 'Laughs & Drafts',
        'address': '456 Ponce de Leon Ave, Atlanta, GA',
        'date': '2025-04-20',
        'time': '21:00',
        'description': 'A hilarious night of comedy and drag performances.',
        'reviews': [
            {'user': 'ComedyLover', 'rating': 5, 'comment': 'I laughed so hard I cried! Ruby is the best!'},
            {'user': 'NightlifeATL', 'rating': 5, 'comment': 'This show is a must-see in Atlanta.'},
        ]
    },
    {
        'id': 3,
        'title': 'Elegant Evening',
        'queen_id': 3,
        'queen_name': 'Sapphire Divine',
        'venue': 'Crystal Ballroom',
        'address': '789 Piedmont Ave, Atlanta, GA',
        'date': '2025-04-25',
        'time': '19:30',
        'description': 'An evening of elegance and pageantry with Atlanta\'s premier drag talent.',
        'reviews': [
            {'user': 'DragEnthusiast', 'rating': 4, 'comment': 'Sapphire\'s gowns are absolutely stunning.'},
            {'user': 'AtlantaNights', 'rating': 5, 'comment': 'Such a professional performance. Worth every penny!'},
        ]
    },
]

def home(request):
    """Home page view"""
    featured_queens = QUEENS[:2]  # Just show first 2 queens
    upcoming_performances = Performance.objects.all()  # Show all performances
    return render(request, 'core/home.html', {
        'featured_queens': featured_queens,
        'upcoming_performances': upcoming_performances,
    })

@login_required  # Added decorator
def queens_list(request):
    """List all queens"""
    return render(request, 'core/queens_list.html', {'queens': QUEENS})
@login_required  # Added decorator
def queen_detail(request, queen_id):
    """Show details for a specific queen"""
    queen = next((q for q in QUEENS if q['id'] == queen_id), None)
    performances = Performance.objects.filter(queen_id=queen_id)
    return render(request, 'core/queen_detail.html', {
        'queen': queen,
        'performances': performances,
    })


def performances_list(request):
    """List all performances with filtering options"""
    date_filter = request.GET.get('date', '')
    venue_filter = request.GET.get('venue', '')

    filtered_performances = Performance.objects.all()  # Use database
    if date_filter:
        filtered_performances = filtered_performances.filter(date=date_filter)
    if venue_filter:
        filtered_performances = filtered_performances.filter(venue=venue_filter)

    venues = list(set(p.venue for p in Performance.objects.all()))

    return render(request, 'core/performances_list.html', {
        'performances': filtered_performances,
        'venues': venues,
        'date_filter': date_filter,
        'venue_filter': venue_filter,
    })


def performance_detail(request, performance_id):
    """Show details for a specific performance including reviews"""
    performance = get_object_or_404(Performance, id=performance_id)  # Use database
    queen = next((q for q in QUEENS if q['id'] == performance.queen_id), None)

    return render(request, 'core/performance_detail.html', {
        'performance': performance,
        'queen': queen,
    })

# New view for submitting reviews
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

@login_required
def submit_review(request, performance_id):
    performance = get_object_or_404(Performance, id=performance_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.performance = performance
            review.save()
            return redirect('performance_detail', performance_id=performance_id)
    else:
        form = ReviewForm()
    return render(request, 'core/submit_review.html', {
        'form': form,
        'performance': performance,
    })

@login_required
def create_profile(request):
    try:
        # if profile alr exisrs
        profile = request.user.profile
        return redirect('edit_profile')
    except:
        # if not
        if request.method == 'POST':
            form = ProfileForm(request.POST)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.user = request.user
                profile.save()
                messages.success(request, "Profile created successfully!")
                return redirect('profile_detail', pk=profile.pk)
        else:
            form = ProfileForm()
        
        return render(request, 'profiles/create_profile.html', {'form': form})

@login_required
def edit_profile(request):
    """Edit existing drag queen profile"""
    profile = get_object_or_404(DragQueenProfile, user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile_detail', pk=profile.pk)
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'profiles/edit_profile.html', {'form': form})

@login_required
def manage_media(request):
    """Manage profile photos and videos"""
    profile = get_object_or_404(DragQueenProfile, user=request.user)
    
    MediaFormSet = modelformset_factory(
        ProfileMedia, 
        form=ProfileMediaForm,
        extra=3,
        max_num=20
    )
    
    if request.method == 'POST':
        formset = MediaFormSet(
            request.POST, 
            request.FILES,
            queryset=ProfileMedia.objects.filter(profile=profile)
        )
        
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.profile = profile
                instance.save()
            
            # Handle deletion
            for obj in formset.deleted_objects:
                obj.delete()
                
            messages.success(request, "Media updated successfully!")
            return redirect('profile_detail', pk=profile.pk)
    else:
        formset = MediaFormSet(queryset=ProfileMedia.objects.filter(profile=profile))
    
    return render(request, 'profiles/manage_media.html', {'formset': formset})

def profile_detail(request, pk):
    """Public profile view"""
    profile = get_object_or_404(DragQueenProfile, pk=pk)
    media = profile.media.all()
    reviews = profile.reviews.all().order_by('-created_at')
    products = profile.products.filter(is_available=True)
    
    # Get average review rating
    avg_rating = profile.average_rating()
    
    context = {
        'profile': profile,
        'media': media,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'products': products,
    }
    
    return render(request, 'profiles/profile_detail.html', context)

@login_required
def manage_reviews(request):
    """View and manage reviews"""
    profile = get_object_or_404(DragQueenProfile, user=request.user)
    reviews = profile.reviews.all().order_by('-created_at')
    
    # Calculate review stats
    review_count = reviews.count()
    avg_rating = profile.average_rating()
    
    # Calculate ratings distribution
    ratings_dist = {}
    for i in range(1, 6):
        ratings_dist[i] = reviews.filter(rating=i).count()
    
    context = {
        'profile': profile,
        'reviews': reviews,
        'review_count': review_count,
        'avg_rating': avg_rating,
        'ratings_dist': ratings_dist,
    }
    
    return render(request, 'reviews/manage_reviews.html', context)
