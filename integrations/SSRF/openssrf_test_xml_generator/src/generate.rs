use openssrf::{
    assignment::{
        config::{ConfigEmission, ConfigFreq, Configuration}, link::{Link, StationConfig}, station::{Station, StationLoc}, Assignment
    },
    location::{Location, Point},
    serial::Serial,
    SSRF,
};
use rand::{rngs::ThreadRng, seq::SliceRandom, thread_rng, Rng};
use rand_distr::Distribution;

pub fn generate_random_openssrf(sites_count: u64, lat: f64, lon: f64, std: f64) -> anyhow::Result<SSRF> {
    let mut rng = thread_rng();
   
    let name = format!("RandomSSRF-{}", sites_count);
    let short_name = format!("RND{}", sites_count);

    let configurations = build_configurations();
    let locations = generate_random_locations(&mut rng, sites_count, lat, lon, std)?;

    let mut stations = Vec::with_capacity(sites_count as usize);
    let mut links = Vec::with_capacity(sites_count as usize);

    for loc in &locations {
        let station = Station {
            station_id: loc.name.clone(),
            station_name: Some(loc.name.clone()),
            ant_structure_height: rng.gen_range(5..=15),
            station_loc: StationLoc {
                loc_sat_ref: loc.serial.clone(),
                location_radius: 15.0,
            },
        };

        let config = configurations.choose(&mut rng).unwrap();

        let link = Link {
            link_id: format!("{}-{}", station.station_id, config.config_id),
            station_config: StationConfig {
                config_id: config.config_id.clone(),
                station_id: station.station_id.clone(),
                feedline_loss: 0.0,
                pointing_az_min: rng.gen_range(0.0..360.0),
                pointing_elev_min: 0.0,
            },
        };

        stations.push(station);
        links.push(link);
    }


    let assignment = Assignment {
        title: Some(name.clone()),
        serial: Serial {
            country: "GBR".to_owned(),
            org: None,
            r#type: "AS".to_owned(),
            name: short_name.clone(),
        },
        stations,
        configurations,
        links,
    };

    Ok(SSRF {
        locations,
        assignments: vec![assignment],
    })
}

fn build_configurations() -> Vec<Configuration> {
    vec![
        Configuration {
            config_id: "A".to_owned(),
            config_emission: ConfigEmission {
                necessary_bw_min: 10.0,
            },
            config_freq: ConfigFreq { freq_min: 100.0 },
            eirp_min: 1.0,
        },
        Configuration {
            config_id: "B".to_owned(),
            config_emission: ConfigEmission {
                necessary_bw_min: 10.0,
            },
            config_freq: ConfigFreq { freq_min: 80.0 },
            eirp_min: 0.5,
        },
        Configuration {
            config_id: "C".to_owned(),
            config_emission: ConfigEmission {
                necessary_bw_min: 10.0,
            },
            config_freq: ConfigFreq { freq_min: 120.0 },
            eirp_min: 1.5,
        },
    ]
}

fn generate_random_locations(
    rng: &mut ThreadRng,
    sites_count: u64,
    lat: f64,
    lon: f64,
    std: f64
) -> anyhow::Result<Vec<Location>> {
    let mut locs = Vec::with_capacity(sites_count as usize);

    let lat_dist = rand_distr::Normal::new(lat, std)?;
    let lon_dist = rand_distr::Normal::new(lon, std)?;


    for i in 0..sites_count {
        let lat = lat_dist.sample(rng);
        let lon = lon_dist.sample(rng);

        let name = format!("RND{}", i);

        let loc = Location {
            name: name.clone(),
            serial: Serial {
                country: "GBR".to_owned(),
                org: None,
                r#type: "LO".to_owned(),
                name: name.clone(),
            },
            point: Point { lat, lon },
        };

        locs.push(loc);
    }

    Ok(locs)
}
