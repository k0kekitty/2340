from django.core.management.base import BaseCommand
from core.models import Performance, Review
from django.contrib.auth.models import User
from datetime import datetime, time

class Command(BaseCommand):
    help = 'Populate the database with static performance and review data'

    def handle(self, *args, **kwargs):
        # Clear existing data
        Performance.objects.all().delete()
        Review.objects.all().delete()

        # Static data (copied from views.py)
        performances_data = [
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

        # Create or get users for reviews
        for perf_data in performances_data:
            # Create performance
            performance = Performance.objects.create(
                title=perf_data['title'],
                queen_id=perf_data['queen_id'],
                queen_name=perf_data['queen_name'],
                venue=perf_data['venue'],
                address=perf_data['address'],
                date=datetime.strptime(perf_data['date'], '%Y-%m-%d').date(),
                time=datetime.strptime(perf_data['time'], '%H:%M').time(),
                description=perf_data['description'],
            )

            # Create reviews
            for review_data in perf_data['reviews']:
                user, _ = User.objects.get_or_create(username=review_data['user'])
                Review.objects.create(
                    performance=performance,
                    user=user,
                    rating=review_data['rating'],
                    comment=review_data['comment'],
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with performances and reviews'))