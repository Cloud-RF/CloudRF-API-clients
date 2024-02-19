use serde::{Deserialize, Serialize};

use crate::serial::{deserialize_serial, serialize_serial, Serial};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct Station {
#[serde(rename = "StationID")]
pub station_id: String,
pub station_name: Option<String>,
pub ant_structure_height: i32,
pub station_loc: StationLoc,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct StationLoc {
#[serde(deserialize_with = "deserialize_serial", serialize_with = "serialize_serial")]
pub loc_sat_ref: Serial,
pub location_radius: f64,
}
