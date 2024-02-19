use serde::{Deserialize, Serialize};

use crate::{
    antenna::Antenna,
    environment::Environment,
    misc::{Bounds, ColourKeyValue},
    model::Model,
    output::Output,
    receiver::Receiver,
    transmitter::Transmitter,
};

#[derive(Debug, Serialize)]
pub struct MultisiteReq {
    pub site: String,
    pub network: String,
    pub transmitters: Vec<MultisiteTransmitter>,
    pub receiver: Receiver,
    pub model: Model,
    pub environment: Environment,
    pub output: Output,
}

impl Default for MultisiteReq {
    fn default() -> Self {
        Self {
            site: "My_Multiite".to_owned(),
            network: "My_Network".to_owned(),
            transmitters: Vec::new(),
            receiver: Default::default(),
            model: Default::default(),
            environment: Default::default(),
            output: Default::default(),
        }
    }
}

#[derive(Debug, Serialize)]
pub struct MultisiteTransmitter {
    #[serde(flatten)]
    pub tx: Transmitter,
    pub nf: f64,
    pub antenna: Antenna,
}

impl Default for MultisiteTransmitter {
    fn default() -> Self {
        Self { tx: Default::default(), nf: -100.0, antenna: Default::default() }
    }
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum MultisiteRes {
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
        area: f64,
        coverage: f64,
        key: Vec<ColourKeyValue>,
        elapsed: f64,
        calculation_adjusted: Option<Vec<String>>,
    },
}
