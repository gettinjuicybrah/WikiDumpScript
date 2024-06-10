#!/usr/bin/env python
# coding: utf-8

# for regular expression usage
import re
import os


def select_chunk(dump_path, filtered_path, chunk_size=16 * 1024 * 1024):
    # This will open the files, but not load them into memory.
    with open(dump_path, 'rb') as input_file, open(filtered_path, 'wb') as output_file:
        buffer = b""
        while True:
            chunk = input_file.read(chunk_size)
            # if the chunk is empty (end of file), exit the infinite loop
            if not chunk:
                break
            buffer = process_chunk(chunk, buffer, output_file)


def process_chunk(chunk, buffer, output_file):
    # Considers each page XML element using regular expressions
    # r is for raw characters in python. Literal characters. Like: \n are individual, not symbolic for a newline.
    # b indiciates a bytes literal, which is a sequence of bytes. useful when working with binary data.
    page_regex = re.compile(rb'<page>(.*?)</page>', re.DOTALL)

    buffer += chunk
    return analyze_page(page_regex, buffer, output_file)


def analyze_page(page_regex, buffer, output_file):
    start = 0
    # search for <page> ... </page> sequences.
    '''
    Importantly, must remember that a partial <page>...</page> sequence could be present, which is just where
    <page> is present, but not the closing </page> So, must account for the unclosed sequence. Such must be appended
    to the beginning of the next decompressed chunk to create a completed <page>...</page> sequence.
    '''
    for match in page_regex.finditer(buffer):
        page_content = match.group()
        global amnt
        amnt += 1
        print(f"Current page: {amnt}")
        # Check for keywords within the page content.
        if any(keyword.lower().encode() in page_content.lower() for keyword in keywords):
            add_page(page_content, output_file)
        '''
            start is an index representing the end of the last complete page element found.
            '''
        start = match.end()
        '''
            By doing this, we only keep the part of the buffer AFTER THE LAST
            COMPLETE PAGE ELEMENT.
            
            THIS ENSURES THAT ANY INCOMPLETE PAGE ELEMENT AT THE END OF THE
            CURRENT FILE IS PRESERVED FOR THE NEXT ITERATION.
            '''
    return buffer[start:]


def add_page(page_content, output_file):
    # writes the page content to the filtered xml file
    output_file.write(page_content)
    # write newline just after the newly added page.
    output_file.write(b'\n')
    global count
    count += 1
    title = extract_title(page_content)
    print(f"{count} articles contain the specified keywords. TITLE: {title}")


def extract_title(page_content):
    title_regex = re.compile(rb'<title>(.*?)</title>', re.DOTALL)
    title_match = title_regex.search(page_content)
    if title_match:
        title = title_match.group(1).decode('utf-8')
        return title
    return "No title found"


def main():
    dump_path = 'C:/Users/18284/Desktop/WikiDumpScript/data/filteredDump/filtered.xml'
    filtered_path = 'C:/Users/18284/Desktop/WikiDumpScript/data/filtered2Dump/filtered2.xml'
    # Check if the input file exists
    if not os.path.exists(dump_path):
        print(f"The file '{dump_path}' does not exist.")
        exit(1)

    # Define the keywords to filter the pages
    global keywords
    keywords = ['category:set theory', 'category:category theory',
                'category:mathematics', 'category:calculus',
                'category:geometry', 'category:algebra', 'category:number theory',
                'category:discrete mathematics', 'category:probability', 'category:statistics',
                'category:decision theory']

    global count
    count = 0
    global amnt
    amnt = 0

    # Start the filtration process
    select_chunk(dump_path, filtered_path)

    print("Filtration process completed.")


if __name__ == '__main__':
    main()
