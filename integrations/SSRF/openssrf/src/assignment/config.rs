use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct Configuration {
#[serde(rename = "ConfigID")]
pub config_id: String,
pub config_emission: ConfigEmission,
pub config_freq: ConfigFreq,
#[serde(rename = "EIRPMin")]
pub eirp_min: f64,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct ConfigFreq {
pub freq_min: f64,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct ConfigEmission {
pub necessary_bw_min: f64,
}
