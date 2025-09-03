import json
import os
from src.Constants import DEFAULT_MEMORY_POWER_DRAW

def get_cpu_model(model_name: str, node_config_file: str = os.path.join("node_config_models", "nodes.json")) -> str:
	"""
	Retrieves the CPU model from the node configuration model name.
	
	Args:
		model_name (str): The name of the node configuration model.
		
	Returns:
		str: The CPU model extracted from the node configuration model name.
	"""
 
	with open(node_config_file) as nodes_json_data:
		models = json.load(nodes_json_data)

		# Get the model data
		model_data = model_name.split('_')
		node_id: str = model_data[0]
		governor: str = model_data[1]
  
		return models[node_id][governor]['cpu_model']

def get_memory_draw(model_name: str, node_config_file: str = os.path.join("node_config_models", "nodes.json")) -> float:
    try:
        with open(node_config_file) as nodes_json_data:
            models = json.load(nodes_json_data)

            # Get the model data
            model_data = model_name.split('_')
            node_id: str = model_data[0]
            governor: str = model_data[1]

            return models[node_id][governor]['mem_draw']
    except:
        return DEFAULT_MEMORY_POWER_DRAW

def get_system_cores(model_name: str, node_config_file: str = os.path.join("node_config_models", "nodes.json")) -> int:
    with open(node_config_file) as nodes_json_data:
        models = json.load(nodes_json_data)

        # Get the model data
        model_data = model_name.split('_')
        node_id: str = model_data[0]
        governor: str = model_data[1]

        return models[node_id][governor]['system_cores']
