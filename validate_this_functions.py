"""
This project is a prototype tool to validate the format of a csv file based on a specification provided by a json file. 

The module contains the functions to support validateThis.py only
"""
import csv
import datetime

def is_timestamp(timestamp_text, timestamp_format):
    """
      determine if passed string is a timestamp or not
    """
    try:
        datetime.datetime.strptime(timestamp_text, timestamp_format)
        return True
    except ValueError:
        return False

def is_time(time_text, time_format):
    """
      determine if passed string is a time or not
    """
    try:
        datetime.datetime.strptime(time_text, time_format)
        return True
    except ValueError:
        return False

def is_date(date_text, date_format):
    """
      determine if passed string is a date or not
    """
    try:
        datetime.datetime.strptime(date_text, date_format)
        return True
    except ValueError:
        return False

def is_float(n):
    """
      determine if passed string is a float or not
    """
    try:
        float(n)
        return True
    except ValueError:
        return False

def is_integer(n):
    """
      determine if passed string is an integer or not
    """
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


def column_test(csvspec, filename, col):
    """
    Reads the data file and test the columns against the csv Specifciation
    1. Test datatype
    2. Maximum tests
    3. Blanks and Nulls
    """
    rc = 0
    arrStrings = []

    arrStrings.append("checking " + col["name"] + " against " + col["type"])
    with open(filename, encoding = csvspec["dialect"]["encoding"]) as csvfile:
        csv_reader = csv.reader(csvfile, dialect='csvspec')
        rowcounter = 0
        datarowcounter = 0
        for row in csv_reader:
            rowcounter = rowcounter + 1
            if rowcounter == 1 and csvspec["dialect"]["has_header"] == True:
                arrStrings.append("skipping header")
                continue
            datarowcounter = datarowcounter + 1

            if col["type"] == "integer":
                if is_integer(row[int(col["colorder"])]) != True:
                    arrStrings.append("ERROR Non-Integer value found at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]))
                    rc = 8

            if col["type"] == "float":
                if is_float(row[int(col["colorder"])]) != True:
                    arrStrings.append("ERROR Non-float value found at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]))
                    rc = 8

            if col["type"] == "date":
                if is_date(row[int(col["colorder"])], col["format"]) != True:
                    arrStrings.append("ERROR Non-date value (" + str(col["format"]) + ") found at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]) + " (check strptime for formats?)")
                    rc = 8

            if col["type"] == "time":
                if is_time(row[int(col["colorder"])], col["format"]) != True:
                    arrStrings.append("ERROR Non-time value (" + str(col["format"]) + ") found at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]) + " (check strptime for formats?)")
                    rc = 8

            if col["type"] == "timestamp":
                if is_timestamp(row[int(col["colorder"])], col["format"]) != True:
                    arrStrings.append("ERROR Non-timestamp value (" + str(col["format"]) + ") found at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]) + " (check strptime for formats?)")
                    rc = 8

            ## Generic tests ###########################################################
            if col["allow_null"] != True and (row[int(col["colorder"])] is None or row[int(col["colorder"])] == col["null_value"]):
                arrStrings.append("Null value found at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]))
                rc = 8
            if col["allow_blank"] != True and (row[int(col["colorder"])] == "" or row[int(col["colorder"])] is None):
                arrStrings.append("ERROR Blank value found at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]))
                rc = 8
            if col["max_len"] is not None and len(row[int(col["colorder"])]) > col["max_len"]:
                arrStrings.append("ERROR Value longer than max len " + str(col["max_len"]) + " at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]))
                rc = 8
            if col["max_value"] is not None and row[int(col["colorder"])] > col["max_value"]:
                arrStrings.append("ERROR Value greater than max " + str(col["max_value"]) + " at row: " + str(datarowcounter) + ": " + str(row[int(col["colorder"])]))
                rc = 8
        arrStrings.append("Rows read: " + str(rowcounter) + ", Rows checked: " + str(datarowcounter))
    return rc, arrStrings


def data_test(csvspec, filename):
    """
      Test the column datatypes found in the spec against allowable data types
    """
    rc = 0
    arrStrings = []

    valid_datatypes = ["string", "integer", "float", "date", "time", "timestamp"]

    for col in csvspec["columns"]:

        if col["type"] not in valid_datatypes:
            arrStrings.append("ERROR Unsupported datatype found in csvspec: " + col["name"] + ": " + str(col["type"]))
            rc = 8
        else:
            column_test_rc, column_test_arrStrings = column_test(csvspec, filename, col)
            arrStrings = arrStrings + column_test_arrStrings
            if column_test_rc > 0:
                return column_test_rc, arrStrings

    return rc, arrStrings

def count_records(csvspec, filename):
    """
      Return number of records in the file
      No determination of header is done, if it exists, it is also included in the count
    """
    with open(filename, encoding=csvspec["dialect"]["encoding"]) as csvfile:
        csv_reader = csv.reader(csvfile, dialect='csvspec')
        rowcounter = 0
        for row in csv_reader:
            rowcounter = rowcounter + 1
    return rowcounter


def domain_test(csvspec, filename):
    """
    Compare all values in the the column against those allowed via the Domain speicfic ine the csvspec for said column
    """
    rc = 0
    arrStrings = []

    for col in csvspec["columns"]:
        if "domain" in col:
            arrStrings.append("Found column with domain constraints: " + str(col["name"]) + " colorder: " + str(col["colorder"]))
            arrStrings.append(str(col["domain"]))
            with open(filename, encoding=csvspec["dialect"]["encoding"]) as csvfile:
                csv_reader = csv.reader(csvfile, dialect='csvspec')
                rowcounter = 0
                for row in csv_reader:
                    rowcounter = rowcounter + 1
                    if rowcounter == 1 and csvspec["dialect"]["has_header"] == True:
                        arrStrings.append("skipping header")
                        continue
                    if row[int(col["colorder"])] not in col["domain"]:
                        arrStrings.append("ERROR Value found not in domain: " + str(row[int(col["colorder"])]))
                        rc = 8
    return rc, arrStrings


def unique_test(csvspec, filename):
    """
    Check the column for uniqieness.   If specified in the csv Spec, there should be no duplicates in the column

    Note, this function is dependent on columns in the file being present and in the correct order
    Previous header checks should already have been performed at least to validate that columns exist and are in the correct order
    """

    rc = 0
    arrStrings = []
    keydata = []
    keycolnumbers = []

    #get column numbers from csvspec
    for ucol in csvspec["uniqueness"]:
        found = False
        for col in csvspec["columns"]:
            if col["name"] == ucol:
                found = True
                keycolnumbers.append(col["colorder"])
        if found == False:
            print("FATAL ERROR, unique column name not found in csvspec column list")
            sys.exit(8)
    arrStrings.append("using col positions for unique test: " + str(keycolnumbers))

    with open(filename, encoding=csvspec["dialect"]["encoding"]) as csvfile:
        csv_reader = csv.reader(csvfile, dialect='csvspec')
        rowcounter = 0
        for row in csv_reader:
            rowcounter = rowcounter + 1
            if rowcounter == 1 and csvspec["dialect"]["has_header"] == True:
                arrStrings.append("skipping header")
                continue
            tempstr = ""
            for k in keycolnumbers:
                tempstr = tempstr + str(row[int(k)])
            keydata.append(tempstr)
        arrStrings.append("rows read: " + str(rowcounter))

    #check for duplicates here so we can provide some additional data back to main.
    seen = []
    rowcounter = 0
    if csvspec["dialect"]["has_header"] == True:
        rowcounter = 1

    for d in keydata:
        rowcounter = rowcounter + 1
        if d in seen:
            arrStrings.append("ERROR Duplicate found at row: " + str(rowcounter) + ": " + str(d))
            rc = 8
        else:
            seen.append(d)

    return rc, arrStrings

def compare_headers(csvspec, headers):
    """
    Compare the header record (column names) to the csv Spec
    This should also quikly identify new/missing columns, column names etc...
    """
    rc = 0
    arrStrings = []

    # lists should be the same length
    if len(csvspec["columns"]) != len(headers):
        arrStrings.append("ERROR Difference in number of columns detected in header")
        rc = 8

    maxlength = 0
    if len(csvspec["columns"]) > len(headers):
        maxlength = len(csvspec["columns"])
    else:
        maxlength = len(headers)
    if maxlength is None:
        maxlength = 0

    arrStrings.append("ColumnNo".ljust(10) + "csvspec".ljust(64) + "Sniffed ".ljust(64))
    i = 0
    #columns should be in the same order
    while i < maxlength:
        tempstr = str(i).ljust(10)
        if i < len(csvspec["columns"]) and len(csvspec["columns"]) != 0:
            tempstr = tempstr + csvspec["columns"][i]["name"].ljust(64)
        if i < len(headers) and len(headers) != 0:
            tempstr = tempstr + headers[i].ljust(64)
        arrStrings.append(tempstr)
        if i < len(csvspec["columns"]) and len(csvspec["columns"]) != 0 and i < len(headers) and len(headers) != 0:
            if csvspec["columns"][i]["name"] != headers[i]:
                arrStrings.append("ERROR Difference in column name or column order detected in header: *" + csvspec["columns"][i]["name"] + "* != *" + headers[i] + "*")
                rc = 8
        i = i + 1

    return rc, arrStrings

def compare_dialect(csvspec, sniffed):
    """
    Compares the sniffed/identified file/table level attributes to the csv Spec 'dialect' attributes
    This includes and is not limited to:
       delimiter
       quotes
       line terminator
    """
    arrStrings = []

    arrStrings.append("Attribute".ljust(17)           +                        "csvspec".ljust(13) +                       "Sniffed ".ljust(13) )
    arrStrings.append("delimeter".ljust(17)           + str(csvspec["delimeter"       ]).ljust(13) + str(sniffed["delimeter"       ]).ljust(13))
    arrStrings.append("doublequote".ljust(17)         + str(csvspec["doublequote"     ]).ljust(13) + str(sniffed["doublequote"     ]).ljust(13))
    arrStrings.append("escapechar".ljust(17)          + str(csvspec["escapechar"      ]).ljust(13) + str(sniffed["escapechar"      ]).ljust(13))
    arrStrings.append("lineterminator".ljust(17)      + str(csvspec["lineterminator"  ]).ljust(13) + str(sniffed["lineterminator"  ]).ljust(13))
    arrStrings.append("quotechar".ljust(17)           + str(csvspec["quotechar"       ]).ljust(13) + str(sniffed["quotechar"       ]).ljust(13))
    arrStrings.append("quoting".ljust(17)             + str(csvspec["quoting"         ]).ljust(13) + str(sniffed["quoting"         ]).ljust(13))
    arrStrings.append("skipinitialspace".ljust(17)    + str(csvspec["skipinitialspace"]).ljust(13) + str(sniffed["skipinitialspace"]).ljust(13))
    arrStrings.append("strict".ljust(17)              + str(csvspec["strict"          ]).ljust(13) + str(sniffed["strict"          ]).ljust(13))
    arrStrings.append("has_header".ljust(17)          + str(csvspec["has_header"      ]).ljust(13) + str(sniffed["has_header"      ]).ljust(13))
    arrStrings.append("encoding".ljust(17)            + str(csvspec["encoding"        ]).ljust(13) + str(sniffed["encoding"        ]).ljust(13))

    rc = 0
    if csvspec["delimeter"       ] !=  sniffed["delimeter"       ].strip("'"):
        arrStrings.append("ERROR Difference in dialect attribute: delimiter")
        rc = 8
    if csvspec["doublequote"     ] !=  sniffed["doublequote"     ]:
        arrStrings.append("ERROR Difference in dialect attribute: doublequote")
        rc = 8
    if str(csvspec["escapechar"      ]) !=  str(sniffed["escapechar"      ]):
        arrStrings.append("ERROR Difference in dialect attribute: escapechar")
        rc = 8
    if csvspec["lineterminator"  ] !=  sniffed["lineterminator"  ]:
        arrStrings.append("ERROR Difference in dialect attribute: lineterminator")
        rc = 8
    if csvspec["quotechar"       ] !=  sniffed["quotechar"       ]:
        arrStrings.append("ERROR Difference in dialect attribute: quotechar")
        rc = 8
    if int(csvspec["quoting"         ]) !=  int(sniffed["quoting"         ]):
        arrStrings.append("ERROR Difference in dialect attribute: quoting")
        rc = 8
    if csvspec["skipinitialspace"] !=  sniffed["skipinitialspace"]:
        arrStrings.append("ERROR Difference in dialect attribute: skipinitialspace")
        rc = 8
    if csvspec["strict"          ] !=  sniffed["strict"          ]:
        arrStrings.append("ERROR Difference in dialect attribute: strict")
        rc = 8
    if csvspec["has_header"          ] !=  sniffed["has_header"          ]:
        arrStrings.append("ERROR Difference in dialect attribute: strict")
        rc = 8
    if csvspec["encoding"          ] !=  sniffed["encoding"          ]:
        arrStrings.append("ERROR Difference in dialect attribute: encoding")
        rc = 8

    return (rc, arrStrings)

def csvdialect_to_dict(name, dialect: csv.Dialect):
    """
    Convert the json formatted csv spec to dict.
    Used for comparisons
    """

    strict = None
    try:
        strict = dialect.strict
    except AttributeError:
        pass

    dictionary = {"name": name
                  ,"dialect"          :
                   {"delimeter"       : repr(dialect.delimiter)
                   ,"doublequote"     : dialect.doublequote
                   ,"escapechar"      : repr(dialect.escapechar)
                   ,"lineterminator"  : repr(dialect.lineterminator)
                   ,"quotechar"       : dialect.quotechar
                   ,"quoting"         : repr(dialect.quoting)
                   ,"skipinitialspace": dialect.skipinitialspace
                   ,"strict"          : strict
                  }
                 }
    #json_object = json.dumps(dictionary, indent = 4)
    return dictionary
