import os
from pathlib import Path


def gather_local_files(input_config_build_sets):

    config_build_sets = {**input_config_build_sets}

    # Gather local repos files
    for config_path_key, paths in config_build_sets.items():

        for candidate_file in _relative_path_potential_siblings(config_path_key):
            if os.path.exists(candidate_file):
                paths.append(candidate_file)

    return config_build_sets


def _relative_path_potential_siblings(path):

    filename = os.path.basename(path)

    directory = os.path.dirname(path)

    return [
        str(Path(directory) / Path("merge." + filename)),
        str(Path(directory) / Path(filename + ".merge")),
    ]
