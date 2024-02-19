use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct Transmitter {
    pub lat: f64,
    pub lon: f64,
    pub alt: f64,
    pub frq: f64,
    pub txw: f64,
    pub bwi: f64,
}

impl Default for Transmitter {
    fn default() -> Self {
        Self {
            lat: 38.916,
            lon: 1.448,
            alt: 20.0,
            frq: 800.0,
            txw: 10.0,
            bwi: 1.0,
        }
    }
}
