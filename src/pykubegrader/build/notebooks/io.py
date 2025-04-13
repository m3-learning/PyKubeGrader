import nbformat


def write_notebook(notebook, save_path):
    with open(save_path, "w") as nb_file:
        nbformat.write(notebook, nb_file)


def read_notebook(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)
    return notebook