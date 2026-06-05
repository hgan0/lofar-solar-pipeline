import os
import heapq
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import ticker
from pylab import rcParams
import sunpy.map
from lofarsolar_pipeline.utils import ephemeris, diagnostics

def add_verification_rect(ax, xy, height, width, color='white', linewidth=1):
    """
    Overlays evaluation boundary frames onto tracking coordinates matrices.
    """
    rect = patches.Rectangle(xy, height, width, linewidth=linewidth, edgecolor=color, facecolor='none')
    ax.add_patch(rect)

def plot_quiet_sun_subbands(subbands, output_dir="."):
    """
    Loops systematically across execution paths to render standardized helioprojective
    solar models containing calibrated limb profiles.
    """
    os.makedirs(output_dir, exist_ok=True)
    rcParams['figure.figsize'] = 7, 6
    rcParams["grid.linestyle"] = '-'

    for sb in subbands:
        fits_file = f"/net/zernike/scratch3/hgan/processed/L2025886/t-ind-selfcal/CasA/{sb}/models/sun_model-image-pb.fits"
        if not os.path.exists(fits_file):
            continue

        data, new_header = ephemeris.get_new_helioprojective_header(fits_file)
        lofar_map = sunpy.map.Map(data, new_header)

        fig = plt.figure()
        ax = fig.add_subplot(projection=lofar_map)
        im = lofar_map.plot(axes=ax, cmap='viridis')
        lofar_map.draw_limb(axes=ax)

        cbformat = ticker.ScalarFormatter()
        cbformat.set_scientific('%.2e')
        cbformat.set_powerlimits((10, 12))
        cbformat.set_useMathText(True)

        cbar = fig.colorbar(im, location='right', format=cbformat, shrink=1.0, pad=0.02)
        cbar.set_label('Flux [Jy/beam]', fontsize=12)

        plt.tight_layout()
        save_path = os.path.join(output_dir, f"quiet_sun_image_{sb}.pdf")
        plt.savefig(save_path)
        plt.close(fig)

def generate_pipeline_comparison_matrix(fits_set_di, fits_set_dde1, fits_set_dde2, save_name="pipeline_comparison.pdf"):
    """
    Builds a unified high-resolution multi-column comparison map tracking metrics across runs.
    """
    num_rows = len(fits_set_di)
    if num_rows == 0:
        return

    rcParams['figure.figsize'] = (4. * 2 + 4. * 0.25), 3. * num_rows * 0.85
    wcs, _, _, _ = ephemeris.create_wcsheader_from_fits(fits_set_di[0])

    fig, axs = plt.subplots(num_rows, 3, subplot_kw=dict(projection=wcs, slices=('x', 'y', 0, 0)))
    plt.subplots_adjust(left=0.1, bottom=0.02, right=0.97, top=0.97, wspace=0.02, hspace=0.001)

    sig_win = 25

    for i in range(num_rows):
        sets = [fits_set_di[i], fits_set_dde1[i], fits_set_dde2[i]]
        for col_idx, fits_file in enumerate(sets):
            if not os.path.exists(fits_file):
                continue
            wcs, data, obstime, frequency = ephemeris.create_wcsheader_from_fits(fits_file)

            # Robust extraction of contrast boundaries using localized filters
            vmax = heapq.nlargest(10, data.flatten())[9]
            vmin = heapq.nsmallest(10, data.flatten())[9]

            max_coord = np.unravel_index(data.argmax(), data.shape)
            ax_obj = axs[i, col_idx] if num_rows > 1 else axs[col_idx]

            im = ax_obj.imshow(data, origin='lower', vmin=vmin, vmax=vmax, cmap='viridis')

            # Subplot Text Metadata Injectors
            ax_obj.text(0.50, 0.9, str(obstime)[-12:], ha='left', va='center', transform=ax_obj.transAxes, color='white')
            ax_obj.text(0.50, 0.83, f"{frequency.to(u.MHz).value:.3f} MHz", ha='left', va='center', transform=ax_obj.transAxes, color='white')

            mean_bkg, std_bkg = diagnostics.calculate_bkg(data[50:250, 50:250])
            mean_sig, _ = diagnostics.calculate_bkg(data[(max_coord[0]-sig_win):(max_coord[0]+sig_win), (max_coord[1]-sig_win):(max_coord[1]+sig_win)])

            # Render validation boxes directly onto tracking channels
            add_verification_rect(ax_obj, (50, 50), 200, 200)
            add_verification_rect(ax_obj, (max_coord[1]-sig_win, max_coord[0]-sig_win), sig_win*2, sig_win*2)

            ax_obj.text(0.50, 0.27, f"{mean_sig*1e-3:.1f} KJy", ha='left', va='center', transform=ax_obj.transAxes, color='white')
            ax_obj.text(0.50, 0.21, f"{std_bkg*1e-3:.1f} KJy", ha='left', va='center', transform=ax_obj.transAxes, color='white')
            ax_obj.text(0.50, 0.15, f"SNR: {mean_sig/std_bkg:.1f}", ha='left', va='center', transform=ax_obj.transAxes, color='white')

    fig.savefig(save_name, dpi=300)
    plt.close(fig)
