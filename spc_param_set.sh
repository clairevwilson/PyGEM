#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=9
#SBATCH --time=08:00:00

# Initialize conda
source ~/.bashrc
conda init bash
conda activate eb_env

# Run the Python script
cd ../research/PyGEM-EB/  
python param_set_parallel.py -n 9