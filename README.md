[![PyPI](https://img.shields.io/badge/Install%20with-PyPI-blue)](https://pypi.org/project/profile_dists/#description)
[![Bioconda](https://img.shields.io/badge/Install%20with-bioconda-green)](https://anaconda.org/bioconda/profile_splitter)
[![Conda](https://img.shields.io/conda/dn/bioconda/profile_dists?color=green)](https://anaconda.org/bioconda/profile_splitter)
[![License: Apache-2.0](https://img.shields.io/github/license/phac-nml/profile_splitter)](https://www.apache.org/licenses/LICENSE-2.0)


## Profile Dists

## Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Quick Start](#quick-start)
- [FAQ](#faq)
- [Citation](#citation)
- [Legal](#legal)
- [Contact](#contact)

## Introduction

Allele profiles produced by aggregrating the results of cg/wgMLST pipelines may require subsetting of large tables 
to perform tailored analyses. The profile splitter tool is designed to provide the functionality to process the mix
format allele profiles that profile_dists supports and convert them into integer profiles with consistent allele identifiers
between each of the different batches. This allows for subsetting the data into different partitions based on an external
file with two columns id,partition but the header naming is not important so much as the first column will be used as the
sample identifier and the second column as the column to partition the data. The second mode allows for subsetting based
on a specific column name supplied by the user, the column specified will be removed from the output profiles. Lastly,
the tool will allow the user to chunk their data based on a fixed number of samples that they want to use to partition their
large profile file into more manageable numbers of samples.

The objective of this tool is to provide atomic functionality for the incorporation into different Nextflow workflows which
may need this functionality.


## Installation

Install the latest released version from conda:

        conda create -c bioconda -c conda-forge -n profile_splitter profile_splitter

Install using pip:

        pip install profile_splitter

Install the latest master branch version directly from Github:

        pip install git+https://github.com/phac-nml/profile_splitter.git



## Usage
If you run ``profile_splitter``, you should see the following usage statement:

    usage: dist.py [-h] --query QUERY --ref REF --outdir OUTDIR [--outfmt OUTFMT]
                   [--file_type FILE_TYPE] [--distm DISTM]
                   [--missing_thresh MISSING_THRESH]
                   [--sample_qual_thresh SAMPLE_QUAL_THRESH]
                   [--match_threshold MATCH_THRESHOLD]
                   [--mapping_file MAPPING_FILE] [--force] [-s] [-V]

Supported profile formats
=====
**Native**

|  id  |  locus_1  |  locus_2  |  locus_3  |  locus_4  |  locus_5  |  locus_6  |  locus_7  | 
| ----------- | ----------- |----------- | ----------- | ----------- |----------- | ----------- | ----------- |
|  S1  |	1  |  1  |  1  |  1  |  1  |  1  |  1  | 
|  S2  |	1  |  1  |  2  |  2  |  ?  |  4  |  1  | 
|  S3  |	1  |  2  |  2  |  2  |  1  |  5  |  1  | 
|  S4  |	1  |  2  |  3  |  2  |  1  |  6  |  1  | 
|  S5  |	1  |  2  |  ?  |  2  |  1  |  8  |  1  | 
|  S6  |	2  |  3 |  3  |  -  |  ?  |  9  |  0  | 

- Direct support for missing data in the form of ?, 0, -, None or space


**chewBBACA**

|  id  |  locus_1  |  locus_2  |  locus_3  |  locus_4  |  locus_5  |  locus_6  |  locus_7  | 
| ----------- | ----------- |----------- | ----------- | ----------- |----------- | ----------- | ----------- |
|  S1  |	1  |  INF-2  |  1  |  1  |  1  |  1  |  1  | 
|  S2  |	1  |  1  |  2  |  2  |  NIPH  |  4  |  1  | 
|  S3  |	1  |  2  |  2  |  2  |  1  |  5  |  1  | 
|  S4  |	1  |  LNF  |  3  |  2  |  1  |  6  |  1  | 
|  S5  |	1  |  2  |  ASM  |  2  |  1  |  8  |  1  | 
|  S6  |	2  |  INF-8  |  3  |  PLOT3  |  PLOT5  |  9  |  NIPH  | 

- All non integer fields will be converted into missing data '0'

**Hashes**

|  id  |  locus_1  |  locus_2  |  locus_3  |  locus_4  |  locus_5  |  locus_6  |  locus_7  | 
| ----------- | ----------- |----------- | ----------- | ----------- |----------- | ----------- | ----------- |
|  S1  |	dc0a04880d1ad381ffd54ce9f6ad1e7a |  -  |  b9f94bf167f34b9fcf45d79cab0e750a  |  8a07b9cb0ab7560ad07b817ca34036bb  |  80c8156d77d724ac0bb16ec60993bc84  |  7a1d0a48f16fa25910cddfea38dab229  |  e1ee776b32c2f6131a7238ce50b75469  | 
|  S2  |	dc0a04880d1ad381ffd54ce9f6ad1e7a  |  0af06522a32865cd2db2cf5a854d195b  |  9fc502308c616ae34146d7f7b0081bd8  |  4577dec2c840472800a3b104c88bb0ef  |  -  |  bba24c25c28c08058d6f32ecfbf509e9  |  e1ee776b32c2f6131a7238ce50b75469  | 
|  S3  |	dc0a04880d1ad381ffd54ce9f6ad1e7a  |  04d45219ee5f6065caf426ba740215e5  |  9fc502308c616ae34146d7f7b0081bd8  |  4577dec2c840472800a3b104c88bb0ef  |  80c8156d77d724ac0bb16ec60993bc84  |  874225c0dec5219dd64584ba32938dbd  |  e1ee776b32c2f6131a7238ce50b75469  | 
|  S4  |	dc0a04880d1ad381ffd54ce9f6ad1e7a  |  -  |  e79562c280691c321612ecdf0dadad9e  |  4577dec2c840472800a3b104c88bb0ef  |  80c8156d77d724ac0bb16ec60993bc84  |  c8087ad8b01d9f88e8eb2c3775ef2e64  |  e1ee776b32c2f6131a7238ce50b75469  | 
|  S5  |	dc0a04880d1ad381ffd54ce9f6ad1e7a  |  04d45219ee5f6065caf426ba740215e5  |  -  |  4577dec2c840472800a3b104c88bb0ef  |  80c8156d77d724ac0bb16ec60993bc84  |  4d547ea59e90173e8385005e706aae96  | e1ee776b32c2f6131a7238ce50b75469  | 
|  S6  |	8214e9d02d1b11e6239d6a55d4acd993  |  -  |  e79562c280691c321612ecdf0dadad9e  |  -  |  -  |  e3088425be5e7de8d9a95da8e59a9ea8  |  -  | 

- Direct support for missing data in the form of ?, 0, - or space

Supported partition formats
=====

|  sample_id  | partition  | 
| ----------- | ----------- |
|  S1  |	A  | 
|  S2  |	A  | 
|  S3  |	1  | 
|  S4  |	2  |  
|  S5  |	2  |  
|  S6  |	Canada:1  |  

- do not include any special characters which are not supported in file names

Output Profile
=====
**Native**

|  id  |  locus_1  |  locus_2  |  locus_3  |  locus_4  |  locus_5  |  locus_6  |  locus_7  | 
| ----------- | ----------- |----------- | ----------- | ----------- |----------- | ----------- | ----------- |
|  S1  |	1  |  1  |  1  |  1  |  1  |  1  |  1  | 
|  S2  |	1  |  1  |  2  |  2  |  0  |  4  |  1  | 
|  S3  |	1  |  2  |  2  |  2  |  1  |  5  |  1  | 
|  S4  |	1  |  2  |  3  |  2  |  1  |  6  |  1  | 
|  S5  |	1  |  2  |  0  |  2  |  1  |  8  |  1  | 
|  S6  |	2  |  3 |  3  |  0  |  0  |  9  |  0  | 

- All columns are converted to contain only integers with missing data represented as a 0




Quick start
=====


**Outputs:**

```
{Output folder name}
├── allele_map.json - Mapping of allele hash string to integer id, can be use for reruning of analyses or masking specific alleles
├── {prefix}-{partition}.{text|parquet} - Subsetted allele profile with samples assigned to this partition
└── run.json - Contains logging information for the run including parameters the path of each output file
```

## FAQ

Coming soon

## Citation

Robertson, James, Wells, Matthew, Petka, Aaron, Bessonov, Kyryllo, Reimer, Aleisha. Profile Splitter: Convenient package for partitioning allele profiles. 2023. https://github.com/phac-nml/profile_splitter

## Legal

Copyright Government of Canada 2023

Written by: National Microbiology Laboratory, Public Health Agency of Canada

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this work except in compliance with the License. You may obtain a copy of the
License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.


## Contact

**James Robertson**: james.robertson@phac-aspc.gc.ca
