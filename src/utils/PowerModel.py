from typing import Any
import json
import src.utils.MathModels as MathModels

"""
Model name format: gpg_<node_id>_<governor>_<model_name>
where governor is either 'ondemand', 'performance', or 'powersave'
and model_name is either 'linear', 'minmax', 'cubic', or 'baseline'"
"""
def get_power_model(model_name: str) -> Any:
    """Return a power model function based on the provided model name."""
    print(f'Model Name Provided: {model_name}')

    with open('node_config_models/gpgnodes.json') as nodes_json_data:
        models = json.load(nodes_json_data)

        model_found: bool = False
        # Get the model data out of the name
        if model_name.startswith('gpg_'):
            model_data = model_name.split('_')
            if len(model_data) != 4:
                print("Unrecognised model name format. Format should be gpg_<node_id>_<governor>_<model_name>.")
                print("E.g. gpg_13_ondemand_minmax | gpg_13_ondemand_linear | gpg_13_ondemand_cubic | gpg_13_performance_minmax")
                print("Exiting...")
                exit(-1)

            node_id: str = "gpg_" + model_data[1]
            governor: str = model_data[2]
            model_type: str = model_data[3]

            # TODO: Refactor this to be more readable
            model_found = node_id in models and governor in models[node_id] and (model_type in models[node_id][governor] or (model_type == 'minmax' and 'min_watts' in models[node_id][governor]) and 'max_watts' in models[node_id][governor])

        if not model_found:
            print("Unrecognised model name. Using default gpg_13_ondemand_minmax model.")
            node_id = "gpg_13"
            governor = "ondemand"
            model_type = "minmax"

        if model_type == 'minmax':
            min_watts = models[node_id][governor]['min_watts']
            max_watts = models[node_id][governor]['max_watts']
            return MathModels.min_max_linear_power_model(min_watts, max_watts)
        elif model_type == 'baseline':
            tdp_per_core = models[node_id][governor]['tdp_per_core']
            return MathModels.baseline_power_model(tdp_per_core)

        return MathModels.polynomial_model(models[node_id][governor][model_type])