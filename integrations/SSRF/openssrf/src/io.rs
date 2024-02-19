use std::{fs::File, io::{BufReader, BufWriter, Read, Write}, path::Path};

use serde::Serialize;

use crate::{OpenssrfErr, SSRF};

pub fn write_ssrf_xml(path: &Path, ssrf: &SSRF) -> Result<(), OpenssrfErr> {
    let mut str = String::new();
    let mut se = quick_xml::se::Serializer::new(&mut str);
    se.indent(' ', 4);
    ssrf.serialize(se)?;


    let file = File::create(path)?;
    let mut file_writer = BufWriter::new(file);

    file_writer.write_all(str.as_bytes())?;

    Ok(())
}

pub fn read_ssrf_xml(path: &Path) -> Result<SSRF, OpenssrfErr> {
    let file = File::open(path)?;
    let mut file_reader = BufReader::new(file);

    let mut str = String::new();
    file_reader.read_to_string(&mut str)?;

    let ssrf: SSRF = quick_xml::de::from_str(&str).unwrap();

    Ok(ssrf)
}