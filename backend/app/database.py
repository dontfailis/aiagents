import os
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
db = firestore.Client(project=project_id)

