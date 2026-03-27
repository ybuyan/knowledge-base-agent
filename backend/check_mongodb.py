from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['agent']

print('Collections:', db.list_collection_names())

docs = list(db.document_status.find())
print(f'Documents count: {len(docs)}')

for d in docs:
    print(f"  - {d.get('filename', 'N/A')} (status: {d.get('status', 'N/A')})")

client.close()
