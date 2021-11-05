## Cloud-RF API clients
These code examples will automate the your RF modelling and integrate your app(s) with the powerful Cloud-RF API for path, area, points and network calculations.

Designed for any operating system with examples for Linux, MacOS and Windows they can be operated as standalone apps or with a spreadsheet of data in CSV and JSON formats.
An internet connection and account at https://cloudrf.com is required.

![Ibiza VHF coverage with 3D buildings ](https://cloudrf.com/files/ibiza.vhf.jpg)
### Commercial use
You are free to use this API in commercial apps, even ones where you charge customers, but you **must provide attribution to CloudRF**. If you want an exemption, you need to request written permission via support@cloudrf.com
Full terms and conditions are here: https://cloudrf.com/terms-and-conditions
You will be responsible for your account and how it is used.

####  API technical description
A standard HTTP request with a JSON body with authentication in the HTTP header as a 'key'. The JSON body is a nested object with human readable sections eg. Transmitter->Antenna, Receiver->Antenna.


### Authentication
Authentication is required and looks like a long string which starts with a number, then a hyphen, then a long random string eg. 123-deadbeef
You should protect your API key as it can be used to create, view and delete calculations associated with your account.
To get a key, signup for an account at https://cloudrf.com

### Demo key
If you don't want to sign up for an account you can exercise the API using the following public use API key which is **limited to the island of Ibiza for testing**. You may be asked to wait if someone else is using the key as it is rate limited..

    uid = 101
    key = IBIZA.DEMO.KEY

*Ibiza is a Mediterranean island east of Spain which we have re-branded the "RF-party island". Ibiza's rugged terrain and coastlines are ideal for demonstrating RF propagation modelling.*
Map: https://www.google.com/maps/place/Ibiza/

### Documentation
Introduction https://cloudrf.com/documentation/introduction.html

3D interface https://cloudrf.com/documentation/interface.html

Postman code examples https://docs.cloudrf.com

Swagger (OAS3) spec https://cloudrf.com/documentation/developer/swagger-ui/

User documentation: https://cloudrf.com/documentation

Video tutorials: https://youtube.com/cloudrfdotcom

## Code and examples

We have example clients for Bash, Python, OpenLayers and LeafletJS.
If you'd like one adding email support@cloudrf.com

