import os
import json

import click
from kili.client import Kili
from tabulate import tabulate

from utils.constants import (
    ContentInput,
    HOME,
    InputType,
    MLTask,
    ModelFramework,
    ModelName,
    ModelRepository,
    Tool,
)
from utils.helpers import (
    get_assets,
    get_project,
    kili_print,
    set_default,
    build_model_repository_path,
    parse_label_types,
)

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["WANDB_DISABLED"] = "true"


def train_image_bounding_box(
    api_key,
    job,
    job_name,
    max_assets,
    args_dict,
    model_framework,
    model_name,
    model_repository,
    project_id,
    label_types,
    clear_dataset_cache,
):
    from utils.ultralytics.train import ultralytics_train_yolov5

    model_repository = set_default(
        model_repository,
        ModelRepository.Ultralytics,
        "model_repository",
        [ModelRepository.Ultralytics],
    )
    path = build_model_repository_path(HOME, project_id, job_name, model_repository)
    if model_repository == ModelRepository.Ultralytics:
        model_framework = set_default(
            model_framework,
            ModelFramework.PyTorch,
            "model_framework",
            [ModelFramework.PyTorch],
        )
        model_name = set_default(
            model_name, ModelName.YoloV5, "model_name", [ModelName.YoloV5]
        )
        return ultralytics_train_yolov5(
            api_key,
            path,
            job,
            max_assets,
            args_dict,
            project_id,
            model_framework,
            label_types,
            clear_dataset_cache,
        )


def train_ner(
    api_key,
    assets,
    job,
    job_name,
    model_framework,
    model_name,
    model_repository,
    project_id,
    clear_dataset_cache,
):
    from utils.huggingface.train import huggingface_train_ner
    import nltk

    nltk.download("punkt")
    model_repository = set_default(
        model_repository,
        ModelRepository.HuggingFace,
        "model_repository",
        [ModelRepository.HuggingFace],
    )
    path = build_model_repository_path(HOME, project_id, job_name, model_repository)
    if model_repository == ModelRepository.HuggingFace:
        model_framework = set_default(
            model_framework,
            ModelFramework.PyTorch,
            "model_framework",
            [ModelFramework.PyTorch, ModelFramework.Tensorflow],
        )
        model_name = set_default(
            model_name,
            ModelName.BertBaseMultilingualCased,
            "model_name",
            [
                ModelName.BertBaseMultilingualCased,
                ModelName.DistilbertBaseCased,
            ],
        )
        return huggingface_train_ner(
            api_key,
            assets,
            job,
            job_name,
            model_framework,
            model_name,
            path,
            clear_dataset_cache,
        )
    else:
        return None


def train_text_classification_single(
    api_key,
    assets,
    job,
    job_name,
    model_framework,
    model_name,
    model_repository,
    project_id,
    clear_dataset_cache,
) -> float:
    """ """
    import nltk

    nltk.download("punkt")
    from utils.huggingface.train import huggingface_train_text_classification_single

    model_repository = set_default(
        model_repository,
        ModelRepository.HuggingFace,
        "model_repository",
        [ModelRepository.HuggingFace],
    )
    path = build_model_repository_path(HOME, project_id, job_name, model_repository)
    if model_repository == ModelRepository.HuggingFace:
        model_framework = set_default(
            model_framework,
            ModelFramework.PyTorch,
            "model_framework",
            [ModelFramework.PyTorch, ModelFramework.Tensorflow],
        )
        model_name = set_default(
            model_name,
            ModelName.BertBaseMultilingualCased,
            "model_name",
            [ModelName.BertBaseMultilingualCased],
        )
        return huggingface_train_text_classification_single(
            api_key,
            assets,
            job,
            job_name,
            model_framework,
            model_name,
            path,
            clear_dataset_cache,
        )


@click.command()
@click.option("--api-key", default=os.environ.get("KILI_API_KEY"), help="Kili API Key")
@click.option(
    "--model-framework", default=None, help="Model framework (eg. pytorch, tensorflow)"
)
@click.option("--model-name", default=None, help="Model name (eg. bert-base-cased)")
@click.option(
    "--model-repository", default=None, help="Model repository (eg. huggingface)"
)
@click.option("--project-id", default=None, help="Kili project ID")
@click.option(
    "--label-types",
    default=None,
    help="Comma separated list Kili specific label types to select (among DEFAULT, REVIEW, PREDICTION)",
)
@click.option(
    "--max-assets",
    default=None,
    type=int,
    help="Maximum number of assets to consider",
)
@click.option(
    "--json-args",
    default=None,
    type=str,
    help="Specific parameters to pass to the trainer (for example Yolov5 train, Hugging Face transformers, ...",
)
@click.option(
    "--clear-dataset-cache",
    default=False,
    is_flag=True,
    help="Tells if the dataset cache must be cleared",
)
def main(
    api_key: str,
    model_framework: str,
    model_name: str,
    model_repository: str,
    project_id: str,
    label_types: str,
    max_assets: int,
    json_args: str,
    clear_dataset_cache: bool,
):
    """ """
    kili = Kili(api_key=api_key)
    input_type, jobs = get_project(kili, project_id)

    training_losses = []
    for job_name, job in jobs.items():
        content_input = job.get("content", {}).get("input")
        ml_task = job.get("mlTask")
        tools = job.get("tools")
        training_loss = None
        if (
            content_input == ContentInput.Radio
            and input_type == InputType.Text
            and ml_task == MLTask.Classification
        ):
            assets = get_assets(kili, project_id, parse_label_types(label_types))
            assets = assets[:max_assets] if max_assets is not None else assets
            training_loss = train_text_classification_single(
                api_key,
                assets,
                job,
                job_name,
                model_framework,
                model_name,
                model_repository,
                project_id,
                clear_dataset_cache,
            )
        elif (
            content_input == ContentInput.Radio
            and input_type == InputType.Text
            and ml_task == MLTask.NamedEntitiesRecognition
        ):
            assets = get_assets(kili, project_id, parse_label_types(label_types))
            assets = assets[:max_assets] if max_assets is not None else assets
            training_loss = train_ner(
                api_key,
                assets,
                job,
                job_name,
                model_framework,
                model_name,
                model_repository,
                project_id,
                clear_dataset_cache,
            )
        elif (
            content_input == ContentInput.Radio
            and input_type == InputType.Image
            and ml_task == MLTask.ObjectDetection
            and Tool.Rectangle in tools
        ):
            training_loss = train_image_bounding_box(
                api_key,
                job,
                job_name,
                max_assets,
                json.loads(json_args) if json_args is not None else {},
                model_framework,
                model_name,
                model_repository,
                project_id,
                parse_label_types(label_types),
                clear_dataset_cache,
            )
        else:
            kili_print("not implemented yet")
        training_losses.append([job_name, training_loss])
    kili_print()
    print(tabulate(training_losses, headers=["job_name", "training_loss"]))


if __name__ == "__main__":
    main()
