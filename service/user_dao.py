import logging
from dao_helper import get_all_objects, make_request, GRAPH_URL

RESOURCE_PATH = '/users/'


def create_user_from_array(user_data_array):
    """
    Function to synchronize user array from Sesam into Azure Active Directory
    This function will try to create user first and update it if create operation failed
    This function will also disable users with _deleted property = true
    :param user_data_array: array of user objects
    :return: nothing if everything is OK
    """

    def __try_create(user_data):
        """
        Internal function to create user
        :param user_data: json object with user details
        :return: void
        """
        logging.info(f'trying to create user {user_data.get("userPrincipalName")}')
        make_request(f'{GRAPH_URL}{RESOURCE_PATH}', 'POST', user_data)
        logging.info(f'user {user_data.get("userPrincipalName")} created successfully')

    def __try_update(user_data):
        """
        Internal function to update user
        Update user with passwordProfile is not possible without Directory.AccessAsUser.All
        which is not exist in "application" permission so we need to remove this part if exist
        :param user_data: json object with user details, must contain user identifier
        (id or userPrincipalName property)
        :return: void
        """
        user_id = user_data['id'] if user_data.get('id') else user_data['userPrincipalName']

        if not user_id:
            raise Exception("Couldn't find id for user, at least id or userPrincipalName needed")

        if user_data.get('passwordProfile'):
            del user_data['passwordProfile']

        logging.info(f'trying to update user {user_data.get("userPrincipalName")}')
        make_request(f'{GRAPH_URL}{RESOURCE_PATH}{user_id}', 'PATCH', user_data)
        logging.info(f'user {user_data.get("userPrincipalName")} updated successfully')

    def __try_delete(user_data):
        """
        Internal function to 'delete' user (We will not actually perform delete operation but only
        disable user account by setting accountEnabled = false
        :param user_data: json object with user details, must contain user identifier
        (id or userPrincipalName property)
        :return: void
        """
        user_id = user_data['id'] if user_data.get('id') else user_data['userPrincipalName']
        if not user_id:
            raise Exception("Couldn't find id for user, at least id or userPrincipalName needed")

        logging.info(f'trying to disable user {user_data.get("userPrincipalName")}')
        make_request(f'{GRAPH_URL}{RESOURCE_PATH}{user_id}', 'PATCH', {'accountEnabled': False})
        logging.info(f'user {user_data.get("userPrincipalName")} disabled successfully')

    for user in user_data_array:
        if '_deleted' in user and user['_deleted']:
            __try_delete(user)
            continue
        try:
            __try_create(user)
        except Exception as e:
            # TODO try to update only if error is about "Another object ... already exists."
            logging.warning(e)
            __try_update(user)


def get_all_users(delta=None):
    """
    Fetch and stream back users from Azure AD via MS Graph API
    :param delta: delta token from last request
    :return: generated JSON output with all fetched users
    """
    yield from get_all_objects(f'{RESOURCE_PATH}delta', delta)
