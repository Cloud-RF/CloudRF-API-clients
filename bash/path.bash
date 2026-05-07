#!/bin/bash
# CloudRF Area API bash demo application
# Please run with -h option for help

OUTPUT_DIR=.

template='
    {
    "site": "{{name}}",
    "network": "{{net}}",
    "transmitter": {
        "lat": {{lat}},
        "lon": {{lon}},
        "alt": {{lat}},
        "frq": {{frq}},
        "txw": {{txw}},
        "bwi": {{bwi}}
    },
    "antenna": {
        "txg": {{txg}},
        "txl": {{txl}},
        "ant": {{ant}},
        "azi": {{azi}},
        "tlt": {{tlt}},
        "pol": "{{pol}}"
    },
    "receiver": {
        "lat": {{rlat}},
        "lon": {{rlon}},
        "alt": {{ralt}},
        "rxg": {{rxg}},
        "rxs": {{rxs}}
    },
    "model": {
        "pm": {{pm}},
        "pe": {{pe}},
        "cli": {{cli}},
        "ked": {{ked}},
        "rel": {{rel}},
        "ter": {{ter}}
    },
    "environment": {
        "clm": {{clm}},
        "cll": {{cll}},
        "mat": {{mat}}
    },
    "output": {
        "units": "{{units}}",
        "col": "{{col}}",
        "out": {{out}},
        "nf": {{nf}},
        "res": {{res}},
        "rad": {{rad}}
    }
    }
    '

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
    -t)
    TEMPLATE="$2"
    shift # past argument
    shift # past value
    template=`cat $TEMPLATE`
    ;;
    -h)
    echo "area.bash API demo"
    echo "usage: area.py [-h] [-i data_file] [-o output_dir] [-r] [-v]"
    echo ""
    echo "CloudRF Area application"
    echo ""
    echo "Area coverage performs a circular sweep around a transmitter out to a user defined radius."
    echo "It factors in system parameters, antenna patterns, environmental characteristics and terrain data"
    echo "to show a heatmap in customisable colours and units."
    echo ""
    echo "This demonstration program utilizes the CloudRF Area API to display the received signal power(dBm)"
    echo "The API arguments are sourced from csv file(s)."
    echo ""
    echo "Please refer to API Reference https://api.cloudrf.com/"
    echo ""
    echo "arguments:"
    echo "  -h, --help            show this help message and exit"
    echo "  -i data_file          data input filename(csv)"
    echo "  -o output_dir         output directory where files are downloaded"
    echo "  -r                    save response content (json/html)"
    echo "  -t template           json template"
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

api_end_point=${base_url}/path

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
		data=$template

		# Building API arguments string
		i=0
                for h in "${row[@]}"
                do
                        from={{${header[$i]}}}
                        to=${row[$i]}
                        data=${data/$from/$to}

                        i=`expr $i + 1`
                done

		if [ "$VERBOSE" == "YES" ];
		then
			echo "data=${data}"
		fi;

		# main API Call
		response=`curl $curl_verb --location --request POST ${api_end_point} --data-raw "$data" --header "key: $key"`

		if [ "$VERBOSE" == "YES" ];
		then
			echo "response=${response}"
		fi;

		kmz_url_line=`echo ${response}|grep "\"kmz\": "`
                kmz_url=`echo ${kmz_url_line}|cut -f4 -d '"'`
                echo "downloading from ${kmz_url}"

                # We use a subshell to change directory
                (cd $OUTPUT_DIR && curl ${curl_verb} -O -J ${kmz_url})

		# greping Signal power at receiver dBm for output to screen
		echo $response|grep "Signal power at receiver dBm"| sed -e 's/^[ \t]*//'

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
