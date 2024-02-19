# Standard Spectrum Resource Format (SSRF) API client

This Rust client is capable of processing Standard Spectrum Resource Format (SSRF) XML documents through the CloudRF/SOOTHSAYER API.

SSRF-XML is used to share spectrum information including transmitters, receivers, geo location and propagation ranges. By pushing this **public**  data through our GPU accelerated "Multisite" API, we can rapidly model complex systems in seconds which previously would have been impossible in a practical time frame or with a unpublished spectrum standard.

## Setup

    apt-get install cargo

To use it you will need an API like https://api.cloudrf.com and an API key.
Define both as environment variables so the gen_kmz.sh script can find them.

    cargo run -q -p openssrf_multisite_pipeline -- -k $API_KEY --url $API_URL -i ./xml -o ./kmz -ncv


## Generate test data

A test script to generate SSRF XML exists called gen_xml.sh.
Within this you can set a center point, maximum number of transmitters and a random distance error measured in degrees. The demo below will generate up to 512 transmitters in Switzerland.

    cargo run -q -p openssrf_test_xml_generator -- --lat 47 --lon 8  -m 512 --std 0.2 -o ./xml


## Further reading

https://github.com/KeyBridge/lib-openssrf

https://cloudrf.com/documentation/developer/



## Credits

Credit to Key Bridge Global LLC and the Wireless Innovation Forum for publishing their excellent OpenSSRF resources on Github. 

