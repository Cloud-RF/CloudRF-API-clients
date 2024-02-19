use std::path::PathBuf;

use anyhow::anyhow;
use openssrf::io::write_ssrf_xml;

use crate::generate::generate_random_openssrf;

pub mod generate;

fn main() -> anyhow::Result<()> {
    let args = parse_args()?;

    let mut i = 1;
    while i <= args.max_sites {
        let ssrf = generate_random_openssrf(i, args.lat, args.lon, args.std)?;
        let filename = format!("rnd-ssrf-{:0>3}.xml", i);

        let file = args.out_folder.join(filename);

        write_ssrf_xml(&file, &ssrf)?;

        println!("Wrote OpenSSRF xml file: {:?}", file);

        i *= 2;
    }

    Ok(())
}

#[derive(Debug)]
struct Args {
    out_folder: PathBuf,
    max_sites: u64,
    lat: f64,
    lon: f64,
    std: f64
}

fn parse_args() -> anyhow::Result<Args> {
    let mut out_folder = None;
    let mut max_sites = None;
    let mut lat = None;
    let mut lon = None;
    let mut std = None;

    let args: Vec<String> = std::env::args().collect();

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-o" | "--out" => {
                i += 1;
                out_folder = args.get(i);
            }
            "-m" | "--max" => {
                i += 1;
                max_sites = args.get(i);
            }
            "--lat" => {
                i += 1;
                lat = args.get(i);
            }
            "--lon" => {
                i += 1;
                lon = args.get(i);
            }
            "-s" | "--std" => {
                i += 1;
                std = args.get(i);
            }
            _ => {}
        }

        i += 1;
    }

    let out_folder = out_folder
        .ok_or(anyhow!("Expected an output folder [-o/--out]"))?
        .clone();
    let max_sites = max_sites.ok_or(anyhow!("Expected max sites [-m/--max]"))?;
    let lat = lat.ok_or(anyhow!("Expected a latitude [--lat]"))?;
    let lon = lon.ok_or(anyhow!("Expected a longitude [--lon]"))?;
    let std = std.ok_or(anyhow!("Expected an STD [-s/--std]"))?;

    let max_sites: u64 = max_sites.parse()?;
    let lat: f64 = lat.parse()?;
    let lon: f64 = lon.parse()?;
    let std: f64 = std.parse()?;

    let out_folder: PathBuf = out_folder.into();
    if !out_folder.is_dir() {
        return Err(anyhow!(format!(
            "Out folder `{:?}` is not a directory",
            out_folder
        )));
    }

    Ok(Args {
        out_folder,
        max_sites,
        lat,
        lon,
        std
    })
}
