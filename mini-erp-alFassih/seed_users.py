# mini-erp-alFassih/seed_users.py
from mini_erp_alFassih import app, db
from mini_erp_alFassih.models import User, Therapist # Corrected: models are in mini_erp_alFassih.models

def create_initial_users():
    with app.app_context(): # Ensure we are within application context
        # Create Admin User
        admin_email = 'admin@example.com'
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                first_name='Admin',
                last_name='User',
                role='admin',
                is_active=True
            )
            admin_user.set_password('adminpass') # Change in a real environment!
            db.session.add(admin_user)
            print(f"Admin user {admin_email} created.")
        else:
            print(f"Admin user {admin_email} already exists.")

        # Create Therapist User and link to a Therapist profile
        therapist_email = 'therapist@example.com'
        therapist_user = User.query.filter_by(email=therapist_email).first()
        if not therapist_user:
            therapist_user = User(
                email=therapist_email,
                first_name='Thera',
                last_name='Pist',
                role='therapist',
                is_active=True
            )
            therapist_user.set_password('therapistpass') # Change in a real environment!
            db.session.add(therapist_user)
            # Must commit here to get therapist_user.id if it's a new user
            # or if we need to query it reliably before linking profile.
            # However, if therapist_profile logic depends on user_id existing,
            # we might need to flush or commit earlier.
            # For simplicity, let's commit the user first if new.
            db.session.commit() # Commit user to ensure it has an ID if new.

            # Try to find an unlinked therapist profile or create a new one
            # This logic assumes a Therapist profile might exist independently first.
            # If a Therapist profile is ALWAYS created WITH a user, this is different.
            # The current Therapist model allows user_id to be nullable.

            # Check if this user already has a linked therapist profile via backref
            if therapist_user.therapist_profile:
                therapist_profile = therapist_user.therapist_profile
                print(f"Therapist user {therapist_email} already linked to profile ID {therapist_profile.id}.")
            else:
                # Option 1: Find an existing unlinked therapist profile (e.g. by name match or if user_id is None)
                # This example tries to find any profile without a user_id.
                therapist_profile = Therapist.query.filter_by(user_id=None).first()

                if not therapist_profile:
                    # Option 2: Or, create a new Therapist profile if no suitable unlinked one is found
                    print(f"No existing unlinked therapist profile found for {therapist_email}. Creating a new one.")
                    therapist_profile = Therapist(
                        first_name=therapist_user.first_name if therapist_user.first_name else 'Thera',
                        last_name=therapist_user.last_name if therapist_user.last_name else 'Pist',
                        specialization='General Therapy'
                        # user_id will be set below
                    )
                    db.session.add(therapist_profile)
                    # Need to commit therapist_profile if it's new and we want its ID printed,
                    # or ensure user_id is set before the final commit.

                therapist_profile.user_id = therapist_user.id
                # If User model is the source of truth for names, update Therapist profile:
                # if therapist_user.first_name: therapist_profile.first_name = therapist_user.first_name
                # if therapist_user.last_name: therapist_profile.last_name = therapist_user.last_name

                # Commit changes to therapist_profile (new or updated user_id)
                db.session.commit()
                print(f"Therapist user {therapist_email} created/found and linked to profile ID {therapist_profile.id}.")
        else:
            print(f"Therapist user {therapist_email} already exists.")

        # One final commit for any pending changes (e.g. admin user if not committed yet)
        db.session.commit()

if __name__ == '__main__':
    create_initial_users()
    print("User seeding process complete.")
