import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to supabase storage
url: str = os.environ.get("SUPABASE_URL")

# Set supabase client
key: str = os.environ.get("SUPABASE_API_SECRET_KEY")
supa_client: Client = create_client(url, key)

# Connect to supabase DB using sqlalchemy
uri_db: str = os.environ.get("SUPABASE_DB_URI")


