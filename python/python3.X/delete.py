#!/usr/bin/python
import requests

# Programmatically delete a calculation by name OR network

server="https://cloudrf.com"
strictSSL=False

uid=str(21531)
key="a8ec44b5ad85e0ab626e55f20e3cb5da111999a2"
network="APITEST"

# Delete by name..
req = requests.get(server+"/API/archive/data.php?uid="+uid+"&key="+key+"&delete=12345_NETWORK_SITE",verify=strictSSL)
result = req.text
print(result)

# Delete by network..
req = requests.get(server+"/API/archive/data.php?uid="+uid+"&key="+key+"&nid="+network+"&del=1",verify=strictSSL)
result = req.text
print(result)




