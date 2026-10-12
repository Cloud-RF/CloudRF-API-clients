Tait Communications - CloudRF API templates
===========================================

These templates were created by AI (Claude, Anthropic) on 2026-10-12 using
the CloudRF templates skill. A copy of the skill file used is in this folder
as SKILL.md.

WARNING
-------
These templates were generated automatically from OEM marketing material and
may contain errors. They have not been uploaded to, or run against, the
CloudRF API. Test each template for accuracy before using it.

Sources
-------
OEM datasheet (Tait TP9300 Specifications, Tait_SS_TP9300_v12.12, 2024):
https://www.taitcommunications.com/hubfs/01%20All%20PDFs/Specifications/DMR/Tait_SS_TP9300.pdf

CloudRF OpenAPI specification (version 3.36):
https://api.cloudrf.com/openapi.json

CloudRF developer documentation:
https://cloudrf.com/documentation/developer/

Contents
--------
36 templates in one model folder, TP9300. Files are named
{model}-{frequency}-{power}-{channel width}.json, for example
TP9300-136MHz-5W-12.5kHz.json.

The TP9300 folder covers the TP9310, TP9355 and TP9360 portables as a
series. The datasheet gives one set of transmitter and receiver figures for
all three; they differ only in features (channels, Bluetooth, encryption).

There is one template for every combination of the lower and upper
frequency of each band, the lower and upper power, and each channel width.

Portable radio (1.5 m, 5 km radius at 5 m resolution)

Band (datasheet code)   Frequencies      Powers
VHF (B1)                136 / 174 MHz    1 / 5 W
VHF (C0)                174 / 225 MHz    1 / 5 W
UHF (HK)                378 / 470 MHz    1 / 4 W
UHF (H7)                450 / 520 MHz    1 / 4 W
700/800 MHz (K5)        757 / 870 MHz    1 / 3 W

174 MHz is the edge of both VHF bands, so it has one set of templates.

What comes from the datasheet
-----------------------------
- Transmit frequency ranges and the nominal output powers for each band.
  The lowest and highest power settings are used; the 2 W, 2.5 W and 3 W
  intermediate settings have no templates.
- Receiver sensitivity, plus 10 dB as the skill specifies:
    12.5 kHz (DMR, 1% BER, -119 dBm)             -> -109 dBm
    25 kHz   (analogue, 12 dB SINAD, -120 dBm)   -> -110 dBm
  The datasheet also gives -123 dBm for DMR at 5% BER. The 1% BER figure is
  used because it matches the DMR standard figure in the skill.

Assumptions
-----------
- Channel width: the datasheet lists channel spacings of 6.25, 12.5, 15, 20,
  25 and 30 kHz. Templates use 12.5 kHz (DMR) and 25 kHz (analogue FM)
  rather than the 6.25 and 30 kHz extremes, because those are the two
  widths the datasheet gives performance figures for, and DMR occupies a
  12.5 kHz channel (6.25 kHz is its per-slot equivalent).
- 700/800 MHz: the transmit range 757-870 MHz is used. The receive range is
  narrower (757-776 MHz and 850-870 MHz).
- UHF 320-380 MHz: this band appears in the regulatory table (CE only) but
  not in the transmitter or receiver tables, so it has no templates.
- Intrinsically safe TP9361: not included; it has its own datasheet.
- Antenna: no antenna data is given, so a 2 dBi omni is assumed
  (360 degree horizontal, 120 degree vertical beamwidth, vertical
  polarisation).
- Transmitter location: Tait head office, 245 Wairakei Road, Christchurch,
  New Zealand (-43.5010, 172.5888). The address is from memory and the
  coordinates were geocoded from it with OpenStreetMap; treat as approximate.
- Noise floor: thermal noise (Johnson-Nyquist) at 21 C plus 10 dB, giving
  -123 dBm at 12.5 kHz and -120 dBm at 25 kHz.
- Radius: the free-space distance to -70 dBm with 0 dBi antennas, capped at
  5 km for a portable. The cap is the skill's "acceptable" figure used as a
  limit; without it, most templates would have a radius of tens of km.
  Eight templates fall below the cap: 520 MHz 1 W (4.6 km), 757 MHz 1 W
  (3.2 km), 870 MHz 1 W (2.7 km) and 870 MHz 3 W (4.8 km), each at both
  channel widths.
- Resolution: the smallest whole metre that keeps the calculation under
  4 million pixels for the radius (3 to 5 m).

Known issue
-----------
The templates use "ked": 2 (Bullington diffraction) as the skill specifies.
The OpenAPI 3.36 shared Model schema (used by the calculation requests)
documents this value in its description but lists only 0 and 1 in its enum,
so a strict schema validator will flag it. The template endpoints have no
enum for ked.
