# Cloud-RF API Clients

![CloudRF API VHF coverage in Ibiza with 3D buildings enabled](https://cloudrf.com/files/ibiza.vhf.jpg)

The code examples within this repository can be used to automate your RF modelling and/or integrate your application(s) with the powerful CloudRF API.

These examples have been built around some of the most common applications around RF modelling and its presentation.

If you have integrated your own application(s) with the CloudRF API and wish to share with others then pull requests to this repository are welcome. Similarly, if there are common usecases which are not included in these examples please raise a feature request via the GitHub issues submission and we will work towards adding the most popular.

In order to make use of these examples you will require:

- An internet connection which is accessible to the CloudRF API service of [https://api.cloudrf.com](https://api.cloudrf.com).
- An account on the CloudRF service with your API key. This can be obtained from [https://cloudrf.com/my-account](https://cloudrf.com/my-account).

## Examples

Below are the list of available examples which can be used. You are encouraged to read the respective `README.md` for each which will detail additional information and usage.

- The [python](python/) directory contains a parent Python 3 script which allows interaction with all of the primary CloudRF API endpoints. This script is quite comprehensive and so for usage you are recommended to consult the [README](python/README.md) for more information.
- The [bash](bash/) directory contains some Bash scripts which make use of cURL to to CloudRF API.
- The [slippy-maps](slippy-maps/) directoriy contains examples of various slippy map libraries which interface with the CloudRF API to present layers of RF coverage and results.
- The [templates](templates/) directory contains a list of example JSON templates which can be used to interface with the CloudRF API. For a more comprehensive list of templates you should consult the [CloudRF UI](https://cloudrf.com/ui).

You can view a live hosted version of the [slippy map](slippy-map) examples at [https://cloud-rf.github.io/CloudRF-API-clients/slippy-maps/index.html](https://cloud-rf.github.io/CloudRF-API-clients/slippy-maps/index.html)

## Commercial Use

You are free to use this API in commercial apps, even ones where you charge customers. Attribution is welcomed but not required.

Full terms and conditions are available at [https://cloudrf.com/terms-and-conditions](https://cloudrf.com/terms-and-conditions)

You will be responsible for your account and how it is used. 

## Resources

Below are a list of resources which may aid you with writing your own clients to integrate with the CloudRF API.

- CloudRF Website: [https://cloudrf.com/](https://cloudrf.com/)
- API Swagger UI OpenAPI Reference: [https://cloudrf.com/documentation/developer/swagger-ui/](https://cloudrf.com/documentation/developer/swagger-ui/)
- API Postman Reference: [https://docs.cloudrf.com/](https://docs.cloudrf.com/)
- 3D User Interface: [https://cloudrf.com/ui/](https://cloudrf.com/ui/)
- User Documentation: [https://cloudrf.com/documentation](https://cloudrf.com/documentation)
- Video Tutorials: [https://youtube.com/cloudrfdotcom](https://youtube.com/cloudrfdotcom)
