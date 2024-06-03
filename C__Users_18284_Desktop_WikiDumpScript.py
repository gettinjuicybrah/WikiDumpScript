#!/usr/bin/env python
# coding: utf-8

# For handling the large bz2 compressed dump in chunks - prevent loading entire dump inot memory.
import bz2
# for regular expression usage
import re
import os


def decompress_chunk(dump_path, filtered_path, chunk_size=16 * 1024 * 1024):
    # Initialize the decompressor object.
    decompressor = bz2.BZ2Decompressor()
    # This will open the files, but not load them into memory.
    with open(dump_path, 'rb') as input_file, open(filtered_path, 'wb') as output_file:
        buffer = b""

        while not decompressor.eof:
            '''
            When you open a file in read mode in Python, an internal pointer
            is maintained that tracks the current position in the file. 
            So, each call to 'input_file.read(chunk_size)' reads the next
            'chunk_size' bytes from the current position and advances the pointer
            by 'chunk_size' bytes. 
            
            This ensures that each subsequent read operation continues from where
            the last one left off.
            '''
            compressed_chunk = input_file.read(chunk_size)

            # if the chunk is empty (end of file), exit the infinite loop
            if not compressed_chunk:
                break

            '''
            Here, we actually get the decompressed chunk for the current
            iteration using our decompressor object.
            '''
            decompressed_chunk = decompressor.decompress(compressed_chunk)

            # Now, it is time to process our decompressed chunk!
            # this will end up either being an empty string OR the incomplete <page>...<\page> sequence that must be appended
            # to the beginning of the next decompressed chunk. This is already taken care of within process_decompressed_chunk
            # because we concatenate the decompressed chunk to buffer there. Within analyze_page, we set buffer to buffer[start:]
            # of which is either empty string or the incomplete sequence. So, concatenated is the empty string, or the
            # beginning of the sequence that's match is then within the next decompressed chunk.
            buffer = process_decompressed_chunk(decompressed_chunk, buffer, output_file)


'''
This function will process the decompressed chunk.
It will iterate through it via 
'''


def process_decompressed_chunk(decompressed_chunk, buffer, output_file):
    # Considers each page XML element using regular expressions
    # r is for raw characters in python. Literal characters. Like: \n are individual, not symbolic for a newline.
    # b indiciates a bytes literal, which is a sequence of bytes. useful when working with binary data.
    page_regex = re.compile(rb'<page>(.*?)</page>', re.DOTALL)

    '''
        This line appends the decompressed chunk to the buffer. Since the
        decompressed chunk might only contain a part of a '<page>' element, we
        accumulate the data in the buffer until we have a complete '<page>' element
        
        The buffer will allow us to accumulate data until complete '<page>' elements
        are avilable, process them then clear the buffer accordingly.
        '''
    buffer += decompressed_chunk
    return analyze_page(page_regex, buffer, output_file)


'''
This function will analyze the particular page within the currently 
considered decompressed chunk. 

If the page contains any of the specified keywords, then call to add_page().
'''


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


'''
This function will add the page to the filtered.xml file.
'''


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
    dump_path = 'C:/Users/18284/Desktop/WikiDumpScript/data/baseDump/enwiki-20240220-pages-articles.xml.bz2'
    filtered_path = 'C:/Users/18284/Desktop/WikiDumpScript/data/filteredDump/filtered.xml'
    # Check if the input file exists
    if not os.path.exists(dump_path):
        print(f"The file '{dump_path}' does not exist.")
        exit(1)

    # Define the keywords to filter the pages
    global keywords
    keywords = ['mathematics', 'set theory', 'category theory']

    global count
    count = 0

    # Start the filtration process
    decompress_chunk(dump_path, filtered_path)

    print("Filtration process completed.")


if __name__ == '__main__':
    main()
