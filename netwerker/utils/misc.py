from collections import deque
from bson import ObjectId

import xxhash

from netwerker.app import mongo

def generate_friendship_hash(_id_1: str, _id_2: str):
    # Sort the UUIDs to ensure the hash is the same regardless of the order
    sorted_uuids = sorted([_id_1, _id_2])
    concatenated_uuids = "".join(sorted_uuids)

    # Generate a fast, non-cryptographic hash optimized for hash table storage
    return str(xxhash.xxh64_intdigest(concatenated_uuids))



def bfs_friendship_distance(start_user_id: ObjectId, target_user_id: ObjectId):
   

    # Initialize the BFS queue and set
    queue = deque([(start_user_id, 0)])  # Each entry is (user_id (BSON Object_id), distance)
    visited = set()

    while queue:
        current_user_id, current_distance = queue.popleft()

        friendship_hash = generate_friendship_hash(start_user_id, target_user_id)

        # Check if the current user and target user are direct friends
        if mongo.db.friends.find_one({"friendship_hash": friendship_hash}):
            return current_distance + 1
        else:
            visited.add(current_user_id) # user has been visited
            

        # Fetch the current user's friends from MongoDB
        current_user = mongo.db.users.find_one({"_id": current_user_id})
        if not current_user or "friends" not in current_user:
            continue

        friends = current_user["friends"]

        for friend_id in friends:
            if friend_id not in visited:
                queue.append((friend_id, current_distance + 1))

    return None  # No path found

