from pymongo import MongoClient

class MongoProdigyDBManager:

    def __init__(self, output_collection, host='localhost', port=27017):
        self.client = MongoClient(host, port)
        self.db_name = "prodigy"
        self.db = getattr(self.client, self.db_name)
        self.output_collection = getattr(self.db, output_collection)

    def get_dataset(self, name):
        return list(self.output_collection.find({"datasets": name}))
    
    def __len__(self):
        return len(self.datasets)

    def __contains__(self, name):
        return self.db.datasets.find_one({"name": name}) is not None

    def get_meta(self, name):
        pass

    def get_examples(self, ids, by="_task_hash"):
        return list(self.output_collection.find({by: {"$in": ids}}))

    def get_input_hashes(self, *names):
        examples = self.output_collection.find({"datasets": {"$in": names}})
        return {ex['_input_hash'] for ex in examples}

    def get_task_hashes(self, *names):
        examples = self.output_collection.find({"datasets": {"$in": names}})
        return {ex['_task_hash'] for ex in examples}

    def count_dataset(self, name, session=False):
        return self.output_collection.count_documents({"datasets": name})

    def add_dataset(self, name, meta=None, session=False):
        if self.db.datasets.find_one({"name": name}) is not None:
            # already exists
            return self.get_dataset(name)
        meta = meta or {}
        dataset = {
            "name": name,
            "meta": meta,
            "session": session
        }
        self.db.datasets.insert_one(dataset)
        return []

    def add_examples(self, examples, datasets):
        if len(examples) == 0:
            return
        for example in examples:
            example['datasets'] = datasets
        self.output_collection.insert_many(examples)

    def link(self, name, example_ids):
        for _id in example_ids:
            example = self.output_collection.find_one({"_id": _id})
            example['datasets'] = example.get('datasets', [])
            example['datasets'] += [name]
            self.output_collection.update_one({"_id": _id}, example)

    def unlink(self, example_ids):
        for _id in example_ids:
            example = self.output_collection.find_one({"_id": _id})
            example['datasets'] = []
            self.output_collection.update_one({"_id": _id}, example)

    def drop_dataset(self, name, batch_size):
        self.db.datasets.delete_one({"name": name})
        for example in self.output_collection.find({"datasets": name}):
            example['datasets'] = list(filter(lambda x: x != name, example['datasets']))
            self.output_collection.update_one({"_id": example['_id']}, example)
        return True

    def get_datasets(self):
        return [dataset['name'] for dataset in self.db.datasets.find({"session": False})]

    def get_sessions(self):
        return [dataset['name'] for dataset in self.db.datasets.find({"session": True})]

    datasets = property(get_datasets)
    sessions = property(get_sessions)

db_manager = MongoProdigyDBManager('silver_output_binary')