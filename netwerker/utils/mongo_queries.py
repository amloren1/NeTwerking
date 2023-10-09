from werkzeug.exceptions import BadRequest, Forbidden

from netwerker.app import mongo


def get_user(
    _id=None,
    uuid: str = None,
    email: str = None,
    none_on_fail: bool = False,
    get_friends: bool = False,
):
    """
    Get user by uuid or email.

    Parameters
    ----------
    uuid : str
        User UUID
    email : str
        User email
    none_on_fail: bool
        Return None if no user is found when set to True

    Returns
    -------
    user : dict
        Dictionary containing user details, or None if no user was found
    """
    # Build the match query based on the provided parameters
    match_query = {}
    if uuid is not None:
        match_query["uuid"] = uuid
    if email is not None:
        match_query["email"] = email
    if _id is not None:
        match_query["_id"] = _id

    proj = {"friends": 0} if not get_friends else {}
    try:
        user = mongo.db.users.find_one(match_query, projection=proj)
    except Exception as e:
        if none_on_fail:
            return None
        else:
            raise Forbidden(f"An error occurred: {str(e)}")

    if user is None and not none_on_fail:
        raise Forbidden("Invalid User")

    return user
