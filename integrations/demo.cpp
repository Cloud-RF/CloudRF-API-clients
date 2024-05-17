#include <iostream>
#include <fstream>
#include <fstream>
#include <sstream>
#include <string>
#include <curl/curl.h>
#include <unistd.h>
#include <string>

#include "include/json.hpp"

using json = nlohmann::json;

/*--------------------FEEL FREE TO CHANGE SETTINGS--------------------*/

const float RADIUS = 30; //           simulation radius in kilometers
const float RESOLUTION = 30; //       simulation resolution in metres
const float ANTENNA_ALTITUDE = 15; // ship antenna altitude above sea level in metres

const float SLEEP_TIME = 2; //        time between each update, 2 recomended

/*---------------------------------------------------------------------*/

std::string ais_api_key;
std::string rf_api_key;

std::ostringstream stream;

std::ifstream ais_api_file("ais-api-key.txt"); // enter APRS API key in a file named "ais-api-key.txt"
std::ifstream rf_api_file("rf-api-key.txt"); // enter CloudRF API key in a file named "rf-api-key.txt"

std::string ais_api_url = "https://api.aprs.fi/api/get?name=OH7RDA&what=loc&apikey=<API KEY>format=json";
std::string rf_api_url = "https://api.cloudrf.com/area";

std::string name;

// function to write data recieved from APIs to stream
size_t write_data(char *ptr, size_t size, size_t nmemb, void *userdata)
{
    std::ostringstream *stream = (std::ostringstream *)userdata;
    size_t count = size * nmemb;
    stream->write(ptr, count);
    return count;
}

int main(int argc, char *argv[])
{

    // get APRS API key from files
    std::getline(ais_api_file, ais_api_key);
    ais_api_file.close();

    // get CloudRF API key from files
    std::getline(rf_api_file, rf_api_key);
    rf_api_file.close();

    // get ship MMSI
    std::cout << "Enter ship name (MMSI): "; std::cin >> name;

    ais_api_url = "https://api.aprs.fi/api/get?name=" + name + "&what=loc&apikey=" + ais_api_key + "&format=json";

    CURL *curl;
    CURLcode res;

    // initialise on windows
    curl_global_init(CURL_GLOBAL_ALL);

    // initialise curl
    curl = curl_easy_init();

    struct curl_slist *slist1 = NULL;
    slist1 = curl_slist_append(slist1, "Content-Type: application/json");
    curl_slist_append(slist1, "Accept: application/json");
    curl_slist_append(slist1, "charsets: utf-8");

    if (curl) // if curl initialised
    {

        while (true)
        {

            stream = std::ostringstream("");

            sleep(SLEEP_TIME); // sleep to not spam APIs

            double lat, lon;

            /* get ship location from APRS API */ {

                // settings for APRS API request
                curl_easy_setopt(curl, CURLOPT_URL, ais_api_url.c_str());
                curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);
                curl_easy_setopt(curl, CURLOPT_WRITEDATA, &stream);

                // make request to APRS
                curl_easy_perform(curl);

                try // APRS may return JSON with error and not contain "entries"
                {

                    // parse ship position
                    json j = json::parse(stream.str());

                    lat = std::stof((std::string)j["entries"][0]["lat"]);
                    lon = std::stof((std::string)j["entries"][0]["lng"]);
                }
                catch (...)
                {
                    std::cerr << "Error getting ship location:\n";
                    std::cerr << stream.str();
                }
            }

            // url to hearmap data
            std::string heatmap_href;

            /* get heatmap from CloudRF API */ {

                // request settings e.g. transmitter, antena etc. in JSON format
                std::string rf_request_data = "{ \"engine\": 1, \"site\" : \"A1\", \"network\" : \"Testing\", \"transmitter\" : { \"lat\" : " + std::to_string(lat) + ", \"lon\" : " + std::to_string(lon) + ", \"alt\" : + " + std::to_string(ANTENNA_ALTITUDE) + ", \"frq\" : 160, \"txw\" : 10, \"bwi\" : 1 }, \"model\": { \"pm\": 7, \"pe\": 2, \"ked\": 0}, \"receiver\" : { \"lat\" : 0, \"lon\" : 0, \"alt\" : 2, \"rxg\" : 3, \"rxs\" : -100 }, \"antenna\" : { \"txg\" : 2.15, \"txl\" : 1, \"ant\" : 1, \"azi\" : 1, \"tlt\" : 10, \"hbw\" : 2, \"vbw\" : 2, \"pol\" : \"h\" }, \"environment\": { \"elevation\": 2, \"landcover\": 0, \"buildings\": 0}, \"output\": { \"units\" : \"metric\", \"col\" : \"RAINBOW.dBm\", \"out\" : 2, \"ber\" : 2, \"mod\" : 7, \"nf\" : -100, \"res\" : " + std::to_string(RESOLUTION) + ", \"rad\" : " + std::to_string(RADIUS) + " }} ";

                stream = std::ostringstream("");

                // declare curl request headers for API key
                struct curl_slist *slist1 = NULL;
                std::string header = "key: " + rf_api_key;
                slist1 = curl_slist_append(slist1, header.c_str());

                // settings for CloudRF API request
                curl_easy_setopt(curl, CURLOPT_URL, (rf_api_url).c_str());
                curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);
                curl_easy_setopt(curl, CURLOPT_WRITEDATA, &stream);
                curl_easy_setopt(curl, CURLOPT_POST, 1);
                curl_easy_setopt(curl, CURLOPT_HTTPHEADER, slist1);
                curl_easy_setopt(curl, CURLOPT_POSTFIELDS, rf_request_data.c_str());

                // make request to CloudRF
                curl_easy_perform(curl);

                try // CloudRF may return JSON with error and not contain "kmz"
                {
                    json j_update_heatmap = json::parse(stream.str());
                    heatmap_href = j_update_heatmap["kmz"]; // url to heatmap data
                }
                catch (...)
                {
                    std::cerr << "Error getting heatmap:\n";
                    std::cerr << stream.str();
                }
            }

            // save pin and heatmap to kml file
            std::ofstream kml_out("ship.kml");

            kml_out << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" << '\n';
            kml_out << "<kml xmlns=\"http://www.opengis.net/kml/2.2\" xmlns:gx=\"http://www.google.com/kml/ext/2.2\">" << '\n';
            kml_out << "    <Document id=\"97\">" << '\n';
            kml_out << "        <NetworkLink id=\"98\">" << '\n';
            kml_out << "            <name>Coverage</name>" << '\n';
            kml_out << "            <Link id=\"99\">" << '\n';
            kml_out << "                <href>" << heatmap_href << "</href>" << '\n';
            kml_out << "                <viewRefreshMode>onRequest</viewRefreshMode>" << '\n';
            kml_out << "            </Link>" << '\n';
            kml_out << "        </NetworkLink>" << '\n';
            kml_out << "        <Placemark id=\"101\">" << '\n';
            kml_out << "            <name>Ship</name>" << '\n';
            kml_out << "            <Point id=\"100\">" << '\n';
            kml_out << "                <coordinates>" << lon << "," << lat << "</coordinates>" << '\n';
            kml_out << "            </Point>" << '\n';
            kml_out << "        </Placemark>" << '\n';
            kml_out << "    </Document>" << '\n';
            kml_out << "</kml>";

            kml_out.close();

            std::cout << "Updated kml file!" << '\n';
        }

        // cleanup curl
        curl_easy_cleanup(curl);
        curl_slist_free_all(slist1);
        curl_global_cleanup();
    }
}