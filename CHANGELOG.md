# CloudRF API Clients Changelog

## 2023-02-08

- Complete redesign of Python example making use of a single entry script for each of the request types: `area`, `interference`, `mesh`, `multisite`, `network`, `path`, `points`.
- Validate file/directory permissions and minimum Python version in Python client.
- Validate CloudRF API key before sending to API in Python client.
- alidate input JSON templates and CSV files in Python client.
- Added `--api-key`, `--base-url`, and `--no-strict-ssl` flags, removing the need for `cloudrf.ini` in Python client.
- Added error logging to output when an API request did not return a HTTP 200 response in Python client.
- Added logic to fix potential broken JSON request for some request types in Python client.
- Added `--save-raw-request` flag to save the response which was sent to the CloudRF API service in Python client.
- Improvements to `--verbose` logging in Python client.
- Updated all slippy map examples to work with new CloudRF logic whereby Ibiza requires an API key. Input box on map example allows you to set this for your environment.
- Added input box on slippy map examples to allow the base URL to be customised.
- Added input box on Mapbox slippy map example to allow you to set your Mapbox public access token without needing to edit the HTML source.
- Removed Windows executables. Instead the Python examples should be run once Python has been installed. Tested as working on Windows 11 with Python 3.11.
- Restructured repository to make directories clearer as to what they do.
- Improvements to all README files, giving instructions on how to execute each example.
- Added GitHub templates for issues on new bugs and feature requests, and on pull requests.
- Added CHANGELOG.

## 2022-11-16

- Removed legacy API v1 examples.

## 2022-10-11

- Added JSON templates.

## 2022-03-23

- Removed `pprint` as requirement, included as standard in Python3.
- Removed deprecated file mode.

## 2022-01-19

- CSV opened in universal newline mode.

## 2022-01-14

- Fixed folder path names.

## 2022-01-10

- Added missing templates.

## 2021-11-30

- Cell tower example.

## 2021-09-30

- Mapbox example.

## 2021-09-23

- Leaflet and OpenLayers examples.

## 2021-09-11

- Updated request in line with CloudRF API.

## 2021-08-11

- Use `sid` from response if returned.

## 2021-07-05

- APIv2 examples.

## 2021-04-16

- Improved documentation.
- Added Bash and Windows executables.

## 2021-04-14

- Added route demo.

## 2020-01-15

- Replaced `aeg` with `txg`, and `bw` with `bwi`.

## 2019-08-22

- Added best server widget example.

## 2019-08-19

- Added LoRa coverage example.

## 2019-05-16

- Updated server address.
- Added Google maps example.

## 2019-04-04

- Replaced `dbm` value with `rxs`.

## 2019-02-17

- Support for Python 2 and 3.
- Save output of path profile.

## 2018-11-29

- Network and mesh Python script.
- Updated API values in line with live API.

## 2018-08-20

- New `path` JavaScript example.

## 2018-07-02

- Added delete from archive example.

## 2018-02-06

- Support for new API.

## 2017-05-10

- Initial release.