from pykubegrader._initialize import username_to_seed
from pykubegrader.telemetry.responses import ensure_responses, log_variable, set_responses_json


def generate_user_seed(name, week, assignment_type, jhub_user):
    seed = username_to_seed(jhub_user) % 1000
    set_responses_json(key="seed", value=seed)
    set_responses_json(key="week", value=week)
    set_responses_json(key="assignment_type", value=assignment_type)

    set_responses_json(key="assignment", value=name)
    set_responses_json(key="jhub_user", value=jhub_user)

        # TODO: Check whether this is called correctly
    log_variable("Student Info", jhub_user, seed)

    responses = ensure_responses()

    if not isinstance(responses.get("seed"), int):
        raise ValueError("Seed not set or is not an integer")
    return responses