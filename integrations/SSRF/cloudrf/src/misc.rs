use serde::Deserialize;
use serde_repr::Serialize_repr;
use serde_tuple::Deserialize_tuple;

#[derive(Debug, Serialize_repr)]
#[repr(u8)]
pub enum Engine {
    CPU = 2,
    GPU = 1,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Deserialize)]
pub struct ColourKeyValue {
    l: String,
    r: u8,
    g: u8,
    b: u8,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Copy, Deserialize_tuple)]
pub struct Bounds {
    north: f64,
    east: f64,
    south: f64,
    west: f64,
}
