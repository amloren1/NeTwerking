from collections import deque
from bson import ObjectId

import xxhash

from netwerker.app import mongo
from netwerker.utils.mongo_queries import get_user

def generate_friendship_hash(_id_1: str, _id_2: str):
    # Sort the UUIDs to ensure the hash is the same regardless of the order
    sorted_ids = sorted([_id_1, _id_2])
    concatenated_ids = "".join(sorted_ids)

    # Generate a fast, non-cryptographic hash optimized for hash table storage
    return str(xxhash.xxh64_intdigest(concatenated_ids))

def bfs_friendship_distance(start_user_id: str, target_user_id: str):

    # Initialize the BFS queue and set
    queue = deque([(start_user_id, 0)])  # Each entry is (user_id (BSON ObjectId), distance)
    visited = set()
    while queue:
        current_user_id, current_distance = queue.popleft()

        # Skip if this user is already visited
        if current_user_id in visited:
            continue

        visited.add(current_user_id)  # Mark the user as visited

        # Generate the hash for the current user and target user
        friendship_hash = generate_friendship_hash(current_user_id, target_user_id)

        # Check if the current user and target user are direct friends
        if mongo.db.friends.find_one({"friendship_hash": friendship_hash}):
            return current_distance + 1

        # Fetch the current user's friends from MongoDB
        current_user = get_user(_id=ObjectId(current_user_id), get_friends=True)
        if not current_user or "friends" not in current_user:
            continue

        friends = current_user["friends"]

        for friend_id in friends:
            if friend_id not in visited:
                queue.append((str(friend_id), current_distance + 1))

    return None  # No path found

