import os
import numpy as np
from astropy.time import Time
from astropy.coordinates import EarthLocation, get_sun, AltAz, SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
import astropy.units as u
from sunpy.coordinates import frames, sun
import sunpy.map

def get_solar_coordinates_at_epoch(obsvID):
    """
    Calculates precise local tracking center offsets for solar positions
    relative to the LOFAR core array center location.
    """
    # Core reference center coordinates for the LOFAR central stations array
    lofar_location = EarthLocation(lat=52.9142, lon=6.8679, height=15)

    # Map execution time epoch dynamically
    current_time_epoch = Time.now()

    # Calculate explicit geocentric coordinates
    sun_sky_coord = get_sun(current_time_epoch)

    # Format directly to string formats expected inside source database headers
    ra_str = sun_sky_coord.ra.to_string(unit='hour', sep=':', precision=2)
    dec_str = sun_sky_coord.dec.to_string(unit='deg', sep='.', precision=2)

    return ra_str, dec_str

def create_wcsheader_from_fits(file_path):
    """
    Parses a reference FITS file image layer to return coordinate systems,
    time matrices, and operating tracking frequencies.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Target FITS path missing: {file_path}")

    with fits.open(file_path) as hdu:
        header = hdu[0].header
        # Extracting 2D visibility projection slice matrices
        data = hdu[0].data[0, 0, :, :]
        obstime = Time(header['date-obs'])
        frequency = header['crval3'] * u.Hz
        wcs = WCS(header)

    return wcs, data, obstime, frequency

def get_new_helioprojective_header(fits_file):
    """
    Transforms geocentric GCRS coordinate points directly into Helioprojective
    arcsecond grids relative to the absolute LOFAR array tracking center.
    """
    with fits.open(fits_file) as hdu:
        header = hdu[0].header
        data = hdu[0].data[0, 0, :, :]
        obstime = Time(header['date-obs'])
        frequency = header['crval3'] * u.Hz

    # Precise LOFAR core geocentric coordinates alignment
    lofar_loc = EarthLocation(lat=52.905329712 * u.deg, lon=6.867996528 * u.deg)
    lofar_gcrs = SkyCoord(lofar_loc.get_gcrs(obstime))

    reference_coord = SkyCoord(
        header['crval1'] * u.Unit(header['cunit1']),
        header['crval2'] * u.Unit(header['cunit2']),
        frame='gcrs',
        obstime=obstime,
        obsgeoloc=lofar_gcrs.cartesian,
        obsgeovel=lofar_gcrs.velocity.to_cartesian(),
        distance=lofar_gcrs.hcrs.distance
    )

    # Target translation to helioprojective reference systems
    reference_coord_arcsec = reference_coord.transform_to(frames.Helioprojective(observer=lofar_gcrs))

    cdelt1 = (np.abs(header['cdelt1']) * u.deg).to(u.arcsec)
    cdelt2 = (np.abs(header['cdelt2']) * u.deg).to(u.arcsec)
    p_angle = sun.P(obstime)

    new_header = sunpy.map.make_fitswcs_header(
        data,
        reference_coord_arcsec,
        reference_pixel=u.Quantity([header['crpix1'] - 1, header['crpix2'] - 1] * u.pixel),
        scale=u.Quantity([cdelt1, cdelt2] * u.arcsec / u.pix),
        rotation_angle=-p_angle,
        wavelength=frequency.to(u.MHz).round(2),
        observatory='LOFAR'
    )

    return data, new_header
