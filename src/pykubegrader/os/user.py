import os


def get_jhub_user():
    jhub_user = os.getenv("JUPYTERHUB_USER")
    if jhub_user is None:
        raise Exception("Setup unsuccessful. Are you on JupyterHub?")
    return jhub_user
