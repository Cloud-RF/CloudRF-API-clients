use std::{fs::File, io::BufWriter, path::Path};

use area::{AreaReq, AreaRes};
use multisite::{MultisiteReq, MultisiteRes};
use regex::Regex;
use thiserror::Error;

pub mod antenna;
pub mod area;
pub mod environment;
pub mod interference;
pub mod misc;
pub mod model;
pub mod multisite;
pub mod output;
pub mod receiver;
pub mod transmitter;

#[derive(Debug, Error)]
pub enum CloudRfErr {
    #[error("request failed with error `{0}`")]
    ReqwestError(#[from] reqwest::Error),
    #[error("download failed with error `{0}`")]
    DownloadError(#[from] std::io::Error),
    #[error("failed to extract calc name from link `{0}`")]
    CalcNameError(String),
}

pub fn send_area_req(
    req: &AreaReq,
    api_url: &str,
    api_key: &str,
    validate_certs: bool,
) -> Result<AreaRes, CloudRfErr> {
    let client = reqwest::blocking::Client::builder()
        .user_agent("cloudrf-rs")
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

pub fn send_multisite_req(
    req: &MultisiteReq,
    api_url: &str,
    api_key: &str,
    validate_certs: bool,
) -> Result<MultisiteRes, CloudRfErr> {
    let client = reqwest::blocking::Client::builder()
        .user_agent("cloudrf-rs")
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

pub fn send_inteference_req(
    req: &interference::InterferenceReq,
    api_url: &str,
    api_key: &str,
    validate_certs: bool,
) -> Result<interference::InterferenceRes, CloudRfErr> {
    let client = reqwest::blocking::Client::builder()
        .user_agent("cloudrf-rs")
        .danger_accept_invalid_certs(!validate_certs)
        .build()?;

        let res = client
        .post(format!("{}/{}", api_url, "interference"))
        .header("key", api_key)
        .json(req)
        .send()?;

    let res = res.json()?;

    Ok(res)
}

pub fn download_file(
    url: String,
    save_path: &Path,
    validate_certs: bool,
) -> Result<u64, CloudRfErr> {
    let client = reqwest::blocking::Client::builder()
        .danger_accept_invalid_certs(!validate_certs)
        .build()?;

    let mut res = client.get(url).send()?;

    let file = File::create(save_path)?;
    let mut writer = BufWriter::new(file);

    let size = res.copy_to(&mut writer)?;

    Ok(size)
}

pub fn extract_calc_name_from_png_wgs84_link(
    link: &str,
    network: &str,
) -> Result<String, CloudRfErr> {
    let pattern = format!(r"([0-9]+_{}_MULTISITE)\.4326\.png", regex::escape(network));
    let re = Regex::new(&pattern).unwrap();

    re.captures(link)
        .and_then(|caps| caps.get(1).map(|m| m.as_str().to_string()))
        .ok_or(CloudRfErr::CalcNameError(link.to_owned()))
}
