use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct Receiver {
    pub lat: f64,
    pub lon: f64,
    pub alt: f64,
    pub rxg: f64,
    pub rxs: f64,
}

impl Default for Receiver {
    fn default() -> Self {
        Self {
            lat: 0.0,
            lon: 0.0,
            alt: 2.0,
            rxg: 1.0,
            rxs: -110.0,
        }
    }
}
