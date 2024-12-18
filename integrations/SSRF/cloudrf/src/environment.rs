use serde::{Serialize, Serializer};
use serde_repr::Serialize_repr;

#[derive(Debug, Serialize)]
pub struct Environment {
    pub clt: String,
    pub elevation: Elevation,
    #[serde(serialize_with = "serialize_bool")]
    pub landcover: bool,
    #[serde(serialize_with = "serialize_bool")]
    pub buildings: bool,
    #[serde(serialize_with = "serialize_bool")]
    pub obstacles: bool,
}

fn serialize_bool<S>(b: &bool, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    let i = if *b { 1 } else { 0 };

    serializer.serialize_u8(i)
}

impl Default for Environment {
    fn default() -> Self {
        Self {
            clt: "Temperate.clt".to_owned(),
            elevation: Elevation::Surface,
            landcover: false,
            buildings: false,
            obstacles: false,
        }
    }
}

#[derive(Debug, Serialize_repr)]
#[repr(u8)]
pub enum Elevation {
    Surface = 1,
    Terrain = 2,
}
