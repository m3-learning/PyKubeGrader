def print_api_response(response, **kwargs):

    verbose = kwargs.get("verbose", False)

    if verbose:
        print(f"status code: {response.status_code}")
        data = response.json()
        for k, v in data.items():
            print(f"{k}: {v}")