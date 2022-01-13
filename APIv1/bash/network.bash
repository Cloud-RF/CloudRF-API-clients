#!/bin/bash
# CloudRF Area API bash demo application
# Please run with -h option for help

OUTPUT_DIR=out

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -v)
    VERBOSE=YES
    shift # past argument
    ;;
    -i)
    INPUT="$2"
    shift # past argument
    shift # past value
    ;;
    -o)
    OUTPUT_DIR="$2"
    mkdir -p $OUTPUT_DIR
    shift # past argument
    shift # past value
    ;;
    -r)
    SAVE_RESPONSE=YES
    shift # past argument
    ;;
    -h)
    echo "area.bash API demo"
    echo "usage: network.bash [-h] [-i data_file] [-o output_dir] [-r] [-v]"
    echo ""
    echo "CloudRF Network application"
    echo ""
    echo "Query your networks to find the best server for a customer."
    echo ""
    echo "This demonstration program utilizes the CloudRF Network API to display the following values"
    echo "Site"
    echo "Distance"
    echo "Received signal power dBm"
    echo ""
    echo "Please refer to API Reference https://api.cloudrf.com/"
    echo ""
    echo "arguments:"
    echo "  -h, --help            show this help message and exit"
    echo "  -i data_file          data input filename(csv)"
    echo "  -o output_dir         output directory where files are downloaded"
    echo "  -r                    save response content (json/html)"
    echo "  -v                    Output more information on screen"
    exit 0
    ;;

esac
done

# Read config file using bash native parser, section names are ignored
source <(grep = cloudrf.ini | sed 's/ *= */=/g')

if [ "$VERBOSE" == "YES" ];
then
	curl_verb=""
else
	curl_verb="-s"  # silent
fi;

OLDIFS=$IFS
IFS=','

# Making sure csv file exists
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }

api_end_point=${base_url}/API/network/

echo "api_end_point=${api_end_point}"

# The following section passes data from CSV rows to Web API.
# The data assignment follows the first header row from the CSV file so that variables are not hard-coded.
row_count=0
while read -a row
do
	# Capturing headers from 1st row
	if [ $row_count -eq 0 ];
	then
		header=("${row[@]}")
	else
		# Building API arguments string
		data="key=$key&uid=$uid"
		i=0
		for h in "${row[@]}"
		do
			data="${data}&${header[$i]}=${row[$i]}"

			i=`expr $i + 1`
		done

		if [ "$VERBOSE" == "YES" ];
		then
			echo "data=${data}"
		fi;

		# main API Call
		response=`curl $curl_verb -d "$data" ${api_end_point}`

		if [ "$VERBOSE" == "YES" ];
		then
			echo "response=${response}"
		fi;

		# greping Signal power at receiver dBm for output to screen
		echo $response|egrep "Server ID|Distance to receiver km|Signal power at receiver dBm"| sed -e 's/^[ \t]*//'

		if [ "$SAVE_RESPONSE" == "YES" ];
		then
			ds=`date +"%Y%m%d%H%M%S%N"|cut -c -17`
			filename="${ds}.json"
			echo "saving response to ${filename}"
			(cd $OUTPUT_DIR && echo "$response">${filename})
		fi;
	fi;

	row_count=`expr $row_count + 1`

done < $INPUT
IFS=$OLDIFS
