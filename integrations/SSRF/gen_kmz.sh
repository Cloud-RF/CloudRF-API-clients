#!/usr/bin/sh

API_URL=https://api.cloudrf.com
cargo run -q -p openssrf_multisite_pipeline -- -k $API_KEY --url $API_URL -i ./xml -o ./kmz -ncv
