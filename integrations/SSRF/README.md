# Standard Spectrum Resource Format (SSRF) API client

This Rust client is capable of processing Standard Spectrum Resource Format (SSRF) XML documents through the CloudRF/SOOTHSAYER API.

SSRF-XML is used to share spectrum information including transmitters, receivers, geo location and propagation ranges. By pushing this **public**  data through our GPU accelerated "Multisite" API, we can rapidly model complex systems in seconds which previously would have been impossible in a practical time frame or with a unpublished spectrum standard.

![Network interference](network_interference.jpg "Network interference")

## Setup

    apt-get install cargo


## Generate test data

A test script to generate SSRF XML exists called gen_xml.sh.
Within this you can set a center point, maximum number of transmitters and a random distance error measured in degrees. The demo below will generate up to 32 transmitters in England, spread across 0.01 degrees of latitude/longitude.

    cargo run -p openssrf_test_xml_generator -- --lat 51.7 --lon -2.4  -m 32 --std 0.01 -o ./xml

## Multisite pipeline

This iterates over a folder of xml documents and processes each in turn. To use it you will need an API like https://api.cloudrf.com and an API key.
Define both as environment variables so the gen_kmz.sh script can find them.

    cargo run -p openssrf_multisite_pipeline -- -k $API_KEY --url $API_URL -i ./xml -o

## Merge test data

To combine SSRF XML files into one, you can use the openssrf_xml_merger like so:

    cargo run -p openssrf_xml_merger -- -i xml/rnd-ssrf-016.xml -i xml/rnd-ssrf-032.xml -i xml/rnd-ssrf-064.xml -o ssrf-interference-data.xml

## Interference analysis

To run multisite and then interference analysis between the assignments in an SSRF XML document, run the following:

    cargo run -p openssrf_interference_analysis -- -k $API_KEY --url $API_URL -i two-32-radio-networks-1W-1W.ssrf.xml -o kmz


## Further reading

https://github.com/KeyBridge/lib-openssrf

https://cloudrf.com/documentation/developer/



## Credits

Credit to Key Bridge Global LLC and the Wireless Innovation Forum for publishing their excellent OpenSSRF resources on Github. 

