import argparse
import sys
import logging
from lofarsolar_pipeline.core import (
    step0_preprocess, step1_calibrator, step2_model_sun,
    step3_selfcal, step4_apply, step5_imaging
)
from lofarsolar_pipeline.utils import diagnostics

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(
        description="🎯 Master Automation Engine for LOFAR Solar Flare Direction-Dependent Calibration"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available structural operations modules")

    # Master Execution Loop Parser configuration
    run_parser = subparsers.add_parser("run", help="Run full pipeline sequence steps 0 to 5 sequentially")
    run_parser.add_argument("--obsvID", required=True, help="Target Solar Observation ID")
    run_parser.add_argument("--obsvID2", required=True, help="Reference Calibrator Observation ID")
    run_parser.add_argument("--date", required=True, help="Target Date string folder path name (e.g., 21Sep2023)")
    run_parser.add_argument("--tstart", required=True, help="Processing interval start point (HH:MM:SS)")
    run_parser.add_argument("--tstop", required=True, help="Processing interval end point (HH:MM:SS)")
    run_parser.add_argument("--rounds", type=int, default=3, help="Number of DDE optimization matrix loops")

    # Performance Analytics Parser configuration
    diag_parser = subparsers.add_parser("analyze", help="Extract pipeline verification parameters")
    diag_parser.add_argument("--fits", help="FITS image target path for peak SNR calculation")
    diag_parser.add_argument("--goes", nargs=2, help="Start and End ISO times to plot matching GOES flux curves")

    args = parser.parse_args()

    if args.command == "run":
        # Static cluster properties matching your network array structural loops setup
        SB_Sun = ['SB009', 'SB029', 'SB049']
        SB_Calibrator = ['SB009', 'SB029', 'SB049']
        pointings = ['SAP000', 'SAP001']
        dir_name = "t-dep-selfcal-production-run"

        logging.info(f"⚡ Starting Full Automation Calibration Sequence for Run: {args.obsvID}")

        step0_preprocess.run_step0(args.date, args.tstart, args.tstop, args.obsvID, args.obsvID2, pointings, SB_Sun, SB_Calibrator, "CasA", dir_name)
        step1_calibrator.run_step1(args.obsvID, SB_Sun, SB_Calibrator, "CasA", "CasA", "10", dir_name)
        step2_model_sun.run_step2(args.obsvID, SB_Sun, SB_Calibrator, "CasA", "Sun", dir_name)
        step3_selfcal.run_step3(args.obsvID, SB_Sun, SB_Calibrator, "Sun", "CasA", args.rounds, dir_name)
        step4_apply.run_apply(args.date, args.obsvID, args.tstart, args.tstop, pointings, SB_Sun, SB_Calibrator, "CasA", "Sun", args.rounds, dir_name)
        step5_imaging.run_imaging(args.obsvID, SB_Sun, dir_name)

        logging.info("🏁 Full Data Calibration and Synthesis Imaging Loop Completed Successfully!")

    elif args.command == "analyze":
        if args.fits:
            diagnostics.calculate_fits_snr(args.fits)
        if args.goes:
            diagnostics.plot_goes_flux(args.goes[0], args.goes[1])
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
