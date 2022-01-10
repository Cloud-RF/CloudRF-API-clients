## Area coverage from CSV
Endpoint: https://api.cloudrf.com/v1/area
KMZ files will be saved to ./out

    python3 area.py -i area.csv -o out -r -v
    
## Path profile from CSV
Endpoint: https://api.cloudrf.com/v1/path
Will test several paths and receive outputs as KMZ, URL, and HTML.

        python3 path.py -i path.csv -o out -r -v

## Best server from CSV
Check sites against a pre-defined network
Endpoint: https://api.cloudrf.com/network

    python3 network.py -i network.csv -o out -r -v
    

