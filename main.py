from bs4 import BeautifulSoup
from requests import Session
import os, re, requests

#This function handles client-server communication through GET and POST commands.
def connect(session, url, method, data="", stream=""):
    try:
        if method=='GET':
            if stream=="stream":
                req=session.get(url, verify=True, stream=True )
            else:
                req=session.get(url, verify=True)
        if method=='POST':
            req=session.post(url,data=data, allow_redirects=True, verify=True )
    except requests.exceptions.ConnectTimeout as e:
        print(e)
        exit()
    except requests.exceptions.ReadTimeout as e:
        print(e)
        exit()
    except requests.exceptions.ConnectionError as e:
        print(e)
        exit()
    except requests.exceptions.HTTPError as e:
        print(e)
        exit()
    except requests.exceptions.SSLError as e:
        print(e)
        exit()
        
    if req!="":
        return req

#Boolean Function to handle login. If login is successful,it returns True, False otherwise. 
def login(session, loginurl,username, password):
    payload = {'log': username, 'pwd': password}
    r=connect(session,loginurl,"POST", payload)
    if r.history:
        return True
    else:
        return False
        
#Function to take course as a parameter and return all its lessons
def getCourseLessonsUrl(session, courseUrl):
    lessonUrls=[]
    r=connect(session, courseUrl,"GET")
    soup=BeautifulSoup(r.text)
    for link in soup.find_all("a", class_="title"):
        lessonUrls.append(link.get('href'))
        
    return lessonUrls

#Lesson videos are stored in vimeo. This function gets the respective vimeo video link for each lesson 
def getVimeoLessonLink(session, lessonUrl):
    r=connect(session,lessonUrl,"GET")
    videoLink=""
    soup=BeautifulSoup(r.text)
    for iframe in soup.find_all("iframe"):
        videoLink=iframe.get('src')
        
    return videoLink

#The videos in vimeo are hidden and marked as private and are rendered via javascript. 
#We need to cheat the server that we are viewing the video from a trusted and authorised site by sending a fake referer header
#This will make the server to respond by rendering both the html and the javascript which contains the required video url plus the authorising
#tokens and sessionids.
#It returns the html and javascript as a string which can easily be scaned to get the required data
def getVimeoLessonVideoHtml(session, url):
    session.headers.update({'referer': url})
    r=connect(session, url,"GET")
    html=r.text
    
    return html   
   
#Well, this function is quite complex but easy.
#It takes the html and javascript as a string and using regular expressions, narrows down the string until only the 
#video url is found.
#Since a specific lesson may have more than one video (probably of different sizes and qualities), we return all the 
#found vidoes as a list. 
def getDownloadLinks(videoHtml):
    cdn=re.compile("pdl.vimeocdn")#finds all data containing the cdn name
    commaSplitter=re.compile(",") #splits the javascript data at every coma to generate url:link pair
    videoSplitter=re.compile("\":") #splits the string at colons to seperate the url from real links
    videoFinder=re.compile("mp4\?") #finds all links with mp4 keyword
    urlFinder=re.compile("url")#helps to eliminate url key and remain with the link alone
    quoteRemover=re.compile("\"")#for removing quotes on the url link
    
    html=[] #Holds the string containing the cdn keyword
    videoList=[] #Holds the data containing the mp4 phrase. It has the url:link pair
    downloadUrls=[] #Holds the final list of video urls (Download links)
    
    #Read the file and make a soup object
    soup=BeautifulSoup(videoHtml)
    for data in soup.find_all('script'):#use only the javascript
        found=cdn.search(str(data))
        if  found:
           html.append(data.string)
    
    #split the data at commas
    splitData=commaSplitter.split(str(html))
    for data in splitData:
        video=videoFinder.search(data)
        if video:
            videoList.append(data)

    #Finally, get the video url by eliminating the url phrase
    for data in videoList:
        link=videoSplitter.split(str(data))
        for data in link:
            foundUrl=urlFinder.search(data)
            if foundUrl:
                pass
            else:
                #remove quotes from the found url and eppend it to the list
                url=quoteRemover.sub("", data)
                downloadUrls.append(url)
    return downloadUrls
    
#A simple function to get the size of a video file
def getFileSize(session, fileurl):
    r=connect(session,fileurl,"GET", "", "stream")
    total_length = int(r.headers.get('content-length'))
    lengthMbs=int((total_length/1000)/1000)
    
    return lengthMbs
    
#The function that downloads the video from the server and saves it as an mp4 file in the computer. 
def urlRetrieve(session, fileurl, saveto):
    print("\tConnecting to the file server. Please Wait...")
    r=connect(session, fileurl,"GET","",  "stream")
    print("\tConnected to the file server. Starting Download..")
    with open(saveto, 'wb') as file:
        dl=0
        total_length = int(r.headers.get('content-length'))
        lengthMbs=int((total_length/1000)/1000)
        print("\n\tStarted Download for "+fileurl+" size: "+str(lengthMbs)+" MBs\n")
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk:
                dl += len(chunk)
                percentage=float(dl/total_length)*100
                file.write(chunk)
                file.flush()
                print("\tDownloading "+str(dl)+" bytes of "+str(lengthMbs)+" Mbs: "+str(percentage)+"%")
        
    print("Successfully downloaded "+saveto)
  
#calls the urlRetrieve function to download the files  
def downloadFiles(session, fileurl, saveto):
    urlRetrieve(session, fileurl, saveto)
 
#A function to handle video download for lessons of a specified course   
def doCourse(session):
    courseUrl=input("Enter course url\n")
    dir=input("Enter directory to save videos into:\n")
    print("Scraping course to get its lessons. Pease wait...")
    lessons=getCourseLessonsUrl(session, courseUrl)
    print("Found "+str(len(lessons))+" Lessons")
    
    lessonCount=-1
    for lesson in lessons:
        lessonCount+=1
        print("("+str(lessonCount)+") "+lesson)
        lessonVimeoLink=getVimeoLessonLink(session, lesson)
        videoHtml=getVimeoLessonVideoHtml(session,lessonVimeoLink)
        print("\tSearching for video files for this lesson\n")
        downloadUrls=getDownloadLinks(videoHtml)
        videoCount=-1
        for url in downloadUrls:
            size=getFileSize(session, url)
            videoCount+=1
            print("\t("+str(videoCount)+") "+str(url)+"("+str(size)+"Mbs)")
        choice=int(input("\tEnter the index of the file to download or -1 to proceed without downloading any of them\n"))
        if choice<=len(downloadUrls) and choice>=0:
            lessonurl=lesson[:-1]
            filename=os.path.basename(lessonurl)
            saveto=dir+filename+".mp4"
            downloadFiles(session,downloadUrls[choice], saveto)
        else:
            pass
  
#Function to do video download for a specific lesson              
def doLesson(session):
    lesson=input("Enter lesson url\n")
    dir=input("Enter directory to save videos into:\n")
    print("Scraping lesson link for video files. Pease wait...")
    lessonVimeoLink=getVimeoLessonLink(session, lesson)
    videoHtml=getVimeoLessonVideoHtml(session,lessonVimeoLink)
    downloadUrls=getDownloadLinks(videoHtml)
    videoCount=-1
    for url in downloadUrls:
        size=getFileSize(session, url)
        videoCount+=1
        print("\t("+str(videoCount)+") "+str(url)+"  ("+str(size)+"Mbs)")
    choice=int(input("\tEnter the index of the video to download or -1 to proceed without downloading any of them\n"))
    if choice<=len(downloadUrls) and choice>=0:
        lessonurl=lesson[:-1]
        filename=os.path.basename(lessonurl)
        saveto=dir+filename+".mp4"
        downloadFiles(session,downloadUrls[choice], saveto)
    else:
        pass
   
#Main function of the program         
def main():
    headers = {'user-agent': 'Mozilla Firefox'}#some websites do not accept being scraped by programs. Let's cheat the server that we are browsing from Mozilla Firefox
    loginurl="https://www.cybrary.it/wp-login.php"
    
    username=input("Enter your username:\t")
    password=input("Enter your password:\t")
   
    with Session() as session:
        session.headers=headers
        useProxy=input("Use Proxy? (y or n)\n")
        if useProxy=='y':
            proxyUrl=input("Enter the proxy server url(must start with http or https. Password Accessible proxies not accepted):\t")
            proxyPort=input("Enter the proxy port:\t")
            proxies={'http':proxyUrl+":"+proxyPort, 'https':proxyUrl+":"+proxyPort}
            session.proxies=proxies
        print("Attempting to log you in. Just wait")
        if login(session, loginurl, username, password):
            print("You have been logged in")
            
            while 1:
                print("SELECT OPTION BELOW:")
                print("\t1. Enter 'c' to get Entire Course Videos")
                print("\t2. Enter 'l' to get Lesson Videos" )
                option=input("\t")
                if option=='c':
                    doCourse(session,)
                elif option=='l':
                    doLesson(session)
                else:
                    pass            
        else:
            print("Did not log in")
          
main()
