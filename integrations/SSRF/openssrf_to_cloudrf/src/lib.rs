use cloudrf::{area::AreaReq, multisite::{MultisiteReq, MultisiteTransmitter}};
use openssrf::{serial::Serial, SSRF};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum SsrfToCloudRFrr {
    #[error("Cloudrf error `{0}`")]
    CloudRfError(#[from] cloudrf::CloudRfErr),
    #[error("Openssrf error `{0}`")]
    OpenssrfError(#[from] openssrf::OpenssrfErr),
}

pub fn ssrf_to_multisite_req(
    ssrf: &SSRF,
    assignment_serial: &Serial,
) -> Result<MultisiteReq, SsrfToCloudRFrr> {
    let assignment = ssrf.get_assignment(assignment_serial)?;

    let mut req = MultisiteReq::default();
    req.output.rad = 0.0;

    req.environment.buildings = false;

    for link in &assignment.links {
        let station = assignment.get_station(&link.station_config.station_id)?;
        let config = assignment.get_config(&link.station_config.config_id)?;

        let location = ssrf.get_location(&station.station_loc.loc_sat_ref)?;

        let mut link_tx = MultisiteTransmitter::default();

        link_tx.tx.alt = station.ant_structure_height as f64;
        link_tx.tx.lat = location.point.lat;
        link_tx.tx.lon = location.point.lon;
        link_tx.tx.frq = config.config_freq.freq_min;
        link_tx.tx.bwi = config.config_emission.necessary_bw_min;
        link_tx.tx.txw = 10.0_f64.powf((config.eirp_min - 2.15) / 10.0);

        link_tx.antenna.txg = -link.station_config.feedline_loss;
        link_tx.antenna.azi = link.station_config.pointing_az_min;
        link_tx.antenna.tlt = link.station_config.pointing_elev_min;

        req.output.rad = f64::max(req.output.rad, station.station_loc.location_radius);

        req.transmitters.push(link_tx);
    }

    if let Some(assignment_title) = &assignment.title {
        req.network = assignment_title.clone();
    }

    Ok(req)
}

pub fn ssrf_to_area_req(ssrf: &SSRF, assignment_serial: &Serial, link_id: &str) -> Result<AreaReq, SsrfToCloudRFrr> {
    let assignment = ssrf.get_assignment(assignment_serial)?;

    let link = assignment.get_link(link_id)?;

    let station = assignment.get_station(&link.station_config.station_id)?;
    let config = assignment.get_config(&link.station_config.config_id)?;

    let location = ssrf.get_location(&station.station_loc.loc_sat_ref)?;

    let mut req = AreaReq::default();

    req.transmitter.alt = station.ant_structure_height as f64;
    req.transmitter.lat = location.point.lat;
    req.transmitter.lon = location.point.lon;
    req.transmitter.frq = config.config_freq.freq_min;
    req.transmitter.bwi = config.config_emission.necessary_bw_min;
    req.transmitter.txw = 10.0_f64.powf((config.eirp_min - 2.15) / 10.0);

    req.output.rad = station.station_loc.location_radius;

    req.antenna.txg = -link.station_config.feedline_loss;
    req.antenna.azi = link.station_config.pointing_az_min;
    req.antenna.tlt = link.station_config.pointing_elev_min;

    req.site = if let Some(station_name) = &station.station_name {
        station_name.clone()
    } else {
        location.name.clone()
    };

    if let Some(assignment_title) = &assignment.title {
        req.network = assignment_title.clone();
    }

    Ok(req)
}