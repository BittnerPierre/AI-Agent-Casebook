from dotenv import find_dotenv, load_dotenv
from langsmith import Client

_ = load_dotenv(find_dotenv())

client = Client()

dataset_name = "ELIGIBILITY-datasets-26-11-2024"
datasets = client.list_datasets(dataset_name=dataset_name)
if not datasets:
    raise ValueError(f"Dataset '{dataset_name}' not found.")

try:
    dataset = next(datasets)
    print(dataset)
except StopIteration:
    raise ValueError(f"Dataset '{dataset_name}' not found.")


examples = client.list_examples(dataset_id=dataset.id)

import json

examples_data = [
    {
        "id": str(example.id),
        "inputs": example.inputs,
        "outputs": example.outputs,
        "metadata": example.metadata,
        "created_at": example.created_at.isoformat(),
        "modified_at": example.modified_at.isoformat(),
    }
    for example in examples
]

with open("dataset_examples_redteaming.json", "w") as f:
    json.dump(examples_data, f, indent=2)