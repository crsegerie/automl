"""
The following elements are memoïzed:

- long function calls:
    - kili_project_memoizer: get_asset_memoized
    - kili_memoizer: download_image
- models:
    - get_last_trained_model_path
- predictions: saved into


"""
import os
import shutil
from typing import List, Optional
from typing_extensions import get_args
from joblib import Memory

from kiliautoml.utils.constants import HOME, ModelRepositoryT
from kiliautoml.utils.path import Path


def kili_project_memoizer(
    sub_dir: str,
):
    """Decorator factory for memoizing a function that takes a project_id as input."""

    def decorator(some_function):
        def wrapper(*args, **kwargs):
            project_id = kwargs.get("project_id")
            if not project_id:
                raise ValueError("project_id not specified in a keyword argument")
            cache_path = Path.cache(project_id, sub_dir)
            memory = Memory(cache_path, verbose=0)
            return memory.cache(some_function)(*args, **kwargs)

        return wrapper

    return decorator


def kili_memoizer(some_function):
    def wrapper(*args, **kwargs):
        memory = Memory(HOME, verbose=0)
        return memory.cache(some_function)(*args, **kwargs)

    return wrapper


def clear_automl_cache(
    project_id: str, command: str, model_repository: Optional[ModelRepositoryT], job_name=None
):
    """If model_repository is None, then it clears for every modelRepository cache."""
    if command == "train":
        sub_dirs = ["get_asset_memoized"]
    elif command == "prioritize":
        sub_dirs = ["get_asset_memoized"]
    else:
        raise ValueError(f"command {command} not recognized")

    cache_paths = [Path.cache(project_id, sub_dir) for sub_dir in sub_dirs]

    if model_repository is None:
        model_repositories: List[ModelRepositoryT] = get_args(ModelRepositoryT)  # type: ignore
    else:
        model_repositories = [model_repository]

    for model_repository in model_repositories:
        if command == "train":
            assert job_name is not None
            assert model_repository is not None
            path = Path.model_repository(
                root_dir=HOME,
                project_id=project_id,
                job_name=job_name,
                model_repository=model_repository,
            )
            cache_paths.append(Path.append_hf_model_folder(path, "pytorch"))

        for cache_path in cache_paths:
            if os.path.exists(cache_path):
                shutil.rmtree(cache_path)
