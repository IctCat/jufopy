# JuFo.py
Julkaisu Foorumi Python (jufo.py) script for automated academic publication ranking search

# About
`jufo.py` Python script was created to aid with the process of doing academic research.
The [Finnish publication forum](https://www.tsv.fi/julkaisufoorumi/haku.php?lang=en) lacked the ability to search for multiple papers at once
because there is no API or any similar solution available.
That is why this script was created to parse the website automatically in order to ease the repetetion of academic research.
The CSV files used with this program are created with [Zotero](https://github.com/zotero/zotero).
You can use your own custom CSV files as long as you give the necessary column names in command line arguments.

# Disclaimers
Http request delay exists for a reason in the source code.
You shouldn't launch too many requests at once because that can be seen as an unintended denial of service attack.
Also don't modify this tool for other purposes if you don't know what you are doing.
The html parser can be [exploited](https://docs.python.org/3/library/xml.html#xml-vulnerabilities) against your machine when used on untrusted grounds.

*TSV level is synonym for JUFO level* 
A null TSV means a paper which is found but doesn't have a set TSV level.
A None TSV means a paper whish is not found.
Values in `Conference Name` column should contain the conference abbreviation inside parentheses.


# Python virtual environment creation
Makes Python package management more modular.
It's recommended to avoid installing packages globally if it's not needed.
Doing so also helps to avoid version conflicts.

## Installation
```bash
sudo apt-get install python3-venv
```
*Note that you also need to install Python3 if your operating system doesn't come bundled with it.*

### Alternative for Python2:
```python
pip install virtualenv
```
Disclaimer: Jufo.py is not tested for Python2! It's quite probable that it doesn't work out-of-the-box.

## Create new virtual environment
```bash
python3 -m venv <file path>
```

### Activation in bash
```bash
source <venv>/bin/activate
```
Replace <venv> with the file path created above. (<file path>).

#### Source
https://docs.python.org/3/library/venv.html
See the site for instructions with other shells than bash.

#### Full example
```bash
python3 -m venv /home/myuser/Environments/Python/myenv/
source ~/Environments/Python/myenv/bin/activate
```


### Extra tips
If you don't always want to run a specific Python script with the `python` command then consider adding a shebang to the beginning of the script:
```python
#!<venv>/bin/python3
```
Example:
```python
#!/home/myuser/Environments/Python/myenv/bin/python3
```

That should do it! Now you can install packages with pip into your virtual Python environment.
You can recognize an active Python environment by the virtual environment name wrapped inside parentheses on the left side of your terminal.

#### This script is not yet tested on Windows environments. Consider contributing if you are running this script on Windows.


# Using Jufo.py
## Installation 
```bash
pip install beautifulsoup4 && \
pip install lxml && \ 
pip install requests
```

## Running examples
without shebang:
```bash
python jufo.py -a
```

with shebang:
```bash
./jufo.py -a
```


Basic search for papers. Shows progress bar, ignores publication title comparison and automatrically finds the .csv file.
```bash
./jufo.py -p -f -a
```

Advanced search. Starts from the 10th paper and processes only 5 papers using a http request delay of 7 seconds. Also shows debug information and requires both ISSN and publication title from those papers.
```bash
./jufo.py -v -p -s 10 -c 5 -d 7 -i -t /home/myuser/example.csv
```

Search for papers with custom column names and automatrically find the .csv file.
```bash
./jufo.py -a -n "Paper Titles;Journal Titles;issn;conference abbr"
```

By default the script uses ISSN or publication title for searching. If both are found then they are used together.


## Terminal manual
Usage: jufo.py [OPTION]... SOURCE
                
SOURCE is a mandatory path to the input csv data file.
Optionally you can use -a flag for automatic .csv file lookup.
    
"Available options:\n\n"
        
        -a, --automatic:    Automatic lookup attempt for .csv file in the current working directory. First match will be used in ascending alphabetical order. Disables SOURCE argument.
        -c  --count:        The amount of papers that TSV data will be fetched for.
        -d, --delay:        Delay between each http request in seconds. Integer value. Two requests are needed per paper. Three if it's a conference paper.
        -f, --force:        Force writing of TSV levels despite title comparison results.
        -i, --issn          Use only ISSN for searching TSV levels. Combine with -t if you want to require both issn and title.\n"
        -n, --names:        Names for alternative columns. Default values from Zotero are "Title", "Publication Title", "ISSN" and "Conference Name".
                            The values are case sensitive and should be given in that order. Use ";" as delimiter.
                            Example use: jufo.py -a -n "Paper Titles;Journal Titles;issn"
        -p, --progress      Show progress bar.
        -s, --start:        Starting index of first paper for fetching TSV data. Note that first row of csv data is the header.
        -t, --title:        Use only publication title for searching TSV levels. Combine with -i if you want to require both issn and title.
                            Therefore, -s 1 would point to the 2nd row of the file as it is the first paper.
                            As well -s 15 would start from the 15th paper/16th row of the csv and continue incrementally from there.
        -v, --verbose:      Show useful debugging related information.

# Future development ideas
Every contribution idea is welcome because both open science and open source software should be promoted.

`jufo.py` is a great reference for people learning about csv and html parsing basics in Python.
Command line argument parsing and progress bar basics can be also learned from this script.
The script can be forked for other similar parsing needs with small effort.
