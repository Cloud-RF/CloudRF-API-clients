use serde::Serialize;
use serde_repr::Serialize_repr;

#[derive(Debug, Serialize)]
pub struct Model {
    pub pm: PropagationModel,
    pub pe: Propagationenvironment,
    pub ked: DiffractionModel,
    pub rel: u64,
}

impl Default for Model {
    fn default() -> Self {
        Self {
            pm: PropagationModel::EGLI,
            pe: Propagationenvironment::Average,
            ked: DiffractionModel::Bullington,
            rel: 50,
        }
    }
}

#[derive(Debug, Serialize_repr)]
#[repr(u8)]
pub enum PropagationModel {
    ITM = 1,
    EGLI = 11,
}

#[derive(Debug, Serialize_repr)]
#[repr(u8)]
pub enum Propagationenvironment {
    Conservative = 1,
    Average = 2,
    Optimistic = 3,
}

#[derive(Debug, Serialize_repr)]
#[repr(u8)]
pub enum DiffractionModel {
    LineOfSight = 0,
    SingleKnifeEdge = 1,
    Bullington = 2,
    Deygout = 4,
}
