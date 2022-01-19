"""
This project is a prototype tool to validate the format of a csv file based on a specification provided by a json file. 

The specification is agreed format of the provided file by the supplier. This is codified in a json file passed on the command line as input. (csv Spec)
This, together with the supplied csv file are used as parameters to run the valation of said csv file. (Data File)

## Sample Usage
```
python3 validateThis.py --config=countries.json --input=countries.csv
```

## Checks
* Check if file is empty and it's allowed to be/not
* Header record in file matches expected Column Names
* csv Dialect matched expected csv Dialect
* Check if expected column(s) contain unique values
* Check data contained in a column is restritect to defined 'domain' values
* Check nulls, blanks and datatypes against expected datatype(s)

"""
import logging
import argparse
import json
import csv
import os
import sys
import math
import datetime as dt
import chardet

from validate_this_functions import csvdialect_to_dict
from validate_this_functions import compare_dialect
from validate_this_functions import compare_headers
from validate_this_functions import unique_test
from validate_this_functions import domain_test
from validate_this_functions import data_test
from validate_this_functions import count_records

THIS_SCRIPTS_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(THIS_SCRIPTS_PATH))

class MyFormatter(logging.Formatter):
    """
    Custom logger format for preferred timestamp
    """
    converter = dt.datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s


# start here! parse command line options ############################################################################################
PARSER = argparse.ArgumentParser(description='Validate data file against the provided csv specification (config)')
PARSER.add_argument('--input', action="store", dest="input_file", required=True, help='CSV Input file path and filename')
PARSER.add_argument('--config', action="store", dest="config_file", required=True, help='Config file path and filename (csv spec)')
OPTIONS = PARSER.parse_args()

# read config  ######################################################################################################################
# The config file is the csv Spec for the data file that will be 'validated'
# Must exist and must not be empty
if not os.path.exists(OPTIONS.config_file):
    print("Config file specified not found: %s", OPTIONS.config_file)
    sys.exit(8)

if os.stat(OPTIONS.config_file).st_size == 0:
    print("Config file specified is empty: %s", OPTIONS.config_file)
    sys.exit(8)

with open(OPTIONS.config_file, "r") as cf:
    config_data = json.load(cf)

# Finalise logger setup #############################################################################################################
LOGGER = logging.getLogger('')
LOGGER.setLevel(config_data["loglevel"])

ch = logging.StreamHandler()
ch.setLevel(config_data["loglevel"])
FORMATTER = MyFormatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f')
ch.setFormatter(FORMATTER)
LOGGER.addHandler(ch)

LOGGER.info("Start")
LOGGER.info("OPTIONS.input_file : %s", OPTIONS.input_file)
LOGGER.info("OPTIONS.config_file: %s", OPTIONS.config_file)


# Check data file exists ############################################################################################################
if not os.path.exists(OPTIONS.input_file):
    print("Input file specified not found: %s", OPTIONS.input_file)
    sys.exit(8)


# Is the data file empty, is file allowed to be empty? ##############################################################################
# Note a subsequent check for empty file is also performed once we know if we are expecting a Header record or not.
if os.stat(OPTIONS.input_file).st_size == 0:
    if config_data["csvspec"]["allow_empty"] == False:
        LOGGER.error("Input file specified is empty: %s", OPTIONS.input_file)
        LOGGER.error("allow_empty: %", str(config_data["csvspec"]["allow_empty"]))
        sys.exit(8)
    else:
        LOGGER.info("Input file specified is empty: %s", OPTIONS.input_file)
        LOGGER.info("allow_empty: %", str(config_data["csvspec"]["allow_empty"]))
        sys.exit(0)
else:
    LOGGER.info("Input file specified is NOT empty: %s", OPTIONS.input_file)


# sniff data file for dialect ########################################################################################################
# read half the file or the entire file if it is small
input_file_size = os.stat(OPTIONS.input_file).st_size
sniff_amount = math.floor(input_file_size / 2)
if sniff_amount < 1024:
    sniff_amount = 1024
LOGGER.info("Sniffing " + str(sniff_amount) + " bytes")

# sniff the encoding of the data file ###############################################################################################
with open(OPTIONS.input_file, 'rb') as rawdata:
    result = chardet.detect(rawdata.read(sniff_amount))
LOGGER.info(str(result))
detected_encoding = result["encoding"]

# sniff the data file to determine the csv dialect being used #######################################################################
with open(OPTIONS.input_file, encoding=config_data["csvspec"]["dialect"]["encoding"], newline='') as csvfile:
    try:
        dialect = csv.Sniffer().sniff(csvfile.read(sniff_amount))
        csvfile.seek(0)
        sniffeddialect = csvdialect_to_dict("sniffed", dialect)
    except Exception as e:
        LOGGER.error("Error sniffing file for dialect: %s", OPTIONS.input_file)
        LOGGER.error(e)
        sys.exit(8)

    try:
        has_header = csv.Sniffer().has_header(csvfile.read(sniff_amount))
        csvfile.seek(0)
        sniffeddialect["dialect"]["has_header"] = has_header
    except Exception as e:
        LOGGER.error("Error sniffing file for dialect: %s", OPTIONS.input_file)
        LOGGER.error(e)
        sys.exit(8)
sniffeddialect["dialect"]["encoding"] = detected_encoding

# Compare sniffed dialect with the config file and look for unexpected mismatches ###################################################
(returncode, report) = compare_dialect(config_data["csvspec"]["dialect"], sniffeddialect["dialect"])
if returncode != 0:
    for line in report:
        LOGGER.error(line)
    LOGGER.error("Difference detected in dialect csvspec vs sniffed")
    sys.exit(returncode)
else:
    for line in report:
        LOGGER.info(line)
    LOGGER.info("Dialect compare OK")

# If we got here proceed with using the config dialect by registering it for later use ##############################################
class csvspec(csv.Dialect):
    delimiter        = config_data["csvspec"]["dialect"]["delimeter"]
    doublequote      = config_data["csvspec"]["dialect"]["doublequote"]
    escapechar       = config_data["csvspec"]["dialect"]["escapechar"]
    lineterminator   = config_data["csvspec"]["dialect"]["lineterminator"]
    quotechar        = config_data["csvspec"]["dialect"]["quotechar"]
    quoting          = config_data["csvspec"]["dialect"]["quoting"]
    skipinitialspace = config_data["csvspec"]["dialect"]["skipinitialspace"]
    strict           = config_data["csvspec"]["dialect"]["strict"]
csv.register_dialect('csvspec', csvspec)

# Data Checks #######################################################################################################################
# Data Checks #######################################################################################################################
# Data Checks #######################################################################################################################

# Count records in file #############################################################################################################
recordcount = count_records(config_data["csvspec"], OPTIONS.input_file)

# File may contain a header only and no data records which may/may not be a valid scenario based on config ##########################
if (recordcount == 1 and config_data["csvspec"]["dialect"]["has_header"] == True and config_data["csvspec"]["allow_empty"] == False):
    LOGGER.error("An empty file has been detected where it is not allowed (Header exists)")
    sys.exit(8)

# Check headers match ################################################################################################################
# this also has the effect of checking that all the expected columns exist/no more/no less ###########################################
# if no headers are included in the file, then further data checks may fail if columns are not as expected ###########################
if config_data["csvspec"]["dialect"]["has_header"] == True:
    with open(OPTIONS.input_file, encoding=config_data["csvspec"]["dialect"]["encoding"], newline='') as csvfile:
        csv_reader = csv.reader(csvfile, dialect='csvspec')
        list_of_column_names = []
        for row in csv_reader:
            list_of_column_names = row
            break

    (returncode, report) = compare_headers(config_data["csvspec"], list_of_column_names)
    if returncode != 0:
        for line in report:
            LOGGER.error(line)
        config_data["csvspec"]["allow_empty"] == False
        sys.exit(returncode)
    else:
        for line in report:
            LOGGER.info(line)
        LOGGER.info("Headers compare OK")
else:
    LOGGER.info("Skipping header check, csvspec has_headers = " + str(config_data["csvspec"]["dialect"]["has_header"]))


# For columns with uniqueness validation, check for duplicates ######################################################################
# Note; multie column/compund keys are not currently supported ######################################################################
if config_data["csvspec"]["uniqueness"] is not None and str(config_data["csvspec"]["uniqueness"]) != "None" and str(config_data["csvspec"]["uniqueness"]) != "Null" and str(config_data["csvspec"]["uniqueness"]) != "":
    returncode, report = unique_test(config_data["csvspec"], OPTIONS.input_file)
    if returncode != 0:
        for line in report:
            LOGGER.error(line)
        LOGGER.error("Failed Unique test")
        sys.exit(returncode)
    else:
        for line in report:
            LOGGER.info(line)
        LOGGER.info("Unique test OK")

# Domain checks #####################################################################################################################
# Check specific columns contain only the allowed values ############################################################################
returncode, report = domain_test(config_data["csvspec"], OPTIONS.input_file)
if returncode != 0:
    for line in report:
        LOGGER.error(line)
    LOGGER.error("Failed Domain test")
    sys.exit(returncode)
else:
    for line in report:
        LOGGER.info(line)
    LOGGER.info("Domain test OK")

# Data checks #######################################################################################################################
# Check data against expected data type, blanks, nulls, max values ##################################################################
returncode, report = data_test(config_data["csvspec"], OPTIONS.input_file)
if returncode != 0:
    for line in report:
        LOGGER.error(line)
    LOGGER.error("Failed data_test test")
    sys.exit(returncode)
else:
    for line in report:
        LOGGER.info(line)
    LOGGER.info("data_test test OK")


# If we got this far then we assume the file to be 'validated' against the specified config #########################################
sys.exit(0)