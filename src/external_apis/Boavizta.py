from src.utils.APIRequests import make_json_post_request, make_json_get_request
from diskcache import Cache

cache = Cache('cache/boavizta_cache')

ALLOWED_COMPONENTS = {
    'cpu',
    'ssd',
    'ram',
    'hdd',
    'motherboard',
    'power_supply',
    'case',
}

@cache.memoize()
def get_component_impact(component: str, name: str):
    """
    Retrieve the embedded Global Warming Potential (GWP) impact value for a hardware component.

    Supports components: cpu, ssd, ram, hdd, motherboard, power_supply, case.

    Args:
        component (str): The component type (one of the supported components).
        name (str): The component name/identifier to query (e.g., "Intel Core i7-11700K").

    Returns:
        float: The embedded GWP impact value.

    Raises:
        ValueError: If the component is not supported.
        RuntimeError: If the API response doesn't contain the expected data.
    """
    component_lower = component.lower()
    if component_lower not in ALLOWED_COMPONENTS:
        raise ValueError(f"Unsupported component '{component}'. Supported: {', '.join(sorted(ALLOWED_COMPONENTS))}")

    print(f"Fetching {component_lower} impact for {name}")
    url = f"https://api.boavizta.org/v1/component/{component_lower}?verbose=false"
    response = make_json_post_request(url, {'name': name})

    try:
        return response['impacts']['gwp']['embedded']['value']
    except Exception as exc:
        raise RuntimeError(f"Unexpected API response structure for component='{component_lower}', name='{name}': {response}") from exc

@cache.memoize()
def get_cpu_impact(cpu_name: str):
    """
    Retrieves the global warming potential (GWP) impact value of a CPU by its name.
    
    Args:
        cpu_name (str): The name of the CPU to query (e.g., "Intel Core i7-11700K").
        
    Returns:
        float: The embedded GWP (Global Warming Potential) impact value of the CPU.
    """
    print(f"Fetching CPU impact for {cpu_name}")
    url = "https://api.boavizta.org/v1/component/cpu?verbose=false"
    return make_json_post_request(url, {'name': cpu_name})['impacts']['gwp']['embedded']['value']

@cache.memoize()
def get_aws_instance_impact(instance_type: str, duration: float = None):
    """
    Retrieves the global warming potential (GWP) impact value of an AWS instance type.
    
    Args:
        instance_type (str): The AWS instance type (e.g., "r6g.medium").
        duration (float, optional): The duration in hours for which to calculate the impact.
                                   If not provided, returns the total impact value.
                                   
    Returns:
        float: The embedded GWP (Global Warming Potential) impact value of the AWS instance.
    """
    print(f"Fetching AWS instance impact for {instance_type} with duration {duration}")
    url = f"https://api.boavizta.org/v1/cloud/instance?provider=aws&instance_type={instance_type}&verbose=false&criteria=gwp"
    if duration: url += f"&duration={duration}"
    return make_json_get_request(url)['impacts']['gwp']['embedded']['value']

if __name__ == "__main__":
	# Example usage
	print(get_cpu_impact("Intel Core i7-11700K"))
	print(get_aws_instance_impact("r6g.medium", 24))