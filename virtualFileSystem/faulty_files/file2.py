def add_user(username, current_list=None):
    if current_list is None:
        current_list = [] 
    current_list.append(username)
    return current_list

def get_user_profile(user_dict, key):
    return user_dict[key]