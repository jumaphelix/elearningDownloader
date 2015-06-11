# downloader
This is a python3 command-line tool to download tutorial videos from e-learning platforms. 
It currently supports Cybrary (http://www.cybrary.it)

It requires that Python3 is installed including the following libraries:
1. requests
2. BeautifulSoup4

To get videos from Cybrary, you must first log in with your username and password and the hidden and undownloadable videos will be made downloadable by the program. 

It also supports proxies that are not password protected.

It has two options:
1. Downloading videos for a specific lesson or
2. Downloading vidoes from all lessons in a specific course. 

The program lists all available videos and their sizes (in Mbs) and gives you the option to choose which video you would like to download.
It also has a download counter that shows you download progress from 0% to 100%. 
