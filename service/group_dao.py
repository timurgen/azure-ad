from dao_helper import get_all_objects

RESOURCE_PATH = '/groups/'


def get_all_groups(delta=None):
    """
    Fetch and stream back users from Azure AD via MS Graph API
    :param delta: delta token from last request
    :return: generated JSON output with all fetched users
    """
    yield from get_all_objects(f'{RESOURCE_PATH}delta', delta)
