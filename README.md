## Cloud-RF API clients
These code examples will automate the your RF modelling and integrate your app(s) with the powerful Cloud-RF API for path, area, points and network calculations. 

Designed for any operating system with examples for Linux, MacOS and Windows they can be operated as standalone apps or with a spreadsheet of data in CSV format.
An internet connection and account at https://cloudrf.com is required.

![Ibiza VHF coverage with 3D buildings ](https://cloudrf.com/files/ibiza.vhf.jpg)
### Commercial use
The Cloud-RF API is ideal for front office with a custom branded interface, back office processing with network data and M2M for network maps with dynamic updates. 
We love to help companies crunch their data, grow their products and make new services with our API but if you want to to charge your customers for this you must seek permission first by emailing support@cloudrf.com
Full terms and conditions are here: https://cloudrf.com/terms-and-conditions

### API versions
Both API versions connect to the same service at https://api.cloudrf.com and will generate calculations in your account which you can find through any interface. Both have the same terrain, antennas and clutter.

#### API v1
The *original* Cloud-RF API since 2012. Uses request parameters and authentication is in the request as a 'uid' and a 'key'.
#### API v2
The **new API** since June 2021. Uses a JSON body and authentication is in the header as a 'key'. Supports radio templates and configurations as .json files.

### Authentication
Authentication is required. API keys vary by version. V1 consists of a user identifier (uid) and a private API key (key). V2 is just a key.
You should protect your API key as it can be used to create, view and delete calculations associated with your account.
To get a key, signup for an account at https://cloudrf.com

### Demo key
If you don't want to sign up for an account you can exercise the API using the following public use API key which is **limited to the island of Ibiza for testing**. You may be asked to wait if someone else is using the key as it is rate limited..

    uid = 101
    key = IBIZA.DEMO.KEY
    
*Ibiza is a Mediterranean island east of Spain which we have re-branded the "RF-party island". Ibiza's rugged terrain and coastlines are ideal for demonstrating RF propagation modelling.*

### Documentation
Introduction https://cloudrf.com/documentation/introduction.html
3D interface https://cloudrf.com/documentation/interface.html
API 1 reference https://documenter.getpostman.com/view/3523402/7TFGb35
API 2 reference https://docs.cloudrf.com
User documentation: https://cloudrf.com/docs
Video tutorials: https://youtube.com/cloudrfdotcom

## Code and examples

[API v1 code and examples](API%20v1)

[API v2 code and examples](API%20v2)

