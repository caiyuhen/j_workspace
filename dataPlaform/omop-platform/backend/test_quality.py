import pymongo
import json

MONGO_URI = 'mongodb://jdjd:JdJdllmix2308@192.168.0.214:27017/'
client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
db = client['omop_cdm_standardized']
col = db['cleaned_data']

total_patients = col.count_documents({})
print('Total Patients:', total_patients)

pipeline = [
    {
        '$project': {
            'conditions': {'$ifNull': ['$conditions', []]},
            'measurements': {'$ifNull': ['$measurements', []]},
            'drug_exposures': {'$ifNull': ['$drug_exposures', []]},
            'observations': {'$ifNull': ['$observations', []]}
        }
    },
    {
        '$project': {
            'conditions_count': {'$size': '$conditions'},
            'measurements_count': {'$size': '$measurements'},
            'drugs_count': {'$size': '$drug_exposures'},
            'observations_count': {'$size': '$observations'},
            'std_conditions': {
                '$size': {
                    '$filter': {
                        'input': '$conditions',
                        'as': 'item',
                        'cond': {'$eq': ['$$item.is_standardized', True]}
                    }
                }
            },
            'std_measurements': {
                '$size': {
                    '$filter': {
                        'input': '$measurements',
                        'as': 'item',
                        'cond': {'$eq': ['$$item.is_standardized', True]}
                    }
                }
            },
            'std_drugs': {
                '$size': {
                    '$filter': {
                        'input': '$drug_exposures',
                        'as': 'item',
                        'cond': {'$eq': ['$$item.is_standardized', True]}
                    }
                }
            }
        }
    },
    {
        '$group': {
            '_id': None,
            'total_conditions': {'$sum': '$conditions_count'},
            'total_measurements': {'$sum': '$measurements_count'},
            'total_drugs': {'$sum': '$drugs_count'},
            'total_observations': {'$sum': '$observations_count'},
            'standardized_conditions': {'$sum': '$std_conditions'},
            'standardized_measurements': {'$sum': '$std_measurements'},
            'standardized_drugs': {'$sum': '$std_drugs'}
        }
    }
]

res = list(col.aggregate(pipeline))
print(json.dumps(res, indent=2))
