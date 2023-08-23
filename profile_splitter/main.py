import sys
from argparse import (ArgumentParser, ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter)
import json
import os
from datetime import datetime

from profile_splitter.version import __version__
from profile_splitter.utils import process_profile, is_file_ok, filter_columns, \
    process_partitions, guess_profile_format
from profile_splitter.constants import RUN_DATA




def parse_args():
    """ Argument Parsing method.

        A function to parse the command line arguments passed at initialization of Clade-o-matic,
        format these arguments,  and return help prompts to the user shell when specified.

        Returns
        -------
        ArgumentParser object
            The arguments and their user specifications, the usage help prompts and the correct formatting
            for the incoming argument (str, int, etc.)
        """

    class CustomFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
        """
                Class to instantiate the formatter classes required for the argument parser.
                Required for the correct formatting of the default parser values

                Parameters
                ----------
                ArgumentDefaultsHelpFormatter object
                    Instatiates the default values for the ArgumentParser for display on the command line.
                RawDescriptionHelpFormatter object
                    Ensures the correct display of the default values for the ArgumentParser
                """
        pass

    parser = ArgumentParser(
        description="Profile Splitter: Tool for splitting allelic profiles into different groups based on defined partitions v. {}".format(
            __version__),
        formatter_class=CustomFormatter)
    parser.add_argument('--profile', '-i', type=str, required=True, help='Allelic profiles')
    parser.add_argument('--partition_file', '-a', type=str, required=False,
                        help='Two column membership file id,partition or json (mutually exclusive with partition_column and partition_size)')
    parser.add_argument('--partition_column', '-c', type=str, required=False,
                        help='Column internal to allelic profile for splitting (mutually exclusive with partition_file and partition_size)')
    parser.add_argument('--partition_size', '-s', type=int, required=False,
                        help='Split file into chunks of specified size (mutually exclusive with partition_file and partition_column)')
    parser.add_argument('--outdir', '-o', type=str, required=True, help='Result output files')
    parser.add_argument('--prefix', '-p', type=str, required=False, help='Prefix for result files',
                        default='partition')
    parser.add_argument('--mapping_file', '-m', type=str, required=False,
                        help='json formatted allele mapping')
    parser.add_argument('--file_type', '-e', type=str, required=False, help='Out format [text, parquet]',
                        default='text')
    parser.add_argument('--force', '-f', required=False, help='Overwrite existing directory',
                        action='store_true')

    parser.add_argument('-V', '--version', action='version', version="%(prog)s " + __version__)

    return parser.parse_args()

def write_partitions(df,bins,outdir,prefix,format):
    out_files = []
    for bin_id in bins:
        out_file = os.path.join(outdir,f'{prefix}-{bin_id}.{format}')
        out_files.append(out_file)
        if format == 'text':
            df[df.index.isin(bins[bin_id])].to_csv(out_file,sep="\t",header=True)
        else:
            df.to_parquet(out_file, compression='gzip')
    return out_files

def main():
    cmd_args = parse_args()
    profile_file = cmd_args.profile
    partition_file = cmd_args.partition_file
    partition_column = cmd_args.partition_column
    partition_size = cmd_args.partition_size
    outdir = cmd_args.outdir
    prefix = cmd_args.prefix
    file_type = cmd_args.file_type
    allele_map = cmd_args.mapping_file
    force = cmd_args.force



    run_data = RUN_DATA
    run_data['analysis_start_time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    run_data['parameters'] = vars(cmd_args)

    if profile_file is not None:
        if not is_file_ok(profile_file):
            print(f'file {profile_file} either does not exist or is too small to be valid')
            sys.exit()

    partition_options = [partition_file, partition_column, partition_size]
    if len(set(partition_options) - set([None])) != 1:
        print(f'Error you have specified invalid combinations of partition options, you need to select only as single'
              f'parameter from profile_file, partition_column, partition_size, you specified:'
              f'partition_file:{partition_file}, partition_column:{partition_column}, partition_size:{partition_size}')

    if partition_file is not None:
        if not is_file_ok(partition_file):
            print(f'file {partition_file} either does not exist or is too small to be valid')
            sys.exit()

    if not force and os.path.isdir(outdir):
        print(f'folder {outdir} already exists, please choose new directory or use --force')
        sys.exit()

    if os.path.isdir(outdir):
        print(f'folder {outdir} already exists, and force specified, cleaning up directory')
        files = [ os.path.join(outdir, 'run.json') ]
        for file in files:
            if os.path.isfile(file):
                os.remove(file)

    if not file_type in ['text', 'parquet']:
        print(f'Supplied filetype does not match [text, parquet]: {file_type} ')
        sys.exit()

    # initialize analysis directory
    if not os.path.isdir(outdir):
        os.makedirs(outdir, 0o755)

    print(f'Reading profile: {profile_file}')
    (allele_map, pdf) = process_profile(profile_file, column_mapping=allele_map,format=guess_profile_format(profile_file))


    print(f'Writting allele map')
    with open(os.path.join(outdir, "allele_map.json"), 'w') as fh:
        fh.write(json.dumps(allele_map, indent=4))

    cols = set(pdf.columns.values.tolist())

    if partition_column is not None:
        print(f'Processing partition column')
        if not partition_column in cols:
            print(f'Supplied profile {profile_file }does not contain specified splitting column {partition_column} ')
            sys.exit()

        partitions = dict(zip(pdf.index.values.tolist(), pdf[partition_column].values.tolist()))

        # remove partition column
        cols_to_remove = [partition_column]
        pdf = filter_columns(pdf, cols_to_remove)

    if partition_file is not None:
        print(f'Processing partition file')
        partitions = process_partitions(partition_file,format=guess_profile_format(partition_file))
        partition_sample_ids = set(partitions.keys())
        profile_sample_ids = set(pdf.index.values.tolist())
        if len(profile_sample_ids & partition_sample_ids) == 0:
            print(f'Errror no sample identifiers overlapped between {partition_file} and {profile_file}')
            print(f'Profile samples: {list(profile_sample_ids)}')
            print(f'Partition samples: {list(partition_sample_ids)}')
            sys.exit()

    if partition_size is not None:
        print(f'Splitting input file into bins of size {partition_size}')
        if partition_size >= len(pdf):
            p = ['1'] * len(pdf)
        else:
            labels = pdf.index.values.tolist()
            bins = []
            while labels:
                chunk, labels = labels[:partition_size], labels[partition_size:]
                bins.append(chunk)
            p = []
            for i in range(0,len(bins)):
                for id in bins[i]:
                    p.append(f'{i}')
        partitions = dict(zip(pdf.index.values.tolist(), p))

    bins = {}
    for id in partitions:
        p = partitions[id]
        if not p in bins:
            bins[p] = []
        bins[p].append(id)

    run_data['batch_memberships'] = bins
    run_data['profile_info']['num_samples'] = len( pdf)
    run_data['profile_info']['parsed_file_path'] = profile_file

    out_files = write_partitions(pdf, bins, outdir, prefix, file_type)
    run_data['result_files'] = out_files

    run_data['analysis_end_time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")



# call main function
if __name__ == '__main__':
    main()
