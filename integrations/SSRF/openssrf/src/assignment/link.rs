use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct Link {
#[serde(rename = "LinkID")]
pub link_id: String,
pub station_config: StationConfig,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct StationConfig {
#[serde(rename = "ConfigID")]
pub config_id: String,
#[serde(rename = "StationID")]
pub station_id: String,
pub feedline_loss: f64,
pub pointing_az_min: f64,
pub pointing_elev_min: f64,
}
