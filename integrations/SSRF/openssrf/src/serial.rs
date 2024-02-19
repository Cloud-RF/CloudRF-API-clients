use serde::{Deserialize, Deserializer, Serializer};

#[derive(Debug, PartialEq, Eq, Clone)]
pub struct Serial {
    pub country: String,
    pub org: Option<String>,
    pub r#type: String,
    pub name: String,
}

impl std::fmt::Display for Serial {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}:{}:{}:{}",
            self.country,
            match &self.org {
                Some(org) => org,
                None => "",
            },
            self.r#type,
            self.name
        )
    }
}

pub(crate) fn deserialize_serial<'de, D>(deserializer: D) -> Result<Serial, D::Error>
where
    D: Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;
    let mut it = s.split(':');

    let country = it.next().unwrap_or("ERR_EXPECTED_COUNTRY").to_owned();
    let org = match it.next() {
        Some(org) if !org.is_empty() => Some(org.to_owned()),
        _ => None,
    };
    let r#type = it.next().unwrap_or("ERR_EXPECTED_TYPE").to_owned();
    let name = it.next().unwrap_or("ERR_EXPECTED_NAME").to_owned();

    Ok(Serial {
        country,
        org,
        r#type,
        name,
    })
}

pub(crate) fn serialize_serial<S>(serial: &Serial, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    let str = format!("{}", serial);

    serializer.serialize_str(&str)
}
