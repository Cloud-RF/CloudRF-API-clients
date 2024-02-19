use serde::{Deserialize, Serialize};

use crate::{
    antenna::Antenna,
    environment::Environment,
    misc::{Bounds, ColourKeyValue, Engine},
    model::Model,
    output::Output,
    receiver::Receiver,
    transmitter::Transmitter,
};

#[derive(Debug, Serialize)]
pub struct AreaReq {
    pub site: String,
    pub network: String,
    pub engine: Engine,
    pub transmitter: Transmitter,
    pub receiver: Receiver,
    pub antenna: Antenna,
    pub model: Model,
    pub environment: Environment,
    pub output: Output,
}

impl Default for AreaReq {
    fn default() -> Self {
        Self {
            site: "My_Site".to_owned(),
            network: "My_Network".to_owned(),
            engine: Engine::GPU,
            transmitter: Default::default(),
            receiver: Default::default(),
            antenna: Default::default(),
            model: Default::default(),
            environment: Default::default(),
            output: Default::default(),
        }
    }
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum AreaRes {
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
