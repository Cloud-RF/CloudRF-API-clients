# General

A script needs a template (`-t`) and a CSV list of sites/variables (`-i`).

* Use `-h` on all bash scripts for help.
* Use `-r` to save the JSON output.
* Use `-v` for more information.

# Area API Example

```
./area.bash -t templates/drone.json -i area.csv -o out -v 
```

# Path API Example

```
./path.bash -t templates/drone_path.json -i path.csv -o out -v -r
```
