use std::path::PathBuf;

use anyhow::anyhow;
use openssrf::io::{read_ssrf_xml, write_ssrf_xml};
use openssrf::SSRF;

fn main() -> anyhow::Result<()> {
    let args = parse_args()?;

    let mut merged_ssrf = SSRF {
        locations: vec![],
        assignments: vec![],
    };

    for file in args.input_files {
        let ssrf = read_ssrf_xml(&file)?;
        merged_ssrf.locations.extend(ssrf.locations);
        merged_ssrf.assignments.extend(ssrf.assignments);
    }

    write_ssrf_xml(&args.output_file, &merged_ssrf)?;

    println!("Merged SSRF xml files into: {:?}", args.output_file);

    Ok(())
}

#[derive(Debug)]
struct Args {
    input_files: Vec<PathBuf>,
    output_file: PathBuf,
}

fn parse_args() -> anyhow::Result<Args> {
    let mut input_files = vec![];
    let mut output_file = None;

    let args: Vec<String> = std::env::args().collect();

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-i" | "--input" => {
                i += 1;
                while i < args.len() && !args[i].starts_with('-') {
                    input_files.push(args[i].clone().into());
                    i += 1;
                }
                i -= 1;
            }
            "-o" | "--output" => {
                i += 1;
                output_file = args.get(i);
            }
            _ => {}
        }

        i += 1;
    }

    if input_files.is_empty() {
        return Err(anyhow!("Expected at least one input file [-i/--input]"));
    }
    let output_file = output_file
        .ok_or(anyhow!("Expected an output file [-o/--output]"))?
        .clone();

    let output_file: PathBuf = output_file.into();

    Ok(Args {
        input_files,
        output_file,
    })
}
