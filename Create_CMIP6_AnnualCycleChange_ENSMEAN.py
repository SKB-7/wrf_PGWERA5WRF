#!/usr/bin/env python
"""
#####################################################################
# Author: Daniel Argueso <daniel>
# Date:   2021-08-25T18:41:42+02:00
# Email:  d.argueso@uib.es
# Last modified by:   daniel
# Last modified time: 2021-08-25T18:41:44+02:00
#
# @Project@
# Version: x.0 (Beta)
# Description:
#
# Dependencies:
#
# Files:
#
#####################################################################
"""


import os, argparse
import xarray as xr
import numpy as np
from glob import glob
import subprocess as subprocess
from pathlib import Path


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


#####################################################################
#####################################################################


def parse_args():
    parser = argparse.ArgumentParser(
        description="PURPOSE: Check the completeness of the CMIP6 files for PGW"
    )

    parser.add_argument(
        "-m",
        "--models",
        dest="models",
        help="Optional input list of models",
        type=str,
        nargs="?",
        default=None,
    )

    # variable(s) to process
    parser.add_argument(
        "-v",
        "--var_names",
        type=str,
        help="Variable names (e.g. ta) to process. Separate "
        + 'multiple variable names with "," (e.g. tas,ta). Default is '
        + "to process all required variables hurs,tas,ps,ts,vas,uas,psl,ta,hus,ua,va,zg.",
        default="hurs,tas,ps,ts,vas,uas,psl,ta,hus,ua,va,zg",
    )

    # input directory
    parser.add_argument(
        "-i",
        "--input_dir",
        type=str,
        help="Directory with input GCM delta files on ERA5 grid",
        default="./", #"./regrid_ERA5/",
    )

    # corrected_plevs directory
    parser.add_argument(
        "-cp",
        "--corrected_plevs_dir",
        type=str,
        help="Directory where the GCM delta files with corrected plevs should be stored.",
        default="./regrid_ERA5/corrected_plevs/",
    )

    # output directory
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        help="Directory where the GCM ENSEMBLE delta files should be stored.",
        default="./", #"./regrid_ERA5/",
    )

    args = parser.parse_args()
    return args

#####################################################################
#####################################################################

args = parse_args()
models_str = args.models

if models_str is None:
    with open("list_CMIP6.txt") as f:
        models = f.read().splitlines()
else:
    models = args.models.split(",")

variables = args.var_names.split(",")

idir = args.input_dir
# odir = args.output_dir
# print(odir)
ENSdelta_odir = f"{args.output_dir}/ENSdelta"
crctd_plvs = f"{args.corrected_plevs_dir}"

plvs = np.asarray(
    [
        100000,
        92500,
        85000,
        70000,
        60000,
        50000,
        40000,
        30000,
        25000,
        20000,
        15000,
        10000,
        7000,
        5000,
        3000,
        2000,
        1000,
        500,
        100,
    ]
)
# correct_plevs = True

def main():
    print(f"{bcolors.OKCYAN}Correcting pressure levels and making ensemble mean{bcolors.ENDC}")
    Path(crctd_plvs).mkdir(exist_ok=True, parents=True)
    print(f"Corrected plevs Directory: {crctd_plvs}")
    Path(ENSdelta_odir).resolve().mkdir(exist_ok=True, parents=True)
    print(f"Output Directory: {ENSdelta_odir}")
    
    for GCM in models:
        # if correct_plevs:
        for vn, varname in enumerate(variables):
            filepath = f"{idir}/{varname}_{GCM}_delta.nc"
            filename = filepath.split("/")[-1]
            # print(filename)
            fin = xr.open_dataset(filepath)
            if varname in ["ta", "hus", "ua", "va", "zg"]:
                fin.coords["plev"] = plvs
                fin.to_netcdf(f"{crctd_plvs}/{filename.split('_delta')[0]}_crctd_plvs_delta.nc")
            else:
                if "height" in fin.coords:
                    fin = fin.drop("height")
                fin = fin[varname]
                # import pdb; pdb.set_trace()  # fmt: skip
                fin.to_netcdf(f"{crctd_plvs}/{filename.split('_delta')[0]}_crctd_plvs_delta.nc")

            ens_file = ENSdelta_odir + "/" + f"{varname}_CC_signal_ssp585_2099-2070_1985-2014.nc"
            print(ens_file)
            crctd_plvs_file = f"{crctd_plvs}/{varname}_{GCM}_crctd_plvs_delta.nc"
            # print('crctd_plvs_file:', crctd_plvs_file)

            if not os.path.isfile(ens_file):
                try:
                    cdo_command = (f"cdo ensmean {crctd_plvs_file} {ens_file}")
                    print(f"Command: {cdo_command}")
                    subprocess.check_output(cdo_command, shell=True)
                    print(f"{bcolors.OKGREEN}Ensemble mean of GCMs{bcolors.ENDC}")
                except Exception:
                    raise SystemExit(
                        f"{bcolors.ERROR}ERROR: Could not make the ensemble mean{bcolors.ENDC}"
                    )

    # for varname in variables:
    #     print(varname)
    #     # import pdb; pdb.set_trace()  # fmt: skip
    #     ens_file = f"{ENSdelta_odir}/{varname}_CC_signal_ssp585_2099-2070_1985-2014.nc"
    #     if not os.path.isfile(ens_file):
    #         try:
    #             subprocess.check_output(
    #                 f"cdo ensmean {crctd_plvs}/{varname}_* {ens_file}",
    #                 shell=True,
    #             )
    #             print(f"{bcolors.OKGREEN}Ensemble mean of GCMs{bcolors.ENDC}")
    #         except Exception:
    #             raise SystemExit(
    #                 f"{bcolors.ERROR}ERROR: Could not make the ensemble mean{bcolors.ENDC}"
    #             )
        # filesin = sorted(glob(f"{args.corrected_plevs_dir}/{varname}_*"))
        # print(filesin)

        # fin = xr.open_mfdataset(filesin, concat_dim="model", combine="nested")
        # fin_ensmean = fin.mean(dim="model").squeeze()
        # fin_ensmean.to_netcdf(f"{varname}_CC_signal_ssp585_2070-2099_1985-2014.nc")


###############################################################################
# __main__  scope
###############################################################################

if __name__ == "__main__":
    main()

###############################################################################
