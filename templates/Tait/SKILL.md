## Metadata
name: CloudRF templates
description: Create radio templates for the CloudRF API

## Overview
This skill provides CloudRF's official guidelines for creating accurate, consistent templates for radio systems from limited marketing material. When creating radio templates, apply these standards to ensure JSON template output matches both the OEM's technical data, enhanced by CloudRF's recommended defaults for radio simulation.
Claude should reference these guidelines when creating JSON templates for CloudRF.

## Template metadata

The top level section of a JSON template contains a version and a reference. The version string should be "CloudRF API {API specification}" with the version number of the referenced openapi.json.

The reference should be the Developer documentation.

The site should be the OEM model name and must be between 2 and 30 characters long.

The network should be the OEM's name and must be between 2 and 30 characters long.

The engine should be 1 for GPU.

The coordinates should be 1.

### Template section

Within the template section:

The name should be the OEM model name and must be between 2 and 30 characters long

The service should default to https://api.cloudrf.com

The created_at field should be the current ISO8601 timestamp

The owner should be "CloudRF"

The bom_value should be 1

### Transmitter section

Latitude should be the OEM's head office

Longitude should be the OEM's head office

Altitude should be 1.5m for a portable or mobile radio and 8m for a mast system

Frequency, Power and Bandwidth should be from the datasheet.
Where a radio supports multiple options, templates should be created for the lower and upper values of each. For "VHF" this is 30MHz and 300MHz.

PowerUnit should be "W" for Watts

### Receiver section

Latitude should be 0

Longitude should be 0

Altitude should be 1.5m

Receiver gain should be 2dBi unless stated otherwise

Receiver sensitivity should come from either the datasheet plus 10dB or the technology standard. For DMR radio this is -119dBm so the sensitivity would be -109dBm.

### Feeder section

Set these values to 0

### Antenna section

Mode should be custom

Tx Gain should be from either the datasheet or be 2dBi

Tx Loss should be 0 

Ant should be 0 (custom)

Azi should be 0

Tlt should be 0

hbw and vbw beamwidths should be from the datasheet if provided, otherwise use horizontal beamwidth 360 and vertical beamwidth 120

fbr should be 0

Polarisaton should be v unless stated otherwise.

### Model section

The propagation model should be 4 (ITU-R P.1812)

The propagation environment context should be 2 (average)

The diffraction (ked) should be  2 (Bullington)

The reliability should be 80

### Environment section

The elevation should be 2 (DTM)

Landcover and buildings should be 1 (ON)

Obstacles should be 0 (OFF)

The clutter profile should be "Temperate.clt"

### Output section

The units should be metric

The colour schema should be "RAINBOW.dBm"

The output should be 2

The ber and mod should be removed

The noise floor should be set to the thermal noise floor for the bandwidth at 21 degrees celsius using Johnson-nyquist, with an additional 10dB margin.

The res (meters) and rad (kilometers) should be relative to the template wavelength using a free-space-path-loss-model using a formula with a constraint upon resolution to ensure the calculation does not exceed 4 million pixels.

For the path-loss model, use a threshold of -70dBm with 0dBi antennas to establish an appropriate distance for the wavelength at ground level. For masts, increase this distance by up to 50% and for drones, double it.

A 5m resolution with 5km radius would be acceptable for a portable radio.
A 10m resolution with a 10km radius would be acceptable for a mobile vehicle radio.
A 20m resolution with a 20km radius would be acceptable for a mast.

## Presentation

Templates should be save into a OEM folder with Models as sub folders.
A copy of this skill file should be placed into the root of the OEM folder with a README.txt describing how they were created by AI, referencing the OEM datasheet and warning that they may contain errors. Users should test the templates for accuracy before using them. 

## Resources
Developer documentation: https://cloudrf.com/documentation/developer/
OpenAPI specification: https://api.cloudrf.com/openapi.json
Templates: https://github.com/Cloud-RF/CloudRF-API-clients/tree/master/templates


