use assignment::Assignment;
use location::Location;
use serde::{Deserialize, Serialize};
use serial::Serial;
use thiserror::Error;

pub mod serial;
pub mod location;
pub mod assignment;
pub mod io;

// A subset of OpenSSRF that can meaningfully be translated to a CloudRF API request

// Some liberties have been taken 
// - required fields/attributes such as "cls" have been ignored
// - certain optional fields are expected

// The libraries serde and quick-xml allow the schema to be parsed
// from this declarative structure, rather than writing a custom parser

#[derive(Debug, Error)]
pub enum OpenssrfErr {
    #[error("an assignment with serial `{serial}` could not be found")]
    AssignmentNotFound {serial: Serial},
    #[error("a location with serial `{serial}` could not be found")]
    LocationNotFound {serial: Serial},
    #[error("a link with id `{link}` could not be found in the assignment with serial `{assignment}`")]
    LinkNotFound { link: String, assignment: Serial },
    #[error("a station with id `{station}` could not be found in the assignment with serial `{assignment}`")]
    StationNotFound { station: String, assignment: Serial },
    #[error("a config with id `{config}` could not be found in the assignment with serial `{assignment}`")]
    ConfigNotFound { config: String, assignment: Serial },
    #[error("io error")]
    IOError(#[from] std::io::Error),
    #[error("deserialize error")]
    DeserializeError(#[from] quick_xml::DeError),
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct SSRF {
    #[serde(rename = "Location")]
    pub locations: Vec<Location>,
    #[serde(rename = "Assignment")]
    pub assignments: Vec<Assignment>,
}

impl SSRF {
    pub fn get_assignment(&self, serial: &Serial) -> Result<&Assignment, OpenssrfErr> {
        match self.assignments.iter().find(|a| a.serial == *serial) {
            Some(a) => Ok(a),
            None => Err(OpenssrfErr::AssignmentNotFound { serial: serial.clone() }),
        }
    }

    pub fn get_location(&self, serial: &Serial) -> Result<&Location, OpenssrfErr> {
        match self.locations.iter().find(|&l| l.serial == *serial) {
            Some(l) => Ok(l),
            None => Err(OpenssrfErr::LocationNotFound { serial: serial.clone() }),
        }
    }
}
