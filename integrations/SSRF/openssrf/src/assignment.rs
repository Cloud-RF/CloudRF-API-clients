use serde::{Deserialize, Serialize};

use crate::{serial::{deserialize_serial, serialize_serial, Serial}, OpenssrfErr};

use self::{config::Configuration, link::Link, station::Station};

pub mod config;
pub mod station;
pub mod link;

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct Assignment {
    pub title: Option<String>,
    #[serde(deserialize_with = "deserialize_serial", serialize_with = "serialize_serial")]
    pub serial: Serial,
    #[serde(rename = "Station")]
    pub stations: Vec<Station>,
    #[serde(rename = "Configuration")]
    pub configurations: Vec<Configuration>,
    #[serde(rename = "Link")]
    pub links: Vec<Link>,
}

impl Assignment {
    pub fn get_link(&self, id: &str) -> Result<&Link, OpenssrfErr> {
        match self.links.iter().find(|&l| l.link_id == *id) {
            Some(l) => Ok(l),
            None => Err(OpenssrfErr::LinkNotFound {
                link: id.to_owned(),
                assignment: self.serial.clone(),
            }),
        }
    }

    pub fn get_station(&self, id: &str) -> Result<&Station, OpenssrfErr> {
        match self.stations.iter().find(|&s| s.station_id == *id) {
            Some(s) => Ok(s),
            None => Err(OpenssrfErr::StationNotFound {
                station: id.to_owned(),
                assignment: self.serial.clone(),
            }),
        }
    }

    pub fn get_config(&self, id: &str) -> Result<&Configuration, OpenssrfErr> {
        match self.configurations.iter().find(|&c| c.config_id == *id) {
            Some(c) => Ok(c),
            None => Err(OpenssrfErr::ConfigNotFound {
                config: id.to_owned(),
                assignment: self.serial.clone(),
            }),
        }
    }
}
