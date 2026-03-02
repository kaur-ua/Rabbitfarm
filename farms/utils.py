def get_user_farm(user):
    if user.is_authenticated:
        return user.farms.first()
    return None