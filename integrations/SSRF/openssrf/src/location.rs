use serde::{Deserialize, Deserializer, Serialize, Serializer};

use crate::serial::{deserialize_serial, serialize_serial, Serial};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct Location {
    pub name: String,
    #[serde(
        deserialize_with = "deserialize_serial",
        serialize_with = "serialize_serial"
    )]
    pub serial: Serial,
    pub point: Point,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct Point {
    #[serde(deserialize_with = "deserialize_lat", serialize_with = "serialize_lat")]
    pub lat: f64,
    #[serde(deserialize_with = "deserialize_lon", serialize_with = "serialize_lon")]
    pub lon: f64,
}

fn deserialize_lat<'de, D>(deserializer: D) -> Result<f64, D::Error>
where
    D: Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;

    let (dms, ns) = s.split_at(s.len() - 1);
    let (dm, s) = dms.split_at(4);
    let (d, m) = dm.split_at(2);

    let d: u64 = d.parse().unwrap();
    let m: u64 = m.parse().unwrap();
    let s: f64 = s.parse().unwrap();

    let mut lat = dms_to_decimal(d, m, s);

    if ns == "S" {
        lat *= -1.0;
    }

    Ok(lat)
}

fn serialize_lat<S>(lat: &f64, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    let (lat, ns) = if *lat < 0.0 {
        (lat.abs(), "S")
    } else {
        (*lat, "N")
    };


    let (d, m, s) = decimal_to_dms(lat);

    let s_int = s.floor() as u64;
    let s_dec = ((s - s.floor()) * 100.0) as u64;

    let str = format!("{:0>2}{:0>2}{:0>2}.{:0>2}{}", d, m, s_int, s_dec, ns);

    serializer.serialize_str(&str)
}

fn deserialize_lon<'de, D>(deserializer: D) -> Result<f64, D::Error>
where
    D: Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;

    let (dms, ew) = s.split_at(s.len() - 1);
    let (dm, s) = dms.split_at(5);
    let (d, m) = dm.split_at(3);

    let d: u64 = d.parse().unwrap();
    let m: u64 = m.parse().unwrap();
    let s: f64 = s.parse().unwrap();

    let mut lon = dms_to_decimal(d, m, s);

    if ew == "W" {
        lon *= -1.0;
    }

    Ok(lon)
}

fn serialize_lon<S>(lon: &f64, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    let (lon, ew) = if *lon < 0.0 {
        (lon.abs(), "W")
    } else {
        (*lon, "E")
    };

    let (d, m, s) = decimal_to_dms(lon);

    let s_int = s.floor() as u64;
    let s_dec = ((s - s.floor()) * 100.0) as u64;

    let str = format!("{:0>3}{:0>2}{:0>2}.{:0>2}{}", d, m, s_int, s_dec, ew);

    serializer.serialize_str(&str)
}

fn dms_to_decimal(degs: u64, mins: u64, secs: f64) -> f64 {
    degs as f64 + mins as f64 / 60.0 + secs / 3600.0
}

fn decimal_to_dms(dec: f64) -> (u64, u64, f64) {
    let degs = dec.floor();
    let mins = ((dec - degs) * 60.0).floor();
    let secs = ((dec - degs) * 60.0 - mins) * 60.0;

    (degs as u64, mins as u64, secs)
}