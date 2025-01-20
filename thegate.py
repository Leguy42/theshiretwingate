Python 3.13.1 (tags/v3.13.1:0671451, Dec  3 2024, 19:06:28) [MSC v.1942 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
>>> from gql import gql, Client
... from gql.transport.requests import RequestsHTTPTransport
... 
...... # Twingate API settings
... API_URL = "https://frodosown.twingate.com/api/graphql/"  # Replace <subdomain> with your Twingate subdomain
... API_KEY = "l_-csxQ7ucNxwwzXgXm3JXhT8mLCUxdOAxHJMeJ7eH9XPNp3-9QnyJ3B7MXyQnsGixLeSr93_vlSvNwIpjEhlJQlYr_Rg1sVxx7V3B-zH6j16a5DQwXGY22V7ZM3TvZwabNadQ"
... TARGET_NETWORK_NAME = "TheShire"  # Replace with your target network name
... 
... QUERY_REMOTE_NETWORKS = gql("""
... query GetRemoteNetworkDetails {
...   remoteNetworks(after: null, first: 10) {
...     edges {
...       node {
...         id
...         name
...         connectors {
...           edges {
...             node {
...               id
...               name
...               publicIP
...               privateIPs
...               remoteNetwork {
...                 id
...                 name
...               }
...             }
...           }
...         }
...       }
...     }
...   }
... }
... """)
... 
... MUTATION_CREATE_RESOURCE = gql("""
... mutation CreateResource($name: String!, $address: String!, $remoteNetworkId: ID!) {
  resourceCreate(
    name: $name,
    address: $address,
    remoteNetworkId: $remoteNetworkId
  ) {
    ok
    error
    entity {
      id
      name
      address {
        type
        value
      }
    }
  }
}
""")

def setup_client():
    transport = RequestsHTTPTransport(
        url=API_URL,
        headers={"X-API-KEY": API_KEY},
        use_json=True,
    )
    return Client(transport=transport, fetch_schema_from_transport=True)

def get_target_network(client):
    response = client.execute(QUERY_REMOTE_NETWORKS)
    for edge in response["remoteNetworks"]["edges"]:
        network = edge["node"]
        if network["name"] == TARGET_NETWORK_NAME:
            return network
    return None

def create_resource(client, name, address_value, remote_network_id):
    params = {
        "name": name,
        "address": address_value,
        "remoteNetworkId": remote_network_id
    }
    response = client.execute(MUTATION_CREATE_RESOURCE, variable_values=params)
    if not response["resourceCreate"]["ok"]:
        raise Exception(f"Failed to create resource: {response['resourceCreate']['error']}")
    return response["resourceCreate"]["entity"]

def automate_resource_creation():
    client = setup_client()

    print(f"Searching for target network: {TARGET_NETWORK_NAME}...")
    target_network = get_target_network(client)

    if not target_network:
        print(f"Network '{TARGET_NETWORK_NAME}' not found.")
        return

    print(f"Found network: {target_network['name']}")
    remote_network_id = target_network['id']

    for connector_edge in target_network["connectors"]["edges"]:
        connector = connector_edge["node"]
        public_ip = connector.get("publicIP")
        private_ips = connector.get("privateIPs", [])

        if public_ip:
            resource_name = f"Resource-Public-{public_ip.replace('.', '-')}"
            print(f"Creating Resource for public IP: {public_ip}...")
            resource = create_resource(client, resource_name, public_ip, remote_network_id)
            print(f"Resource created: {resource['name']} (ID: {resource['id']}, Address: {resource['address']['value']})")

        for private_ip in private_ips:
            resource_name = f"Resource-Private-{private_ip.replace('.', '-')}"
            print(f"Creating Resource for private IP: {private_ip}...")
            resource = create_resource(client, resource_name, private_ip, remote_network_id)
            print(f"Resource created: {resource['name']} (ID: {resource['id']}, Address: {resource['address']['value']})")

if __name__ == "__main__":
    try:
        automate_resource_creation()
    except Exception as e:
        print(f"Error: {e}")
