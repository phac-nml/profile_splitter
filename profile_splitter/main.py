import sys
from argparse import (ArgumentParser, ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter)
import json
import os
from datetime import datetime

from profile_splitter.version import __version__
from profile_splitter.utils import read_data
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
    parser.add_argument('--file_type', '-e', type=str, required=False, help='Out format [text, parquet]',
                        default='text')
    parser.add_argument('--force', '-f', required=False, help='Overwrite existing directory',
                        action='store_true')

    parser.add_argument('-V', '--version', action='version', version="%(prog)s " + __version__)

    return parser.parse_args()

def write_partitions(df,bins,outdir,format):
    out_files = []
    for bin_id in bins:
        out_file = os.path.join(outdir,f'{bin_id}.{format}')
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
    file_type = cmd_args.file_type
    force = cmd_args.force

    if not file_type in ['text', 'parquet']:
        print(f'Supplied filetype does not match [text, parquet]: {file_type} ')
        sys.exit()




    run_data = RUN_DATA
    run_data['analysis_start_time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    run_data['parameters'] = vars(cmd_args)

    if not force and os.path.isdir(outdir):
        print(f'folder {outdir} already exists, please choose new directory or use --force')
        sys.exit()

    if os.path.isdir(outdir):
        print(f'folder {outdir} already exists, and force specified, cleaning up directory')
        files = [ os.path.join(outdir, 'run.json') ]
        for file in files:
            if os.path.isfile(file):
                os.remove(file)


    # initialize analysis directory
    if not os.path.isdir(outdir):
        os.makedirs(outdir, 0o755)

    print(f'Reading profile: {profile_file}')
    profile = read_data(profile_file)

    if profile.status == False:
        print(
            f'{profile.messages}')
        sys.exit()
    profile_columns = profile_df.columns.to_list()

    if partition_file is not None:
        partition = read_data(partition_file)
        if partition.status == False:
            print(
                f'{partition.messages}')
            sys.exit()
        partitions = dict(zip(partition.df['sample_id'].values.tolist(), partition.df['partition'].values.tolist()))
    elif partition_column is not None:
        if not partition_column in profile_columns:
            print(
                f'Error you have specified invalid partition_column:{partition_column}, it is not found in {profile_file}')
            sys.exit()
        partitions = dict(zip(profile.df[partition_column].values.tolist(), p))

    elif partition_size is not None:
        if partition_size >= len(profile.df):
            partition_size = len(profile.df)

        labels = profile.df.index.values.tolist()
        bins = []
        while labels:
            chunk, labels = labels[:partition_size], labels[partition_size:]
            bins.append(chunk)
        p = []
        for i in range(0, len(bins)):
            p+= [f'{i}'] * len(bins[i])
        partitions = dict(zip(profile.df.index.values.tolist(), p))
    else:
        print(f'Error you have specified invalid combinations of partition options, you need to select only as single'
              f'parameter from profile_file, partition_column, partition_size, you specified:'
              f'partition_file:{partition_file}, partition_column:{partition_column}, partition_size:{partition_size}')

    groups = {}
    for sample_id in partitions:
        group_id = partitions[sample_id]
        if not group_id in groups:
            groups[group_id] = []
        groups[group_id].append(sample_id)



    run_data['profile_info']['num_samples'] = len(profile.df)
    run_data['profile_info']['parsed_file_path'] = profile_file

    out_files = write_partitions(profile.df, groups, outdir, file_type)
    run_data['result_files'] = out_files

    run_data['analysis_end_time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    with open(os.path.join(outdir,"run.json"),'w' ) as fh:
        fh.write(json.dumps(run_data, indent=4))


# call main function
if __name__ == '__main__':
    main()
