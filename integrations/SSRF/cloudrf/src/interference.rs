use serde::{Deserialize, Serialize};

use crate::misc::{Bounds, ColourKeyValue};


#[derive(Debug, Serialize)]
pub struct InterferenceReq {
    #[serde(flatten)]
    pub signal: Signal,
    #[serde(flatten)]
    pub jamming: Jamming,
    pub name: String,
    pub colour_key: String,
}

impl Default for InterferenceReq {
    fn default() -> Self {
        Self {
            signal: Default::default(),
            jamming: Default::default(),
            name: "QRM".to_owned(),
            colour_key: "JS.dB".to_owned(),
        }
    }
}

#[derive(Debug, Serialize)]
#[serde(untagged)]
pub enum Signal {
    Network{s_network: String},
    Sites{s_sites: Vec<String>},
    Both{s_network: String, s_sites: Vec<String>},
}

#[derive(Debug, Serialize)]
#[serde(untagged)]
pub enum Jamming {
    Network{j_network: String},
    Sites{j_sites: Vec<String>},
    Both{j_network: String, j_sites: Vec<String>},
}


impl Default for Signal {
    fn default() -> Self {
        Self::Network{ s_network: "My_Signal_Network".to_owned()}
    }
}

impl Default for Jamming {
    fn default() -> Self {
        Self::Network{ j_network: "My_Jamming_Network".to_owned()}
    }
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum InterferenceRes {
    Error {
        error: String,
    },
    Success {
        kmz: String,
        #[serde(rename = "PNG_WGS84")]
        png_wgs84: String,
        #[serde(rename = "PNG_Mercator")]
        png_mercator: String,
        bounds: Bounds,
        key: Vec<ColourKeyValue>,
        elapsed: f64,
        calculation_adjusted: Option<Vec<String>>,
    },
} 