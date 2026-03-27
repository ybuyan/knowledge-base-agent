from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["agent"]

# Delete all sessions
sessions_result = db.sessions.delete_many({})
print(f"Deleted {sessions_result.deleted_count} sessions")

# Delete all messages
messages_result = db.messages.delete_many({})
print(f"Deleted {messages_result.deleted_count} messages")

# Delete all document status
docs_result = db.document_status.delete_many({})
print(f"Deleted {docs_result.deleted_count} document statuses")

print("\nAll data cleared successfully!")
