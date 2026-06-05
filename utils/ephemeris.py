import numpy as np
from astropy.time import Time
from astropy.coordinates import EarthLocation, get_sun, AltAz

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
