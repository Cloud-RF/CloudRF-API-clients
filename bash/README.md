# General

A script needs a template (`-t`) and a CSV list of sites/variables (`-i`).

* Use `-h` on all bash scripts for help.
* Use `-r` to save the JSON output.
* Use `-v` for more information.

# Authentication

Enter your API key into the cloudrf.ini file.


    [user]
    key = 12345-9d1ce4802d415ee94c46e7c8796b2b7b6e0ddead

# Area API Example

```
./area.bash -t templates/drone.json -i area.csv -o out -v 
```

# Path API Example

```
./path.bash -t templates/drone_path.json -i path.csv -o out -v -r
```
