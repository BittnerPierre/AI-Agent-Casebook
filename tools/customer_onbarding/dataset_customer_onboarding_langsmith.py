import json
from dotenv import find_dotenv, load_dotenv
from langsmith import Client

# Load environment variables
load_dotenv(find_dotenv())

# Initialize the LangSmith client
client = Client()

# Define dataset name and description
FILE_NAME = "dataset_customer_onboarding_simple.json"
DATASET_NAME = "CUSTOMER-ONBOARDING-SIMPLE-datasets-04-12-2024"
DESCRIPTION = "Simple Dataset for testing customer onboarding assistant"

# Check if the dataset already exists
datasets = list(client.list_datasets(dataset_name=DATASET_NAME))

if datasets:
    dataset = datasets[0]
    print(f"Dataset '{DATASET_NAME}' already exists.")
else:
    # Create the dataset if it doesn't exist
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description=DESCRIPTION
    )
    print(f"Dataset '{DATASET_NAME}' created.")

# Load examples from the JSON file
with open(FILE_NAME, 'r', encoding='utf-8') as file:
    examples = json.load(file)

# Retrieve existing examples from the dataset
existing_examples = list(client.list_examples(dataset_id=dataset.id))

# Create a mapping of existing examples based on their inputs
existing_inputs_map = {
    json.dumps(example.inputs, sort_keys=True): example
    for example in existing_examples
}

# Add or update each example in the dataset
for example in examples:
    inputs = example.get('inputs', {})
    outputs = example.get('outputs', {})
    metadata = example.get('metadata', {})

    # Serialize inputs to JSON for comparison
    serialized_inputs = json.dumps(inputs, sort_keys=True)

    if serialized_inputs in existing_inputs_map:
        # Update the existing example
        existing_example = existing_inputs_map[serialized_inputs]
        client.update_example(
            example_id=existing_example.id,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata
        )
        print(f"Updated example with ID: {existing_example.id}")
    else:
        # Create a new example
        new_example = client.create_example(
            inputs=inputs,
            outputs=outputs,
            metadata=metadata,
            dataset_id=dataset.id
        )
        print(f"Created new example with ID: {new_example.id}")
