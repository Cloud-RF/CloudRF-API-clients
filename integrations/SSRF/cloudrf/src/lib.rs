use area::{AreaReq, AreaRes};
use multisite::{MultisiteReq, MultisiteRes};
use thiserror::Error;

pub mod multisite;
pub mod area;
pub mod misc;
pub mod transmitter;
pub mod receiver;
pub mod antenna;
pub mod model;
pub mod environment;
pub mod output;

#[derive(Debug, Error)]
pub enum CloudRfErr {
    #[error("request failed with error `{0}`")]
    ReqwestError(#[from] reqwest::Error),
}


pub fn send_area_req(req: &AreaReq, api_url: &str, api_key: &str, validate_certs: bool) -> Result<AreaRes, CloudRfErr> {
    let client = reqwest::blocking::Client::builder()
        .danger_accept_invalid_certs(!validate_certs)
        .build()?;

    let res = client
        .post(format!("{}/{}", api_url, "area"))
        .header("key", api_key)
        .json(req)
        .send()?;

    let res = res.json()?;

    Ok(res)
}

pub fn send_multisite_req(req: &MultisiteReq, api_url: &str, api_key: &str, validate_certs: bool) -> Result<MultisiteRes, CloudRfErr> {
    let client = reqwest::blocking::Client::builder()
        .danger_accept_invalid_certs(!validate_certs)
        .build()?;

    let res = client
        .post(format!("{}/{}", api_url, "multisite"))
        .header("key", api_key)
        .json(req)
        .send()?;

    let res = res.json()?;

    Ok(res)
}