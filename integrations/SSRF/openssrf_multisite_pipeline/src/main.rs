use std::{
    collections::HashMap, fs::{read_dir, File}, io::BufWriter, path::{Path, PathBuf}, thread::sleep, time::{Duration, SystemTime}
};

use anyhow::anyhow;
use chrono::{DateTime, Utc};
use cloudrf::{multisite::MultisiteRes, send_multisite_req};
use openssrf::io::read_ssrf_xml;

use crate::convert::ssrf_to_multisite_req;

pub mod convert;

fn download_file(url: String, save_path: &Path, validate_certs: bool) -> anyhow::Result<u64> {
    let client = reqwest::blocking::Client::builder()
        .danger_accept_invalid_certs(!validate_certs)
        .build()?;

    let mut res = client.get(url).send()?;

    let file = File::create(save_path)?;
    let mut writer = BufWriter::new(file);

    let size = res.copy_to(&mut writer)?;

    Ok(size)
}

fn run_calculation(
    ssrf_file: &Path,
    api_key: &str,
    api_url: &str,
    validate_certs: bool,
) -> anyhow::Result<String> {
    println!("Perform calc on {:?}", ssrf_file);

    let ssrf = read_ssrf_xml(ssrf_file)?;

    let assignment_serial = ssrf.assignments[0].serial.clone();

    let req = ssrf_to_multisite_req(&ssrf, &assignment_serial)?;

    let res = send_multisite_req(&req, api_url, api_key, validate_certs)?;

    match res {
        MultisiteRes::Error { error } => Err(anyhow!(error)),
        MultisiteRes::Success { kmz, .. } => Ok(kmz.clone()),
    }
}

fn main() -> anyhow::Result<()> {
    let args = parse_args()?;

    let mut file_last_read: HashMap<PathBuf, SystemTime> = HashMap::new();

    loop {
        let mut files: Vec<_> = read_dir(&args.in_folder)?
            .filter_map(|f| match f {
                Ok(f) => Some((f.file_name().into_string().unwrap(), f)),
                Err(e) => {
                    println!("Error encountered `{}`", e);
                    None
                }
            })
            .collect();

        files.sort_by(|(name_a, _), (name_b, _)| name_a.cmp(name_b));

        for (filename, file) in files {
            let path = file.path();
            let last_changed = file.metadata()?.modified()?;
            let filename = match filename.strip_suffix(".xml") {
                Some(filename) => filename,
                None => {
                    continue;
                }
            };

            let last_changed_str = DateTime::<Utc>::from(last_changed)
                .format("%Y-%m-%d:%T")
                .to_string();

            let output_path = args
                .out_folder
                .join(format!("{}--{}.kmz", filename, last_changed_str));

            let kmz_url = match file_last_read.get(&path) {
                Some(previous_last_changed) if *previous_last_changed < last_changed => {
                    file_last_read.insert(path.clone(), last_changed);
                    sleep(Duration::from_secs_f64(0.5));
                    run_calculation(&path, &args.api_key, &args.url, args.validate_certs)
                }
                None => {
                    file_last_read.insert(path.clone(), last_changed);
                    sleep(Duration::from_secs_f64(0.5));
                    run_calculation(&path, &args.api_key, &args.url, args.validate_certs)
                }
                _ => {
                    continue;
                }
            };

            let kmz_url = match kmz_url {
                Ok(url) => url,
                Err(e) => {
                    println!("Error encountered `{}`", e);
                    continue;
                }
            };

            match download_file(kmz_url, &output_path, args.validate_certs) {
                Ok(bytes) => println!("Success, wrote KMZ with size {}", bytes),
                Err(e) => println!("Error encountered `{}`", e),
            }

            println!("")
        }
    }
}

#[derive(Debug)]
struct Args {
    api_key: String,
    url: String,
    in_folder: PathBuf,
    out_folder: PathBuf,
    validate_certs: bool,
}

fn parse_args() -> anyhow::Result<Args> {
    let mut api_key = None;
    let mut url = None;
    let mut in_folder = None;
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
                in_folder = args.get(i);
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
    let in_folder = in_folder
        .ok_or(anyhow!("Expected an input folder [-i/--in]"))?
        .clone();
    let out_folder = out_folder
        .ok_or(anyhow!("Expected an output folder [-o/--out]"))?
        .clone();

    let in_folder: PathBuf = in_folder.into();
    if !in_folder.is_dir() {
        return Err(anyhow!(format!(
            "In folder `{:?}` is not a directory",
            in_folder
        )));
    }

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
        in_folder,
        out_folder,
        validate_certs,
    })
}
