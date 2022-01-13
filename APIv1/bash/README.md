## Area coverage from CSV
Endpoint: https://api.cloudrf.com/v1/area
KMZ files will be saved to ./out

    ./area.bash -i area.csv -v

## Path profile from CSV
Endpoint: https://api.cloudrf.com/v1/path
JSON files will be saved to ./out

        ./path.bash -i path.csv -v -r

## Best server from CSV
Check sites against a pre-defined network
Endpoint: https://api.cloudrf.com/network

    /network.bash -i network.csv -v -r
    
