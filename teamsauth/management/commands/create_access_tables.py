from django.core.management.base import BaseCommand
from django.db import connections, connection

class Command(BaseCommand):
    help = 'Creates migration for new access models'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating migrations for access models...'))

        cursor = connection.cursor()
        
        # Check if the table exists
        cursor.execute("""
            SELECT COUNT(name) FROM sqlite_master 
            WHERE type='table' AND name='teamsauth_useraccessmapping';
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            self.stdout.write(self.style.SUCCESS('Creating UserAccessMapping table...'))
            
            # Create the table for UserAccessMapping
            cursor.execute("""
            CREATE TABLE teamsauth_useraccessmapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                access_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES teamsauth_teamsprofile (id) ON DELETE CASCADE,
                UNIQUE(user_id, access_id)
            );
            """)
            
            self.stdout.write(self.style.SUCCESS('UserAccessMapping table created successfully'))
        else:
            self.stdout.write(self.style.SUCCESS('UserAccessMapping table already exists'))
            
        # Verify tables are created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        self.stdout.write(self.style.SUCCESS(f'Tables in database: {", ".join([t[0] for t in tables])}'))
        
        self.stdout.write(self.style.SUCCESS('Migration complete!'))
