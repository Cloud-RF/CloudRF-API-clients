use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct Output {
    pub units: Units,
    pub col: String,
    pub out: u64,
    pub nf: f64,
    pub res: f64,
    pub rad: f64,
}

impl Default for Output {
    fn default() -> Self {
        Self {
            units: Units::MetersAGL,
            col: "LTE.dBm".to_owned(),
            out: 2,
            nf: -100.0,
            res: 4.0,
            rad: 2.0,
        }
    }
}

#[derive(Debug, Serialize)]
pub enum Units {
    #[serde(rename(serialize = "m"))]
    MetersAGL,
    #[serde(rename(serialize = "m_amsl"))]
    MetersASL,
    #[serde(rename(serialize = "f"))]
    FeetAGL,
    #[serde(rename(serialize = "f_amsl"))]
    FeetASL,
}
