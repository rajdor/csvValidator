# csv Validator
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

