
## Windows clients
These .exe clients have been built from the Python source for Windows 10 x64.

## WARNING: May be detected as malware  
Windows Defender has been reported to flag these .exe files as malware because they contain a HTTPS network client compiled from Python which it regards as suspicious.
If this happens, you will need to configure Windows Defender to ignore this folder or at least visit it after it's quarantined a file to manually permit it.

If in doubt, you can build the files from source yourself using the build.bat script within the Python folder.

### Commercial use
You are free to use this API in commercial apps, even ones where you charge customers, but you **must provide attribution to CloudRF**. If you want an exemption, you need to request written permission via support@cloudrf.com
Full terms and conditions are here: https://cloudrf.com/terms-and-conditions
You will be responsible for your account and how it is used.

## Examples

### Point-to-multipoint "heatmap"  x3
The CSV file contains the sites and the JSON file contains the template for the transmitter/receiver/environment etc. Unique values (Latitude,Longitude) belong in the CSV and common criteria (Frequency, Power) belong in the JSON.

    area.exe -i 3sites.csv -t drone.json

### Point-to-point link
As before but this time a receiver location is defined.

    path.exe -i link.csv -t drone.json
    
### Route analysis 
A route of "points" is tested in a single call. The points object is an array of tuples (lat,lon,alt) in quotes as follows:
"[(38.916, 1.411, 1), (38.919, 1.411, 1), (38.922, 1.411), (38.93, 1.427), (38.921, 1.448), (38.976, 1.44)]"

    points.exe -i route.csv -t drone.json
    
### Network analysis
A previously created network is tested against a customer location for service.
This requires a network to exist in your account.

    network.exe -i network.csv
    
## Advanced
All programs come with a help menu which you can show with either -h or /?

### Outputs
Options vary by application but you can download outputs in different formats including KML, KMZ, GeoTIFF, SHP and ZIP.

### Handling data where every row has unique values
If there are no common criteria you can put every setting into a spreadsheet with unique column names and then use a 'custom' template with matching override tags on each option. You pick the column names - so long as they align to the right place in the JSON.

## Ingesting data from Tower Coverage

An example for using formatted data from Tower Coverage:

    area.exe -i towercoverage.csv -t custom.json

Note that the tower coverage API has Tx power in dBm and in CloudRF Tx the unit is Watts. Antenna codes are unique to the system so will also need re-mapping.
A calculator is here: https://www.rapidtables.com/convert/power/dBm_to_Watt.html

