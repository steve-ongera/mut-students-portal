"""
Django management command to seed library management data
Usage: python manage.py seed_library_management
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from portal.models import (
    BookCategory, Book, BookBorrowing, Student, 
    AcademicYear, Semester, User
)


class Command(BaseCommand):
    help = 'Seeds library management data with real books'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting library management seeding...')
        
        # Create book categories
        categories = self.create_categories()
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} book categories'))
        
        # Create books
        books = self.create_books(categories)
        self.stdout.write(self.style.SUCCESS(f'Created {len(books)} books'))
        
        # Create book borrowings
        borrowings = self.create_borrowings(books)
        self.stdout.write(self.style.SUCCESS(f'Created {len(borrowings)} book borrowings'))
        
        self.stdout.write(self.style.SUCCESS('Library management seeding completed!'))

    def create_categories(self):
        """Create book categories"""
        categories_data = [
            {'name': 'Computer Science', 'code': 'CS', 'description': 'Books related to computer science and programming'},
            {'name': 'Information Technology', 'code': 'IT', 'description': 'IT infrastructure and systems books'},
            {'name': 'Software Engineering', 'code': 'SE', 'description': 'Software development and engineering books'},
            {'name': 'Data Science', 'code': 'DS', 'description': 'Data analysis, machine learning, and AI books'},
            {'name': 'Networking', 'code': 'NET', 'description': 'Computer networks and telecommunications'},
            {'name': 'Database Systems', 'code': 'DB', 'description': 'Database management and design'},
            {'name': 'Web Development', 'code': 'WEB', 'description': 'Web design and development'},
            {'name': 'Mobile Development', 'code': 'MOB', 'description': 'Mobile app development'},
            {'name': 'Cybersecurity', 'code': 'SEC', 'description': 'Information security and ethical hacking'},
            {'name': 'Business & Management', 'code': 'BUS', 'description': 'Business and management books'},
            {'name': 'Mathematics', 'code': 'MATH', 'description': 'Mathematics and statistics'},
            {'name': 'Engineering', 'code': 'ENG', 'description': 'General engineering books'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = BookCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            categories.append(category)
        
        return categories

    def create_books(self, categories):
        """Create 70 real books"""
        books_data = [
            # Computer Science
            {'isbn': '9780262033848', 'title': 'Introduction to Algorithms', 'author': 'Thomas H. Cormen, Charles E. Leiserson', 'publisher': 'MIT Press', 'year': 2009, 'edition': '3rd', 'category': 'CS', 'copies': 5},
            {'isbn': '9780134685991', 'title': 'Effective Java', 'author': 'Joshua Bloch', 'publisher': 'Addison-Wesley', 'year': 2018, 'edition': '3rd', 'category': 'CS', 'copies': 4},
            {'isbn': '9780132350884', 'title': 'Clean Code', 'author': 'Robert C. Martin', 'publisher': 'Prentice Hall', 'year': 2008, 'edition': '1st', 'category': 'CS', 'copies': 6},
            {'isbn': '9780135957059', 'title': 'The Pragmatic Programmer', 'author': 'David Thomas, Andrew Hunt', 'publisher': 'Addison-Wesley', 'year': 2019, 'edition': '2nd', 'category': 'CS', 'copies': 3},
            {'isbn': '9780596007126', 'title': 'Head First Design Patterns', 'author': 'Eric Freeman, Elisabeth Robson', 'publisher': "O'Reilly Media", 'year': 2004, 'edition': '1st', 'category': 'CS', 'copies': 4},
            
            # Data Science & AI
            {'isbn': '9781449369415', 'title': 'Python for Data Analysis', 'author': 'Wes McKinney', 'publisher': "O'Reilly Media", 'year': 2017, 'edition': '2nd', 'category': 'DS', 'copies': 5},
            {'isbn': '9781491952962', 'title': 'Introduction to Machine Learning with Python', 'author': 'Andreas C. Müller, Sarah Guido', 'publisher': "O'Reilly Media", 'year': 2016, 'edition': '1st', 'category': 'DS', 'copies': 4},
            {'isbn': '9781492032649', 'title': 'Hands-On Machine Learning', 'author': 'Aurélien Géron', 'publisher': "O'Reilly Media", 'year': 2019, 'edition': '2nd', 'category': 'DS', 'copies': 6},
            {'isbn': '9780262035613', 'title': 'Deep Learning', 'author': 'Ian Goodfellow, Yoshua Bengio', 'publisher': 'MIT Press', 'year': 2016, 'edition': '1st', 'category': 'DS', 'copies': 3},
            {'isbn': '9781617294433', 'title': 'Deep Learning with Python', 'author': 'François Chollet', 'publisher': 'Manning', 'year': 2017, 'edition': '1st', 'category': 'DS', 'copies': 4},
            
            # Software Engineering
            {'isbn': '9780134494166', 'title': 'Clean Architecture', 'author': 'Robert C. Martin', 'publisher': 'Prentice Hall', 'year': 2017, 'edition': '1st', 'category': 'SE', 'copies': 4},
            {'isbn': '9780201633610', 'title': 'Design Patterns', 'author': 'Erich Gamma, Richard Helm', 'publisher': 'Addison-Wesley', 'year': 1994, 'edition': '1st', 'category': 'SE', 'copies': 3},
            {'isbn': '9780132071482', 'title': 'Refactoring', 'author': 'Martin Fowler', 'publisher': 'Addison-Wesley', 'year': 2018, 'edition': '2nd', 'category': 'SE', 'copies': 5},
            {'isbn': '9780137081073', 'title': 'The Clean Coder', 'author': 'Robert C. Martin', 'publisher': 'Prentice Hall', 'year': 2011, 'edition': '1st', 'category': 'SE', 'copies': 3},
            {'isbn': '9780321344755', 'title': 'Test Driven Development', 'author': 'Kent Beck', 'publisher': 'Addison-Wesley', 'year': 2002, 'edition': '1st', 'category': 'SE', 'copies': 3},
            
            # Web Development
            {'isbn': '9781491918661', 'title': 'Learning Web Design', 'author': 'Jennifer Niederst Robbins', 'publisher': "O'Reilly Media", 'year': 2018, 'edition': '5th', 'category': 'WEB', 'copies': 4},
            {'isbn': '9781491978917', 'title': 'Eloquent JavaScript', 'author': 'Marijn Haverbeke', 'publisher': 'No Starch Press', 'year': 2018, 'edition': '3rd', 'category': 'WEB', 'copies': 5},
            {'isbn': '9781119067399', 'title': 'HTML and CSS: Design and Build Websites', 'author': 'Jon Duckett', 'publisher': 'Wiley', 'year': 2011, 'edition': '1st', 'category': 'WEB', 'copies': 6},
            {'isbn': '9781491957660', 'title': 'Learning React', 'author': 'Alex Banks, Eve Porcello', 'publisher': "O'Reilly Media", 'year': 2020, 'edition': '2nd', 'category': 'WEB', 'copies': 4},
            {'isbn': '9781491962022', 'title': 'Full Stack Python', 'author': 'Matt Makai', 'publisher': 'Matt Makai', 'year': 2017, 'edition': '1st', 'category': 'WEB', 'copies': 3},
            
            # Database Systems
            {'isbn': '9780321884497', 'title': 'Database System Concepts', 'author': 'Abraham Silberschatz, Henry Korth', 'publisher': 'McGraw-Hill', 'year': 2019, 'edition': '7th', 'category': 'DB', 'copies': 5},
            {'isbn': '9780134093413', 'title': 'Database Management Systems', 'author': 'Raghu Ramakrishnan, Johannes Gehrke', 'publisher': 'McGraw-Hill', 'year': 2003, 'edition': '3rd', 'category': 'DB', 'copies': 4},
            {'isbn': '9780596007126', 'title': 'SQL Queries for Mere Mortals', 'author': 'John Viescas, Michael Hernandez', 'publisher': 'Addison-Wesley', 'year': 2018, 'edition': '4th', 'category': 'DB', 'copies': 3},
            {'isbn': '9781449373320', 'title': 'Designing Data-Intensive Applications', 'author': 'Martin Kleppmann', 'publisher': "O'Reilly Media", 'year': 2017, 'edition': '1st', 'category': 'DB', 'copies': 5},
            {'isbn': '9781491903063', 'title': 'Learning SQL', 'author': 'Alan Beaulieu', 'publisher': "O'Reilly Media", 'year': 2020, 'edition': '3rd', 'category': 'DB', 'copies': 4},
            
            # Networking
            {'isbn': '9780133594140', 'title': 'Computer Networking: A Top-Down Approach', 'author': 'James Kurose, Keith Ross', 'publisher': 'Pearson', 'year': 2016, 'edition': '7th', 'category': 'NET', 'copies': 5},
            {'isbn': '9781587143670', 'title': 'CCNA Routing and Switching', 'author': 'Wendell Odom', 'publisher': 'Cisco Press', 'year': 2016, 'edition': '1st', 'category': 'NET', 'copies': 3},
            {'isbn': '9781449373320', 'title': 'TCP/IP Illustrated', 'author': 'W. Richard Stevens', 'publisher': 'Addison-Wesley', 'year': 1994, 'edition': '1st', 'category': 'NET', 'copies': 4},
            {'isbn': '9781118057537', 'title': 'Network Security Essentials', 'author': 'William Stallings', 'publisher': 'Pearson', 'year': 2017, 'edition': '6th', 'category': 'NET', 'copies': 3},
            
            # Cybersecurity
            {'isbn': '9781119085911', 'title': 'The Web Application Hackers Handbook', 'author': 'Dafydd Stuttard, Marcus Pinto', 'publisher': 'Wiley', 'year': 2011, 'edition': '2nd', 'category': 'SEC', 'copies': 4},
            {'isbn': '9781593278595', 'title': 'Penetration Testing', 'author': 'Georgia Weidman', 'publisher': 'No Starch Press', 'year': 2014, 'edition': '1st', 'category': 'SEC', 'copies': 3},
            {'isbn': '9781491918661', 'title': 'Cybersecurity Essentials', 'author': 'Charles J. Brooks', 'publisher': 'Wiley', 'year': 2018, 'edition': '1st', 'category': 'SEC', 'copies': 4},
            {'isbn': '9781119085928', 'title': 'Ethical Hacking and Penetration Testing', 'author': 'Rafay Baloch', 'publisher': 'CRC Press', 'year': 2017, 'edition': '2nd', 'category': 'SEC', 'copies': 3},
            {'isbn': '9781119085935', 'title': 'Applied Cryptography', 'author': 'Bruce Schneier', 'publisher': 'Wiley', 'year': 1996, 'edition': '2nd', 'category': 'SEC', 'copies': 2},
            
            # Mobile Development
            {'isbn': '9780134844534', 'title': 'Android Programming', 'author': 'Bill Phillips, Chris Stewart', 'publisher': 'Big Nerd Ranch', 'year': 2019, 'edition': '4th', 'category': 'MOB', 'copies': 4},
            {'isbn': '9780134682334', 'title': 'iOS Programming', 'author': 'Christian Keur, Aaron Hillegass', 'publisher': 'Big Nerd Ranch', 'year': 2018, 'edition': '6th', 'category': 'MOB', 'copies': 3},
            {'isbn': '9781491999837', 'title': 'React Native in Action', 'author': 'Nader Dabit', 'publisher': 'Manning', 'year': 2019, 'edition': '1st', 'category': 'MOB', 'copies': 4},
            {'isbn': '9781119287087', 'title': 'Flutter in Action', 'author': 'Eric Windmill', 'publisher': 'Manning', 'year': 2020, 'edition': '1st', 'category': 'MOB', 'copies': 3},
            
            # Mathematics
            {'isbn': '9780982477274', 'title': 'Discrete Mathematics and Its Applications', 'author': 'Kenneth Rosen', 'publisher': 'McGraw-Hill', 'year': 2018, 'edition': '8th', 'category': 'MATH', 'copies': 5},
            {'isbn': '9780470458365', 'title': 'Linear Algebra and Its Applications', 'author': 'David Lay, Steven Lay', 'publisher': 'Pearson', 'year': 2015, 'edition': '5th', 'category': 'MATH', 'copies': 4},
            {'isbn': '9780134689517', 'title': 'Calculus: Early Transcendentals', 'author': 'James Stewart', 'publisher': 'Cengage', 'year': 2015, 'edition': '8th', 'category': 'MATH', 'copies': 6},
            {'isbn': '9780321847997', 'title': 'Probability and Statistics', 'author': 'Morris DeGroot, Mark Schervish', 'publisher': 'Pearson', 'year': 2011, 'edition': '4th', 'category': 'MATH', 'copies': 4},
            {'isbn': '9781292223766', 'title': 'Introduction to Probability', 'author': 'Joseph Blitzstein, Jessica Hwang', 'publisher': 'CRC Press', 'year': 2019, 'edition': '2nd', 'category': 'MATH', 'copies': 3},
            
            # Information Technology
            {'isbn': '9780134683416', 'title': 'CompTIA A+ Certification', 'author': 'Mike Meyers', 'publisher': 'McGraw-Hill', 'year': 2019, 'edition': '9th', 'category': 'IT', 'copies': 4},
            {'isbn': '9780134618944', 'title': 'IT Project Management', 'author': 'Kathy Schwalbe', 'publisher': 'Cengage', 'year': 2018, 'edition': '9th', 'category': 'IT', 'copies': 3},
            {'isbn': '9781119515937', 'title': 'Cloud Computing', 'author': 'Thomas Erl, Ricardo Puttini', 'publisher': 'Prentice Hall', 'year': 2013, 'edition': '1st', 'category': 'IT', 'copies': 4},
            {'isbn': '9780135263983', 'title': 'DevOps Handbook', 'author': 'Gene Kim, Jez Humble', 'publisher': 'IT Revolution Press', 'year': 2016, 'edition': '1st', 'category': 'IT', 'copies': 3},
            {'isbn': '9781491988473', 'title': 'Kubernetes in Action', 'author': 'Marko Luksa', 'publisher': 'Manning', 'year': 2018, 'edition': '1st', 'category': 'IT', 'copies': 3},
            
            # Business & Management
            {'isbn': '9780735619678', 'title': 'The Lean Startup', 'author': 'Eric Ries', 'publisher': 'Crown Business', 'year': 2011, 'edition': '1st', 'category': 'BUS', 'copies': 5},
            {'isbn': '9780062301239', 'title': 'The Hard Thing About Hard Things', 'author': 'Ben Horowitz', 'publisher': 'Harper Business', 'year': 2014, 'edition': '1st', 'category': 'BUS', 'copies': 4},
            {'isbn': '9780307887894', 'title': 'Zero to One', 'author': 'Peter Thiel', 'publisher': 'Crown Business', 'year': 2014, 'edition': '1st', 'category': 'BUS', 'copies': 4},
            {'isbn': '9780062273208', 'title': 'The Innovators Dilemma', 'author': 'Clayton Christensen', 'publisher': 'Harvard Business Review Press', 'year': 2016, 'edition': '1st', 'category': 'BUS', 'copies': 3},
            {'isbn': '9780062315007', 'title': 'Good to Great', 'author': 'Jim Collins', 'publisher': 'Harper Business', 'year': 2001, 'edition': '1st', 'category': 'BUS', 'copies': 4},
            
            # Programming Languages
            {'isbn': '9781491919538', 'title': 'Learning Python', 'author': 'Mark Lutz', 'publisher': "O'Reilly Media", 'year': 2013, 'edition': '5th', 'category': 'CS', 'copies': 6},
            {'isbn': '9781491910740', 'title': 'Programming in C', 'author': 'Stephen Kochan', 'publisher': 'Addison-Wesley', 'year': 2014, 'edition': '4th', 'category': 'CS', 'copies': 4},
            {'isbn': '9780134190440', 'title': 'The C++ Programming Language', 'author': 'Bjarne Stroustrup', 'publisher': 'Addison-Wesley', 'year': 2013, 'edition': '4th', 'category': 'CS', 'copies': 3},
            {'isbn': '9781491956229', 'title': 'Learning Java', 'author': 'Patrick Niemeyer, Daniel Leuck', 'publisher': "O'Reilly Media", 'year': 2013, 'edition': '4th', 'category': 'CS', 'copies': 5},
            {'isbn': '9781449355739', 'title': 'JavaScript: The Good Parts', 'author': 'Douglas Crockford', 'publisher': "O'Reilly Media", 'year': 2008, 'edition': '1st', 'category': 'WEB', 'copies': 4},
            {'isbn': '9780135404676', 'title': 'PHP and MySQL Web Development', 'author': 'Luke Welling, Laura Thomson', 'publisher': 'Addison-Wesley', 'year': 2016, 'edition': '5th', 'category': 'WEB', 'copies': 3},
            
            # Additional Technical Books
            {'isbn': '9781617294020', 'title': 'Git Pocket Guide', 'author': 'Richard Silverman', 'publisher': "O'Reilly Media", 'year': 2013, 'edition': '1st', 'category': 'CS', 'copies': 5},
            {'isbn': '9781491954249', 'title': 'RESTful Web APIs', 'author': 'Leonard Richardson, Mike Amundsen', 'publisher': "O'Reilly Media", 'year': 2013, 'edition': '1st', 'category': 'WEB', 'copies': 3},
            {'isbn': '9780137141975', 'title': 'Continuous Delivery', 'author': 'Jez Humble, David Farley', 'publisher': 'Addison-Wesley', 'year': 2010, 'edition': '1st', 'category': 'SE', 'copies': 3},
            {'isbn': '9780321336774', 'title': 'Agile Software Development', 'author': 'Robert C. Martin', 'publisher': 'Prentice Hall', 'year': 2002, 'edition': '1st', 'category': 'SE', 'copies': 3},
            {'isbn': '9780321125217', 'title': 'Domain-Driven Design', 'author': 'Eric Evans', 'publisher': 'Addison-Wesley', 'year': 2003, 'edition': '1st', 'category': 'SE', 'copies': 3},
            {'isbn': '9780201616224', 'title': 'The Art of Computer Programming Vol 1', 'author': 'Donald Knuth', 'publisher': 'Addison-Wesley', 'year': 1997, 'edition': '3rd', 'category': 'CS', 'copies': 2},
            {'isbn': '9781449358068', 'title': 'Building Microservices', 'author': 'Sam Newman', 'publisher': "O'Reilly Media", 'year': 2015, 'edition': '1st', 'category': 'SE', 'copies': 4},
            {'isbn': '9781491950357', 'title': 'Site Reliability Engineering', 'author': 'Betsy Beyer, Chris Jones', 'publisher': "O'Reilly Media", 'year': 2016, 'edition': '1st', 'category': 'IT', 'copies': 3},
        ]
        
        category_map = {cat.code: cat for cat in categories}
        books = []
        
        for book_data in books_data:
            category = category_map.get(book_data['category'])
            if not category:
                continue
            
            total_copies = book_data['copies']
            available = random.randint(0, total_copies)  # Some books are borrowed
            
            book, created = Book.objects.get_or_create(
                isbn=book_data['isbn'],
                defaults={
                    'title': book_data['title'],
                    'author': book_data['author'],
                    'publisher': book_data['publisher'],
                    'publication_year': book_data['year'],
                    'edition': book_data['edition'],
                    'category': category,
                    'total_copies': total_copies,
                    'available_copies': available,
                    'status': 'available' if available > 0 else 'borrowed',
                    'shelf_location': f"Section {category.code}-{random.randint(1, 20)}",
                    'call_number': f"{category.code}.{random.randint(100, 999)}",
                    'acquisition_date': timezone.now().date() - timedelta(days=random.randint(30, 730)),
                    'price': Decimal(random.randint(1000, 8000))
                }
            )
            books.append(book)
        
        return books

    def create_borrowings(self, books):
        """Create book borrowings for existing students"""
        # Get current academic year and semester
        try:
            current_academic_year = AcademicYear.objects.filter(is_current=True).first()
            current_semester = Semester.objects.filter(is_current=True).first()
            
            if not current_academic_year or not current_semester:
                self.stdout.write(self.style.WARNING('No current academic year or semester found'))
                return []
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting academic year/semester: {e}'))
            return []
        
        # Get all active students
        students = list(Student.objects.filter(student_status='active'))
        if not students:
            self.stdout.write(self.style.WARNING('No active students found'))
            return []
        
        # Get librarian user
        librarian = User.objects.filter(role='librarian').first()
        if not librarian:
            self.stdout.write(self.style.WARNING('No librarian user found'))
            return []
        
        borrowings = []
        borrowing_statuses = ['active', 'returned', 'overdue']
        
        # Create 50-80 random borrowings
        num_borrowings = random.randint(50, 80)
        
        for _ in range(num_borrowings):
            student = random.choice(students)
            book = random.choice(books)
            status = random.choice(borrowing_statuses)
            
            # Random borrow date (within last 60 days)
            days_ago = random.randint(1, 60)
            borrow_date = timezone.now() - timedelta(days=days_ago)
            due_date = borrow_date.date() + timedelta(days=14)  # 2 weeks borrowing period
            
            # Determine return date and fine based on status
            return_date = None
            fine_amount = Decimal('0.00')
            fine_paid = False
            
            if status == 'returned':
                # Returned on time or early
                return_date = borrow_date + timedelta(days=random.randint(1, 14))
            elif status == 'overdue':
                # Calculate fine for overdue (5 KES per day)
                overdue_days = (timezone.now().date() - due_date).days
                if overdue_days > 0:
                    fine_amount = Decimal(overdue_days * 5)
                    fine_paid = random.choice([True, False])
            
            try:
                borrowing, created = BookBorrowing.objects.get_or_create(
                    student=student,
                    book=book,
                    borrow_date=borrow_date,
                    defaults={
                        'academic_year': current_academic_year,
                        'semester': current_semester,
                        'due_date': due_date,
                        'return_date': return_date,
                        'status': status,
                        'fine_amount': fine_amount,
                        'fine_paid': fine_paid,
                        'issued_by': librarian,
                        'returned_to': librarian if return_date else None,
                        'remarks': f'Borrowed from Muranga University of Technology Library'
                    }
                )
                if created:
                    borrowings.append(borrowing)
                    
                    # Update book availability
                    if status == 'active' or status == 'overdue':
                        book.available_copies = max(0, book.available_copies - 1)
                        if book.available_copies == 0:
                            book.status = 'borrowed'
                        book.save()
            
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not create borrowing: {e}'))
                continue
        
        return borrowings