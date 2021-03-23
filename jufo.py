
# Jufo.py version 1.0 - A html parsing tool for adding academic publications' TSV values into a CSV file from tsv.fi database.

# Copyright 2021 IctCat (https://github.com/IctCat)

# MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including 
# without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject 
# to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH 
# THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''
WARNING: DON'T USE THIS SCRIPT FOR UNTRUSTED OR MALICIOUS WEBSITES! HTML/XML parsing can be exploited!
https://docs.python.org/3/library/xml.html#xml-vulnerabilities
'''

def print_manual():
    print("\n\n"                                    
            "          # #    # ######  ####      #####  #   #\n" 
            "          # #    # #      #    #     #    #  # # \n" 
            "          # #    # #####  #    #     #    #   #  \n" 
            "    #     # #    # #      #    #     #####    #  \n" 
            "    #     # #    # #      #    #     #        #  \n" 
            "     #####   ####  #       ####   #  #        #  \n\n")

    print("A html parsing tool for adding academic publications' TSV values into a CSV file from tsv.fi database.\n\n\n"
        "Usage: jufo.py [OPTION]... SOURCE\n\n"
        
        "SOURCE is a mandatory path to the input csv data file.\n"
        "Optionally you can use -a flag for automatic .csv file lookup.\n\n"
               
        "Available options:\n\n"
        
        "-a, --automatic:    Automatic lookup attempt for .csv file in the current working directory. First match will be used in ascending alphabetical order. Disables SOURCE argument.\n"
        "-c  --count:        The amount of papers that TSV data will be fetched for.\n"
        "-d, --delay:        Delay between each http request in seconds. Integer value. Two requests are needed per paper. Three if it's a conference paper.\n"
        "-e, --encoding:     Encoding to use for reading the CSV file. Defaults to utf-8.\n"
        "-f, --force:        Force writing of TSV levels despite title comparison results.\n"
        "-i, --issn          Use only ISSN for searching TSV levels. Combine with -t if you want to require both issn and title.\n"
        "-l, --limiter:      Delimiter for reading CSV file. If not specified then default delimiter is ;\n"
        '-n, --names:        Names for alternative columns. Default values from Zotero are "Title", "Publication Title", "ISSN" and "Conference Name".\n'
        '                    The values are case sensitive and should be given in that order. Use ";" as delimiter.\n'
        '                    Example use: jufo.py -a -n "Paper Titles;Journal Titles;issn;conference abbr"\n'
        "-p, --progress:     Show progress bar.\n"
        "-s, --start:        Starting index of first paper for fetching TSV data. Note that first row of csv data is the header.\n" 
        "-t, --title:        Use only publication title for searching TSV levels. Combine with -i if you want to require both issn and title.\n"
        '                    Therefore, -s 1 would point to the 2nd row of the file as it is the first paper.\n'
        '                    As well -s 15 would start from the 15th paper/16th row of the csv and continue incrementally from there.\n\n'
        '-v, --verbose:      Show useful debugging related information.'
        "COPYRIGHT\n"
        "                    Copyright 2021 IctCat\n"
        "                    MIT License\n"
             
        "SEE ALSO\n"
        "                    https://github.com/IctCat/jufopy")

import argparse, csv, getopt, glob, os, sys
import requests
import random
from bs4 import BeautifulSoup
from tempfile import NamedTemporaryFile
import shutil
import re
import time
import urllib
from progress.bar import IncrementalBar

DEFAULT_REQUEST_DELAY = 5 # Seconds

SEARCH_URL_BASE = "https://www.tsv.fi/julkaisufoorumi/haku.php?lang=&nimeke="
SEARCH_URL_CONFERENCE = "&konferenssilyh="
SEARCH_URL_ISSN = "&issn="
SEARCH_URL_END = "&tyyppi=kaikki&kieli=&maa=&wos=&scopus=&nappi=Search"
TSV_URL_BASE = "https://www.tsv.fi/julkaisufoorumi/tulokset.php?%20%20%20%20%20%20o=0&md5="
RESULT_URL_BASE = "https://www.tsv.fi/julkaisufoorumi/tiedot.php?PHPSESSID="
RESULT_URL_DETAIL = "&nayta="
RESULT_URL_RANDOM = "&r="

# Default Zotero column names
DEFAULT_TITLE = "Title"
DEFAULT_PUBLICATION_TITLE = "Publication Title"
DEFAULT_ISSN = "ISSN"
DEFAULT_CONFERENCE = "Conference Name"

NULL_TSV_LEVEL_MARKER = "Null"
DEFAULT_CSV_LIMITER = ";"
DEFAULT_CSV_ENCODING = "utf-8"

config = None


def request_details(phpsession_id, details_id):
    random_number = str(random.randint(10000, 99999))

    details_request_url = RESULT_URL_BASE + phpsession_id + RESULT_URL_DETAIL + details_id + RESULT_URL_RANDOM + random_number
    
    if config.isDebugging():
        print("Requesting: ", details_request_url)
    
    time.sleep(config.getDelay())
    details_request = requests.get(details_request_url)

    html_text = details_request.text
    soup = BeautifulSoup(html_text, 'html.parser')
    soup_result = soup.find("th", string="Lyhenne")
    parent = soup_result.parent
    conference_name = parent.td.contents[0]
    return conference_name

def request_paper(publication=None, issn=None, conference=None):
    
    title_query_param = ""
    issn_query_param = ""
    conference_query_param = ""
    
    if publication:
        jufo_safe_title = publication.replace("&", "and")
        title_query_param = urllib.parse.quote(jufo_safe_title, safe='')
    if issn:
        for idx,character in enumerate(issn):
            if((idx != 4) and idx < 9):
                issn_query_param += character
            elif(idx == 4):
                issn_query_param += "-"
                if(character != "-"):
                    issn_query_param += character
    if conference:
        last_parentheses_regex = r"\(([^)]*)\)[^(]*$"
        conference_abbr_regex = re.search(last_parentheses_regex, conference)
        if conference_abbr_regex:
            conference_query_param = conference_abbr_regex.group(0)
            conference_query_param = re.sub(r"[()]", "", conference_query_param)
        else:
            conference = ""
        title_query_param = ""

    base_request_url = SEARCH_URL_BASE + title_query_param + SEARCH_URL_CONFERENCE + conference_query_param + SEARCH_URL_ISSN + issn_query_param + SEARCH_URL_END
    if config.isDebugging():
        print("Requesting: ", base_request_url)
    base_request = requests.get(base_request_url)

    # Regex matching everything between: 'o="+ofs+"&md5=' and '";'. Result should contain necessary md5 and PHPSESSID
    reg_result = re.search(r'(?<=o=\"\+ofs\+\"\&md5=)(.*)(?=\";)', base_request.text)

    if reg_result:
        search_cookie = reg_result.group(0)

    
    search_url = TSV_URL_BASE + search_cookie
    
    if config.isDebugging():
        print("Requesting: ", search_url)

    time.sleep(config.getDelay())
    search_request = requests.get(search_url)

    phpsessid = re.search(r'PHPSESSID=(.*)\&d=', search_cookie).group(1)

    html_text = search_request.text
    soup = BeautifulSoup(html_text, 'html.parser')
    #soup_results = soup.select(".detaillink")
    soup_results = soup.find_all("span", class_="detaillink")

    jufo_name = ""
    jufo_level = None
    
    for result in soup_results:
        if(result.contents):
            if conference:
                span_string = str(result)
                details_regex = re.search(r'(?<=details\()(.*)(?=\);\">)', span_string)
                if details_regex:
                    details_id = details_regex.group(0)
                else:
                    continue
                received_conference = request_details(phpsessid, details_id)
                if (received_conference.lower() != conference_query_param.lower()):
                    continue
               
            jufo_name = str(result.contents[0])
            parent = result.parent                  # Get parent (div) of the span that had "detaillink" class
            sibling = parent.previous_sibling       # Get previous div
            if(len(sibling.contents[0]) > 0):       # Make sure that the div has level content
                jufo_level = int(str(sibling.contents[0]))
                if config.isForcing():
                    return jufo_level
            else:
                jufo_level = NULL_TSV_LEVEL_MARKER
                if config.isForcing():
                    return jufo_level
            break

    comparison_name = jufo_name.lower().replace(" ", "")
    comparison_title = jufo_safe_title.lower().replace(" ", "")      
    
    if config.isDebugging():
        print("( - REQUEST RESULT VALIDATION - ) < RECEIVED NAME >: ", comparison_name, "& < REQUESTED NAME >: ", comparison_title, " & < TSV LEVEL VALUE >:", jufo_level)
    
    if (comparison_name != comparison_title):
        jufo_level = None
        if config.isDebugging():
            print("!!! WARNING !!! Unmatching journal names")

    if config.isDebugging():
        if not jufo_level:
            print("!!! WARNING !!! No result for publication: ", publication)
 
    return jufo_level

def parse_csv(filename, start=1, limit=None, 
              columns=[DEFAULT_TITLE, DEFAULT_PUBLICATION_TITLE, DEFAULT_ISSN, DEFAULT_CONFERENCE], 
              title_strict=False, issn_strict=False, 
              custom_delimiter=DEFAULT_CSV_LIMITER,
              custom_encoding=DEFAULT_CSV_ENCODING):
    tempfile = NamedTemporaryFile(mode='w+t', newline='', delete=False, encoding=custom_encoding)
    if config.isDebugging():
        print("Tempfile path: ", tempfile.name)

    no_results_list = []
    null_results_list = []
    incorrect_papers_list = []
    good_papers_list = []
    skipped_papers_count = 0
 
    with open(filename, 'r', newline='', encoding=custom_encoding) as csvfile, tempfile:
        total_rows = sum(1 for row in csvfile)
        csvfile.seek(0)
  
        paper_queue_count = total_rows-1
        if(limit != None):
            paper_queue_count = limit
        else: 
            paper_queue_count = paper_queue_count - (start-1)

        csvreader = csv.DictReader(csvfile, delimiter=custom_delimiter, quotechar='"')
        
        limit_counter = 0
        skip_counter = start - 1

        fields = csvreader.fieldnames
        if config.isDebugging():
            print("Existing CSV column names: ", fields)
        if "TSV" not in fields:
            fields.append("TSV")
        
        writer = csv.DictWriter(tempfile, delimiter=';', quotechar='"', fieldnames=fields)
        writer.writeheader()
        
        bar = IncrementalBar('Parsing', max=(total_rows-1), suffix='Elapsed: %(elapsed)ds - ETA: %(eta)ds - Papers done: %(index)d / %(max)d - %(percent)d%%')

        for row in csvreader:
            if(limit != None and limit_counter >= limit):
                if config.isDebugging():
                    print("Limit reached")
                
                bar.next()
                writer.writerow(row)
                skipped_papers_count += 1
                continue
            
            paper_title = row[columns[0]]
            paper_publication = row[columns[1]]
            paper_issn = row[columns[2]]
            paper_conference = row[columns[3]]

            if(skip_counter > 0):
                skip_counter -= 1
                if config.isDebugging():
                    print("\nSkipped paper: ", paper_title)
                
                bar.next()
                writer.writerow(row)
                skipped_papers_count += 1
                continue
            
            if config.isDebugging():
                print("\n---------------------------")

            if not paper_publication and not paper_issn:
                if config.isDebugging():
                    print("Paper: ", paper_title, "\nEmpty publication title and ISSN, skipping")
                
                bar.next()
                writer.writerow(row)
                
                incorrect_papers_list.append(paper_title)
                continue
            elif title_strict and issn_strict:
                if not paper_publication or not paper_issn:
                    if config.isDebugging():
                        print("Paper: ", paper_title, "\nEmpty publication title or ISSN, skipping")
                
                    bar.next()
                    writer.writerow(row)
                
                    incorrect_papers_list.append(paper_title)
                    continue
            elif title_strict:
                if not paper_publication:
                    if config.isDebugging():
                        print("Paper: ", paper_title, "\nEmpty publication title, skipping")
                
                    bar.next()
                    writer.writerow(row)
                
                    incorrect_papers_list.append(paper_title)
                    continue
            elif issn_strict:
                if not paper_issn:
                    if config.isDebugging():
                        print("Paper: ", paper_title, "\nEmpty ISSN, skipping")
                
                    bar.next()
                    writer.writerow(row)
                
                    incorrect_papers_list.append(paper_title)
                    continue

            paper_publication = paper_publication.strip()
            paper_conference = paper_conference.strip()
                
            if config.isDebugging():
                    print("Paper: ", paper_title, "\nRequesting with: ", paper_publication, "\nISSN: ", paper_issn)

            paper_tsv_level = request_paper(publication=paper_publication, issn=paper_issn, conference=paper_conference)
       
            time.sleep(config.getDelay())
            
            if paper_tsv_level == NULL_TSV_LEVEL_MARKER:
                null_results_list.append(paper_title)
                row['TSV'] = paper_tsv_level
            elif not paper_tsv_level:
                no_results_list.append(paper_title)
            else:
                good_papers_list.append(paper_title)
                row['TSV'] = paper_tsv_level
            
            if config.isDebugging():
                print("TSV: ", paper_tsv_level)
            
            bar.next()
            writer.writerow(row)
            limit_counter += 1
            
        bar.finish()


    shutil.move(tempfile.name, filename)

    if config.isDebugging():
        print("( --- Papers' summary --- )")
        print("Good result paper titles:", good_papers_list, sep='\n')
        print("Empty result paper titles: ", no_results_list, sep='\n')
        print("Null TSV result paper titles: ", null_results_list, sep='\n')

    print("( --- Parsing statistics --- )")
    print("Amount of good papers: ", len(good_papers_list))
    print("Amount of invalid papers: ", len(incorrect_papers_list))
    print("Amount of empty result papers: ", len(no_results_list))
    print("Amount of null TSV result papers: ", len(null_results_list))
    print("Amount of skipped papers: ", skipped_papers_count) 

    return

class Config:
    def __init__(self, debug, delay, force):
        self.debug = debug
        self.delay = delay
        self.force = force

    def isDebugging(self):
        return self.debug

    def getDelay(self):
        return self.delay

    def isForcing(self):
        return self.force

def main(argv):
    ARG_AUTOLOOKUP = False
    ARG_REQDELAY = 5
    ARG_TITLEFORCE = False
    ARG_COUNT = None
    ARG_COLUMN_NAMES = None
    ARG_PROGRESS = False
    ARG_START = 1
    ARG_CSVPATH = None
    ARG_VERBOSE = False
    ARG_ISSN_SEARCH = False
    ARG_TITLE_SEARCH = False
    ARG_DELIMITER = None
    ARG_ENCODING = None

    try:
        opts, args = getopt.getopt(argv,"ac:de:hil::fn:ps:tv",["automatic", "count=", "delay=", "encoding=", "force", "help", "issn", "limiter=", "names=", "progress", "start=", "title", "verbose"])
    except getopt.GetoptError:
       print("Incorrect flags received!\n\n"
            "Usage: jufo.py <optional flags> SOURCE\n"
            "For manual run: jufo.py --help\n")
       sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_manual()
            exit()
        elif opt in ("-a", "--automatic"):
            ARG_AUTOLOOKUP = True
            if(len(args) > 0):
                print("Incorrect arguments received!\n\n"
                "Using filepath argument with -a flag is not allowed!"
                "Usage: jufo.py <optional flags> SOURCE\n"
                "For manual run: jufo.py --help\n")
                sys.exit(2)
        elif opt in ("-c", "--count"):
            ARG_COUNT = arg
            try :
                ARG_COUNT = int(ARG_COUNT)
                assert(ARG_COUNT > 0)
            except (ValueError, AssertionError):
                print("Error: -c flag requires positive integer parameter")
                sys.exit(2)
        elif opt in ("-d", "--delay"):
            ARG_REQDELAY = arg
            try:
                ARG_REQDELAY = int(ARG_REQDELAY)
         
            except (ValueError, AssertionError):
                print("Error: -d flag requires positive or zero integer parameter")
                sys.exit(2)
        elif opt in ("-e", "--encoding"):
            ARG_ENCODING = arg
        elif opt in ("-f", "--force"):
            ARG_TITLEFORCE = True
        elif opt in ("-i", "--issn"):
            ARG_ISSN_SEARCH = True
        elif opt in ("-l", "--limiter"):
            ARG_DELIMITER = arg
        elif opt in ("-n", "--names"):
            ARG_COLUMN_NAMES = arg
            ARG_COLUMN_NAMES = ARG_COLUMN_NAMES.split(";")
            for idx,name in enumerate(ARG_COLUMN_NAMES):
                ARG_COLUMN_NAMES[idx] = name.replace(";", "")
    
            if(len(ARG_COLUMN_NAMES) != 4 or not all(ARG_COLUMN_NAMES)):
                print("Error: -n flag requires four column names.")
                sys.exit(2)
        elif opt in ("-p", "--progress"):
            ARG_PROGRESS = True
        elif opt in ("-s", "--start"):
            ARG_START = arg
            try:
                ARG_START = int(ARG_START)
                assert(ARG_START > 0)
            except (ValueError, AssertionError):
                print("Error: -s flag requires positive integer parameter")
                sys.exit(2)
        elif opt in ("-t", "--title"):
            ARG_TITLE_SEARCH = True
        elif opt in ("-v", "--verbose"):
            ARG_VERBOSE = True
    

    if(not ARG_AUTOLOOKUP):
        try:
            ARG_CSVPATH = args[0]
            if not os.path.exists(ARG_CSVPATH):
                raise FileNotFoundError
            else:
                csv_filepath = ARG_CSVPATH
        except FileNotFoundError:
            exit("Error: file " + ARG_CSVPATH + " not found")
        except IndexError:
            print("Incorrect arguments received!\n"
                "Filepath argument not given.\n\n"
                "Usage: jufo.py <optional flags> SOURCE\n"
                "For manual run: jufo.py --help\n")
            sys.exit(2)
    else:
        filelist = glob.glob("*.csv", recursive=False)
        file = sorted(filelist)[0]
        csv_filepath = os.path.join(os.getcwd(), file)

    if ARG_COLUMN_NAMES == None:
        ARG_COLUMN_NAMES = [DEFAULT_TITLE, DEFAULT_PUBLICATION_TITLE, DEFAULT_ISSN, DEFAULT_CONFERENCE]

    if ARG_DELIMITER == None:
        ARG_DELIMITER = DEFAULT_CSV_LIMITER

    if ARG_ENCODING == None:
        ARG_ENCODING = DEFAULT_CSV_ENCODING
    
    print("Source csv path: ", csv_filepath)    
    if ARG_VERBOSE:
        print("Debugging is ON")
        print("Automatic file lookup:  ", ARG_AUTOLOOKUP)
        print("REQDELAY:               ", ARG_REQDELAY, "s")
        print("Force TSV write:        ", ARG_TITLEFORCE)
        print("ISSN strict search:     ", ARG_ISSN_SEARCH)
        print("Title strict search:    ", ARG_TITLE_SEARCH)
        print("Paper processing count: ", ARG_COUNT)
        print("Starting paper number:  ", ARG_START)
        print("Custom column names:    ", ARG_COLUMN_NAMES)
        print("Progress bar enabled:   ", ARG_PROGRESS)
        print("CSV delimiter:          ", ARG_DELIMITER)
        print("CSV encoding:           ", ARG_ENCODING)
    
    global config
    config = Config(ARG_VERBOSE, ARG_REQDELAY, ARG_TITLEFORCE)   

    parse_csv(csv_filepath, start=ARG_START, limit=ARG_COUNT, columns=ARG_COLUMN_NAMES, title_strict=ARG_TITLE_SEARCH, 
              issn_strict=ARG_ISSN_SEARCH, custom_delimiter=ARG_DELIMITER, custom_encoding=ARG_ENCODING)
    

if __name__ == "__main__":
    main(sys.argv[1:])
    
    print("Execution finished")
