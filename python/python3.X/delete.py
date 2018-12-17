#!/usr/bin/python

# Programmatically delete a calculation by name.
# Requires session authentication with archive

server="https://cloudrf.com"
user= "my@email.com"
password= "SECRET!"
uid="1234"
site= "CALCULATION_NAME"

session = requests.Session()
session.auth = (user,password)
auth = session.post(server + "/API/archive")
payload = {'uid': uid, 'delete': site}
r = session.get(server + "/API/archive/index.php", params=payload)
print(r.text)
