use std::path::{Path, PathBuf};

use anyhow::anyhow;
use cloudrf::{
    download_file, extract_calc_name_from_png_wgs84_link,
    interference::{InterferenceReq, Jamming, Signal},
    multisite::MultisiteRes,
    send_inteference_req, send_multisite_req,
};
use openssrf::io::read_ssrf_xml;
use openssrf_to_cloudrf::ssrf_to_multisite_req;

fn run_multsitite_calculations(
    ssrf_file: &Path,
    out_folder: &Path,
    api_key: &str,
    api_url: &str,
    validate_certs: bool,
) -> anyhow::Result<Vec<String>> {

    let ssrf = read_ssrf_xml(ssrf_file)?;

    let mut calc_names = Vec::new();

    for assignment in &ssrf.assignments {
        println!("Performing multisite calculation");

        let mut req = ssrf_to_multisite_req(&ssrf, &assignment.serial)?;
        req.output.col = "LTE.dBm".to_owned();

        let res = send_multisite_req(&req, api_url, api_key, validate_certs)?;

        match res {
            MultisiteRes::Error { error } => return Err(anyhow!(error)),
            MultisiteRes::Success { kmz, png_wgs84, .. } => {
                let calc_name = extract_calc_name_from_png_wgs84_link(&png_wgs84, &req.network)?;
                calc_names.push(calc_name.clone());

                let output_path = out_folder.join(format!("{}.kmz", calc_name));
                match download_file(kmz.clone(), &output_path, validate_certs) {
                    Ok(bytes) => println!("Success, wrote KMZ with size {}", bytes),
                    Err(e) => return Err(anyhow!(e)),
                }
            }
        }
    }

    Ok(calc_names)
}

fn run_interference_calculations(
    calc_names: Vec<String>,
    out_folder: &Path,
    api_key: &str,
    api_url: &str,
    validate_certs: bool,
) -> anyhow::Result<()> {

    for (idx, calc_name) in calc_names.iter().enumerate() {
        println!("Performing interference calculation");


        let other_calcs = calc_names
            .clone()
            .into_iter()
            .enumerate()
            .filter(|(i, _)| *i != idx)
            .map(|(_, name)| name)
            .collect::<Vec<_>>();

        let req = InterferenceReq {
            signal: Signal::Sites{ s_sites: vec![calc_name.clone()]},
            jamming: Jamming::Sites{ j_sites: other_calcs},
            name: calc_name.clone(),
            colour_key: "JS.dB".to_owned(),
        };

        let res = send_inteference_req(&req, api_url, api_key, validate_certs)?;

        match res {
            cloudrf::interference::InterferenceRes::Error { error } => return Err(anyhow!(error)),
            cloudrf::interference::InterferenceRes::Success { kmz, .. } => {
                let output_path = out_folder.join(format!("{}_interference.kmz", calc_name));
                match download_file(kmz.clone(), &output_path, validate_certs) {
                    Ok(bytes) => println!("Success, wrote KMZ with size {}", bytes),
                    Err(e) => return Err(anyhow!(e)),
                }
            }
        }
    }

    Ok(())
}

fn main() -> anyhow::Result<()> {
    let args = parse_args()?;

    let calc_names = run_multsitite_calculations(
        &args.ssrf_file,
        &args.out_folder,
        &args.api_key,
        &args.url,
        args.validate_certs,
    )?;

    run_interference_calculations(
        calc_names,
        &args.out_folder,
        &args.api_key,
        &args.url,
        args.validate_certs,
    )?;

    Ok(())
}

#[derive(Debug)]
struct Args {
    api_key: String,
    url: String,
    ssrf_file: PathBuf,
    out_folder: PathBuf,
    validate_certs: bool,
}

fn parse_args() -> anyhow::Result<Args> {
    let mut api_key = None;
    let mut url = None;
    let mut ssrf_file = None;
    let mut out_folder = None;
    let mut validate_certs = true;

    let args: Vec<String> = std::env::args().collect();

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-k" | "--key" => {
                i += 1;
                api_key = args.get(i);
            }
            "-u" | "--url" => {
                i += 1;
                url = args.get(i);
            }
            "-i" | "--in" => {
                i += 1;
                ssrf_file = args.get(i);
            }
            "-o" | "--out" => {
                i += 1;
                out_folder = args.get(i);
            }
            "-ncv" | "--no-certificate-validation" => {
                validate_certs = false;
            }
            _ => {}
        }

        i += 1;
    }

    let api_key = api_key
        .ok_or(anyhow!("Expected an api key [-k/--key]"))?
        .clone();
    let url = url.ok_or(anyhow!("Expected a url [-u/--url]"))?.clone();
    let ssrf_file = ssrf_file
        .ok_or(anyhow!("Expected an SSRF file [-f/--file]"))?
        .clone();
    let out_folder = out_folder
        .ok_or(anyhow!("Expected an output folder [-o/--out]"))?
        .clone();

    let ssrf_file: PathBuf = ssrf_file.into();
    let out_folder: PathBuf = out_folder.into();
    if !out_folder.is_dir() {
        return Err(anyhow!(format!(
            "Out folder `{:?}` is not a directory",
            out_folder
        )));
    }

    Ok(Args {
        api_key,
        url,
        ssrf_file,
        out_folder,
        validate_certs,
    })
}
