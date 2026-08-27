import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def main():
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        return

    print("Connecting to Supabase Admin Client...")
    supabase = create_client(supabase_url, service_role_key)

    email = "user@example.com"
    password = "Password123!"

    try:
        print(f"Creating confirmed test user '{email}'...")
        response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        print("User created successfully!")
        print(f"Credentials:\n- Email: {email}\n- Password: {password}")
    except Exception as e:
        print(f"Failed to create user. It may already exist. Details: {str(e)}")

if __name__ == "__main__":
    main()
