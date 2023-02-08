# General

A script needs a template (-t) and a CSV list of sites/variables (-i)

* use -h on all bash scripts for help
* use -r to save the JSON output
* use -v for more information

# Area API example

./area.bash -t templates/drone.json -i area.csv -o out -v 

# Path API example

./path.bash -t templates/drone_path.json -i path.csv -o out -v -r
