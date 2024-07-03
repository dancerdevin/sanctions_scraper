import requests
import pandas
import re
from bs4 import BeautifulSoup
import time
import json
import datetime
# Note: you must install the lxml package, to help Beautiful Soup with faster parsing, for this code to run.

# Defining lists to be used as columns in our data frame.
# Column 1: DocNumbers/patent numbers, to serve both as ID numbers and to iterate through the URLs of the patents
doc_num = []
# RECOMMENDED TOTAL RANGE: (2180000, 2822145) FOR ABOUT 650K PATENTS
# To be safe, break it up into sections (make sure not to overwrite your csv or txt files!)
for i in range(2722145, 2822145):
    doc_num.append(i)
# Column 3: Application Date -- between (22) and either (24) or (45) [so first parse to 45, then to 22 if app]
application_date = []
# Column 4: Industries -- between (51) and either (52) or (12)
industries = []
# Column 5: Applicants -- (71) because sometimes there aren't authors
applicants = []
# Column 6: Authors -- (72) if applicable
authors = []
# Column 7: Author Countries -- (**) letters after (72) and before (73) if applicable and (54) if not
author_countries = []
# at the end, also save a text file with the counts of author countries
country_count = {}

# Iterate through doc_num to access each HTML file
for i in doc_num:
    # I force a delay of 3 seconds so that the Russian government does not think I am performing a DDoS attack.
    time.sleep(3)
    url = f"https://www1.fips.ru/registers-doc-view/fips_servlet?DB=RUPAT&rn=1&DocNumber={i}&TypeFile=html"
    response = requests.get(url)
    # Must install lxml library here for faster HTML parsing
    soup = BeautifulSoup(response.text, "lxml")
    # Find application date in HTML source
    application_date_match = re.search('\(22\).*\</b\>', str(soup))
    if not application_date_match:
        application_date.append("NA")
    else:
        # Clean up code based on expected formatting
        clean_application_date_string = application_date_match.group().split('a>, ')[1]
        clean_application_date_string = clean_application_date_string.split('</b')[0]
        application_date.append(clean_application_date_string)
    # Find Industries in HTML source (for some reason, I can only find them by tag!)
    industry_codes = soup.find_all('span', {'class': 'i'})
    patent_industries = []
    for code in industry_codes:
        clean_code = re.search('>.*<', str(code))
        clean_code = clean_code.group().strip(">< ")
        if clean_code not in patent_industries:
            # There are sometimes duplicate industry codes, so this conditional helps to avoid redundancy.
            patent_industries.append(clean_code)
    industries.append(patent_industries)
    # Beautiful Soup is a huge pain but I think I've hacked it. I'm forcing their stupid tagged object into a big string
    dirty_text = soup.find_all('p')
    # Forcibly remove all line breaks
    clean_text = str(dirty_text).replace("\n", "")
    # Some of these older patents just list "applicants," some just list "authors."
    # NOTE: I am only scraping the country codes from "authors"! That seems to be how the newer ones are formatted.
    # I expect that all the newer patents will just have "NA" here, but I am tracking it just to be safe.
    applicants_match = re.search('\(71\).*\(72\)', clean_text)
    patent_applicants = []
    if not applicants_match:
        patent_applicants.append("NA")
    else:
        split_applicants = applicants_match.group().split('<br/>')
        for applicant in split_applicants:
            if applicant not in patent_applicants:
                patent_applicants.append(applicant)
    applicants.append(patent_applicants)
    authors_match = re.search('\(72\).*\(73\)', clean_text)
    patent_authors = []
    patent_author_countries = []
    if not authors_match:
        patent_authors.append("NA")
    else:
        split_authors = authors_match.group().split('<br/>')
        # The first item will be the "authors" line, so I am removing it.
        split_authors.pop(0)
        # The last item will have HTML tag junk in it to be cleaned up.
        split_authors[-1] = split_authors[-1].split("</")[0]
        for author in split_authors:
            if author not in patent_authors:
                patent_authors.append(author)
                # Every two capital letters contained within parentheses is presumed to be a country code.
                author_country = re.search("\([A-Z][A-Z]\)", author)
                if author_country:
                    clean_country = author_country.group().strip('() ')
                    patent_author_countries.append(clean_country)
    authors.append(patent_authors)
    author_countries.append(patent_author_countries)

# print(doc_num)
# print(application_date)
# print(industries)
# print(applicants)
# print(authors)
# print(author_countries)

# Create data frame using Pandas, using the above lists as columns, for export into CSV.
data_frame = pandas.DataFrame({"Patent Number": doc_num,
                               "Application Date": application_date,
                               "Industry Codes": industries,
                               "Applicants": applicants,
                               "Authors": authors,
                               "Author Countries": author_countries})
# Using a datetime string to help make sure that we do not accidentally overwrite our files.
date_string = str(datetime.datetime.today()).split(":")[0]
data_frame.to_csv(f'russian_patents_{date_string}.csv', index=False, encoding="utf-8-sig")
# Update country_count dictionary with new country count
for sublist in author_countries:
    for country in sublist:
        try:
            country_count[country] = country_count[country] + 1
        except KeyError:
            country_count[country] = 1

# Write the dictionary to a TXT file using json. Look in country_count.txt for the number of country references!
print(country_count)
with open(f"country_count_{date_string}.txt", "w") as text_file:
    text_file.write(json.dumps(country_count))