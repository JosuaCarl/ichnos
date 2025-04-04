import requests

def get_cpu_impact(cpu_name: str):
    # Construct API URL and headers
    url = "https://api.boavizta.org/v1/component/cpu?verbose=false"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = { "name": cpu_name }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()['impacts']['gwp']['embedded']['value']

print(get_cpu_impact("Intel Core i7-11700K"))