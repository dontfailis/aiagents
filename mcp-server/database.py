import os
import json
from dotenv import load_dotenv

load_dotenv()

class MockDocument:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None
    
    def to_dict(self):
        return self._data

class MockCollection:
    def __init__(self, name, db_path):
        self.name = name
        self.db_path = db_path
        
    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_db(self, db_data):
        with open(self.db_path, 'w') as f:
            json.dump(db_data, f)

    def document(self, doc_id):
        return MockDocumentReference(doc_id, self)

class MockDocumentReference:
    def __init__(self, doc_id, collection):
        self.id = doc_id
        self.collection = collection

    def set(self, data):
        db_data = self.collection._load_db()
        if self.collection.name not in db_data:
            db_data[self.collection.name] = {}
        
        # Handle SERVER_TIMESTAMP
        serializable_data = {}
        for k, v in data.items():
            if hasattr(v, '__module__') and 'google.cloud.firestore' in v.__module__:
                serializable_data[k] = "2026-03-16T21:00:00Z"
            else:
                serializable_data[k] = v
                
        db_data[self.collection.name][self.id] = serializable_data
        self.collection._save_db(db_data)

    def update(self, data):
        db_data = self.collection._load_db()
        if self.collection.name in db_data and self.id in db_data[self.collection.name]:
            current_data = db_data[self.collection.name][self.id]
            for k, v in data.items():
                if hasattr(v, '__module__') and 'google.cloud.firestore' in v.__module__:
                    current_data[k] = "2026-03-16T21:00:00Z"
                else:
                    current_data[k] = v
            db_data[self.collection.name][self.id] = current_data
            self.collection._save_db(db_data)

    def get(self):
        db_data = self.collection._load_db()
        data = db_data.get(self.collection.name, {}).get(self.id)
        return MockDocument(data)

class MockFirestore:
    def __init__(self, db_path="test_db.json"):
        self.db_path = db_path
        self.SERVER_TIMESTAMP = "SENTINEL_TIMESTAMP"

    def collection(self, name):
        return MockCollection(name, self.db_path)

# Use real firestore if available and configured, else mock
USE_MOCK = os.getenv("USE_MOCK_DB", "true").lower() == "true"

if USE_MOCK:
    db = MockFirestore()
    from unittest.mock import MagicMock
    firestore = MagicMock()
    firestore.SERVER_TIMESTAMP = "SENTINEL_TIMESTAMP"
else:
    from google.cloud import firestore
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    db = firestore.Client(project=project_id)
