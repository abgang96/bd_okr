import os
import sys
import subprocess

def run_command(command):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, text=True)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        return False
    return True

def main():
    # Step 1: Apply the teamsauth migration with --fake-initial flag
    if not run_command("python manage.py migrate teamsauth 0001 --fake-initial"):
        return
    
    # Step 2: Apply all remaining migrations
    if not run_command("python manage.py migrate"):
        return
    
    print("\nMigrations completed successfully!")
    print("\nNOTE: Since you've added a custom user model to an existing project,")
    print("you might need to manually fix any user-related data inconsistencies.")
    print("Consider creating a superuser with:")
    print("python manage.py createsuperuser")

if __name__ == "__main__":
    # Make sure we're in the Django project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()