Motorola Solutions - CloudRF API templates
==========================================

These templates were created by AI (Claude, Anthropic) on 2026-10-11 using
the CloudRF templates skill. A copy of the skill file used is in this folder
as SKILL.md.

WARNING
-------
These templates were generated automatically from OEM marketing material and
may contain errors. They have not been uploaded to, or run against, the
CloudRF API. Test each template for accuracy before using it.

Sources
-------
OEM brochure (MOTOTRBO At A Glance), used for every folder except DM4000e:
https://www.motorolasolutions.com/content/dam/msi/docs/EA_Collaterals/ENGLISH/MOTOTRBO/General/mototrbo_brochure_eng.pdf

OEM datasheet (MOTOTRBO DM4000e Series, EMEA), used for the DM4000e folder:
https://www.motorolasolutions.com/content/dam/msi/docs/EA_Collaterals/ENGLISH/MOTOTRBO/Mobiles/dm4000e-series-datasheet-emea-eng.pdf

CloudRF OpenAPI specification (version 3.36):
https://api.cloudrf.com/openapi.json

CloudRF developer documentation:
https://cloudrf.com/documentation/developer/

Contents
--------
144 templates in 25 model folders. Files are named
{model}-{frequency}-{power}-{channel width}.json, for example
DP4401e-403MHz-4W-12.5kHz.json.

Each folder has one template for every combination of the lower and upper
frequency of each band and each power listed below.

Portable radios (1.5 m, 5 km radius at 5 m resolution)

Folder     VHF 136-174   300-400 MHz   UHF            UHF power
DP1400     5 W           -             403-470 MHz    4 W
DP2400e    5 W           4 W           403-527 MHz    4 W
DP2600e    5 W           -             403-527 MHz    4 W
DP3441e    5 W           -             403-527 MHz    4 W
DP3661e    5 W           -             403-527 MHz    4 W
DP4400e    5 W           -             403-527 MHz    4 W
DP4401e    5 W           4 W           403-527 MHz    4 W
DP4600e    5 W           -             403-527 MHz    4 W
DP4601e    5 W           -             403-527 MHz    4 W
DP4800e    5 W           -             403-527 MHz    4 W
DP4801e    5 W           4 W           403-527 MHz    4 W
DP4401Ex   1 W           -             403-470 MHz    1 W
DP4801Ex   1 W           -             403-470 MHz    1 W
Ion        -             -             400-527 MHz    4 W
SL1600     3 W           -             403-470 MHz    3 W
SL2600     3 W           -             403-470 MHz    3 W
R2         5 W           -             400-480 MHz    4 W
R7a        5 W           -             400-527 MHz    4 W
R7         5 W           -             400-527 MHz    4 W

Vehicle mobile radios (1.5 m, 10 km radius at 10 m resolution)

Folder     VHF 136-174   UHF 403-470
DM1400     25 / 45 W     25 / 40 W
DM1600     25 / 45 W     25 / 40 W
DM2600     25 / 45 W     25 / 40 W
DM4000e    see "DM4000e folder" below

Repeaters (8 m mast, 20 km radius at 20 m resolution)

Folder     VHF 136-174   UHF 403-470
SLR5500    50 W          50 W
SLR8000    100 W         100 W

Brochure-based folders: what comes from the brochure
----------------------------------------------------
- Bands and maximum power per model, from the portable and mobile comparison
  tables and their footnotes.
- 300 MHz versions exist only for the DP2400e, DP4401e and DP4801e (and the
  DM4401e / DM4601e, which are covered by the DM4000e folder).
- Repeater output power: 50 W (SLR 5500) and up to 100 W (SLR 8000).

Brochure-based folders: assumptions made where the brochure is silent
---------------------------------------------------------------------
- Repeater frequencies: the brochure gives no frequency range for the
  SLR 5500 or SLR 8000. VHF 136-174 MHz and UHF 403-470 MHz are assumed.
  Check these against the repeater datasheets.
- Low power: the brochure gives only the maximum power for portables, so
  there is no low-power template. For mobiles, "25 W or 45 W" is treated as
  the lower and upper power.
- Channel width: not stated, so the 12.5 kHz DMR channel is used. There are
  no 25 kHz analogue templates.
- Receiver sensitivity: not stated, so the DMR standard figure in the skill
  (-119 dBm) plus 10 dB is used, giving -109 dBm.
- SL1600 / SL2600: the 3 W digital rating is used, not the 2 W analogue one.
- R7: one folder covers both the no-keypad and full-keypad versions.
- The SLR 1000 repeater is not included because the brochure gives no power
  or frequency for it.

DM4000e folder (from the datasheet, not the brochure)
-----------------------------------------------------
32 templates covering the DM4400e, DM4401e, DM4600e and DM4601e as a series.
It was built from the more detailed datasheet, so it differs from the
brochure-based folders:

Band      Frequencies      Powers
VHF       136 / 174 MHz    1 / 45 W
300 MHz   300 / 400 MHz    1 / 40 W
UHF1      403 / 470 MHz    1 / 45 W
UHF2      450 / 527 MHz    1 / 40 W

- Both 12.5 kHz and 25 kHz channels are included.
- Receiver sensitivity is the datasheet figure plus 10 dB:
    12.5 kHz (DMR digital, 0.16 uV = -123 dBm)   -> -113 dBm
    25 kHz   (analogue,    0.18 uV = -122 dBm)   -> -112 dBm
- The 1 W templates from 300 MHz upwards have a radius below 10 km (down to
  4.5 km at 527 MHz), set by the free-space distance.

Assumptions common to all folders
---------------------------------
- Antenna: no antenna data is given, so a 2 dBi omni is assumed
  (360 degree horizontal, 120 degree vertical beamwidth, vertical polarisation).
- Transmitter location: Motorola Solutions head office, Chicago
  (41.8803, -87.6400). This is approximate and was not looked up.
- 300 MHz band: the two sub-bands (300-360 and 350-400 MHz) are treated as a
  single 300-400 MHz band.
- Noise floor: thermal noise (Johnson-Nyquist) at 21 C plus 10 dB, giving
  -123 dBm at 12.5 kHz and -120 dBm at 25 kHz.
- Radius: the free-space distance to -70 dBm with 0 dBi antennas (increased
  by 50% for masts), capped at 5 km for portables, 10 km for mobiles and
  20 km for masts. The caps are the skill's "acceptable" figures used as
  limits; without them, most templates would have a radius of tens of km.
- Resolution: the smallest value that keeps the calculation under 4 million
  pixels for the radius.

Known issue
-----------
The templates use "ked": 2 (Bullington diffraction) as the skill specifies.
The OpenAPI 3.36 schema documents this value in its description but lists
only 0 and 1 in its enum, so a strict schema validator will flag it.
