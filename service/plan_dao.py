import requests

from dao_helper import get_all_objects, get_object


def get_plans(group_generator_func, since=None):
    for group in group_generator_func:
        for plan in get_plans_for_group(group['id']):
            plan['details'] = get_plan_details(plan['id'])
            yield (plan)


def get_plans_for_group(group_id):
    try:
        yield from get_all_objects(f'/groups/{group_id}/planner/plans')
    except requests.exceptions.HTTPError:
        # already logged in make_request function, no action needed
        pass


def get_plan_details(plan_id):
    return get_object(f'/planner/plans/{plan_id}/details')
