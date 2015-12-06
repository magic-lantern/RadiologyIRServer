from pymongo import MongoClient
from datetime import datetime
import pymongo
from bson.objectid import ObjectId

client = MongoClient("mongodb://localhost:27017")
# connect to resturants database
db = client['querysession']

## this example works to find those with 15 total results
#cursor = db.querysession.find({"result_count": 15})

## this example finds those query sessions that had AJR as a source
#cursor = db.querysession.find({'results' : {'$elemMatch': {
#    'source': 'AJR'
#}}})
cursor = db.querysession.find({'results' : {'$elemMatch': {
    'articleLink': 'http://www.mypacs.net/cases/40101.html',
}}})
print("Query Sessions matched: ", cursor.count())
for document in cursor:
    print('Query session occurred at: ', document['datetime'])
    print('Query Parameters used: ', document['query_params'])
    for result in document['results']:
        if result['articleLink'] == 'http://www.ajronline.org/cgi/content/full/192/3/W117':
            print('    Result Position: ', result['resultID'])
            print('    Result Title: ', result['resultTitle'])
            if('followedCount' in result):
                print('    Times lnk followed: ', result['followedCount'])
            else:
                print('    Times lnk followed: 0')

# find by mongodb ID
cursor = db.querysession.find({"_id": ObjectId('5663dfb6da042e529ab0cc66')})
for document in cursor:
    print(document)


cursor = db.querysession.find()
print("total number of documents in store : ", cursor.count())
for document in cursor:
    print(document)

#create a new restaurant
# result = db.restaurants.insert_one(
#     {
#         "address": {
#             "street": "2 Avenue",
#             "zipcode": "10075",
#             "building": "1480",
#             "coord": [-73.9557413, 40.7720266]
#         },
#         "borough": "Manhattan",
#         "cuisine": "French",
#         "grades": [
#             {
#                 "date": datetime.strptime("2014-10-01", "%Y-%m-%d"),
#                 "grade": "F",
#                 "score": 0
#             },
#             {
#                 "date": datetime.strptime("2014-01-16", "%Y-%m-%d"),
#                 "grade": "D",
#                 "score": 11
#             }
#         ],
#         "name": "La Diva",
#         "restaurant_id": "41704620"
#     }
# )

cursor = db.restaurants.find({"cuisine": "American (New)"})
print("Restaurants with American (New)")
for document in cursor:
    print(document["name"] + " " + document["cuisine"])

print("Show grade A restaurants.")
cursor = db.restaurants.find({"grades.grade": "A"})
for document in cursor:
    print(document["name"])

print("    Demo of AND")
#Logical AND
cursor = db.restaurants.find({"cuisine": "Italian", "address.zipcode": "10075"})
for document in cursor:
    print(document["name"])

print("    Demo of OR")
#Logical OR
cursor = db.restaurants.find({"$or": [{"cuisine": "Italian"}, {"address.zipcode": "10075"}]})
for document in cursor:
    print(document["name"])

print("    Demo of sort")
#Sort Results
cursor = db.restaurants.find().sort([
    ("borough", pymongo.ASCENDING),
    ("address.zipcode", pymongo.DESCENDING)
])
for document in cursor:
    print(document["name"] + document["cuisine"])

result = db.restaurants.update_one(
    {"name": "Le Dive 2"},
    {
        "$set": {
            "cuisine": "American (New)"
        },
        "$currentDate": {"lastModified": True}
    }
)
print("results matched", result.matched_count)
print("results modified", result.modified_count)

result = db.restaurants.update_one(
    {"name": "The Hole"},
    {
        "$set": {
            "cuisine": "Grease"
        },
        "$currentDate": {"lastModified": True}
    }
)
print("results matched", result.matched_count)
print("results modified", result.modified_count)
