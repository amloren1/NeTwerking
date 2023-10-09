/*
    Two collections for user and friend relationships:

    user collection:
    {
        "_id": ObjectId,          
        "user_uuid": String,      // unique identifier, maybe wont use
        "name": String,
        "email": String,
        "friends": [              // Array of ObjectIDs referring to friends
            ObjectId, 
            ...
        ]
    }

    friends collection:

    {
        "_id": ObjectId,           
        "friendship_hash": String, // Unique hash based on sorted ObjectIDs
        "user1_id": ObjectId,      // ObjectID of the first user
        "user2_id": ObjectId,      // ObjectID of the second user
        "created_at": DateTime     // Timestamp
    }


*/


db.createUser(
    {
        user: "dev",
        pwd: "password",
        roles: [
            {
                role: "readWrite",
                db: "netwerker"
            }
        ]
    }
);

// Sample data for 10 users with custom UUIDs
const users = Array.from({ length: 10 }, (_, i) => {
    const baseUuid = `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx`;  // Replace this with a real UUID generator
    const customUuid = `${baseUuid}${String(i + 1).padStart(2, '0')}`;
    
    return {
      uuid: customUuid,
      name: `User${i + 1}`,
      email: `user${i + 1}@example.com`,
      passwordHash: "pbkdf2:sha256:260000$DZKVC5QFnHA4lmxy$9a653846d4522b7d0d1c9bc21c2f397ca41030598eaecbfcb169982b047ac4b3",
      friends: [],
      email_verified: true,
    };
  });
  
db.users.insertMany(users);


