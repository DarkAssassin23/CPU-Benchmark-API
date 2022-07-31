#!/usr/bin/env python3
from requests import get
from bs4 import BeautifulSoup as bs
import csv, os, argparse

baseURL = "https://www.cpubenchmark.net/cpu.php?cpu="
# Default List of CPUs file
cpuListFileName = "cpus.txt"
# Default csv file
csvFileName = "cpuData.csv"
cpuDict = {
    "Name":[],
    "CPU Class":[],
    "Socket":[],
    "Launched":[],
    "Overall Score":[],
    "Single Thread Rating":[],
    "Clockspeed":[],
    "Turbo Speed":[],
    "TDP":[],
    "Cores":[],
    "Threads":[]
    }

# Extracts the name of the CPU from the website
def getCPUName(soup):
    nameLine = soup.find_all('span', class_="cpuname")
    for n in nameLine:
        print(n.text)
        cpuDict["Name"].append(n.text)
        if("[Dual CPU]" in n.text):
            return True
        else:
            return False

# Extracts the single thread rating of the CPU from the website
def getSingleThreadedScore(soup):
    data = soup.get_text()
    location = data.find("Single Thread Rating:")
    str = data[location:data.find('\n',location)]

    d = dict(x.split(":") for x in str.split("\n"))
    for k, v in d.items():
        cpuDict[k].append(v)

# Extracts the class of the CPU from the website
# ex. Laptop, Desktop, Server
def getChipType(soup):
    data = soup.get_text()
    location = data.find("Class:")
    str = data[location:data.find('\n',location)]

    d = dict(x.split(":") for x in str.split("\n"))
    for k, v in d.items():
        if(v==' '):
            v = "N/A"
        cpuDict["CPU Class"].append(v)

# Extracts the type of socket the CPU is made for from the website
def getSocketType(soup):
    data = soup.get_text()
    location = data.find("Socket:")
    str = data[location:data.find('\n',location)]

    d = dict(x.split(":") for x in str.split("\n"))
    for k, v in d.items():
        if(v==' '):
            v = "N/A"
        cpuDict[k].append(v)

# Extracts the quarter and year the CPU was released from the website
def getTimeOfRelease(soup):
    data = soup.get_text()
    location = data.find("CPU First Seen on Charts:")
    str = data[location+25:data.find('\n',location)]

    cpuDict["Launched"].append(str)

# Extracts the Overall Score of the CPU from the website
def getOverallScore(soup):
    overallScore = soup.find_all('span', attrs={'style':"font-family: Arial, Helvetica, sans-serif;font-size: 44px;	font-weight: bold; color: #F48A18;"})
    for os in overallScore:
        cpuDict["Overall Score"].append(os.text)

# Extracts the additional details about the CPU from the website
# ex. TDP, Number of Cores, Number of Threads, Clockspeeds, etc.
def getDetails(soup, dualCPU):
    data = soup.find_all('p', class_="bg-table-row")
    data += soup.find_all('p', class_="mobile-column")
    data += soup.find_all('p', attrs={"style":"padding-left: 35px;"})
    string = ""
    for x in data:
        if(("Cores" in x.text or "TDP" in x.text) and dualCPU):
            if(not "Cores" in x.text):
                string += x.text+"\n"
            else: 
                if("Threads" in x.text):
                    string += x.text[:x.text.find("Threads")]+"\n"
                    string += x.text[x.text.find("Threads"):]
                else:
                    string += x.text[:x.text.find(" ", x.text.find(" ")+1)]+"\n"
                    string += "Threads: "+x.text[x.text.find(":")+1:x.text.find(" ", x.text.find(" ")+1)]

        elif(not("TDP Down" in x.text) and not("TDP Up" in x.text)):
            if("Cores" in x.text and not dualCPU):
                if("Threads" in x.text):
                    if("Total Cores" in x.text):
                        string += x.text[x.text.find("Cores"):x.text.find("Cores,")]+"\n"
                        string += "Threads:"+x.text[x.text.find(",")+1:x.text.find("Threads")]+"\n"
                    elif("Primary" in x.text or "Performance" in x.text):
                        string += "Clockspeed:"+x.text[x.text.find("Threads,")+8:x.text.find("Base")]+"\n"
                        string += "Turbo Speed:"+x.text[x.text.find("Base,")+5:x.text.find("Turbo")]+"\n"
                    elif("Secondary" in x.text or "Efficient" in x.text):
                        pass
                    else:
                        string += x.text[:x.text.find("Threads")]+"\n"
                        string += x.text[x.text.find("Threads"):]
                else:
                    string += x.text[:x.text.find(" ", x.text.find(" ")+1)]+"\n"
                    string += "Threads: "+x.text[x.text.find(":")+1:x.text.find(" ", x.text.find(" ")+1)]
            else:
                string += x.text+"\n"

    d = dict(x.split(":") for x in string.strip().split("\n"))
    for k, v in d.items():
        if(("TDP" in k or "Cores" in k or "Threads" in k) and dualCPU):
            if("TDP" in k):
                tdp = v.strip().split(" ")
                tdp[0] = int(tdp[0]) * 2
                v = str(tdp[0])+" "+tdp[1]
            else:
                v = int(v)*2
        if("TDP" in k):
            cpuDict["TDP"].append(v)
        else:
            if(v==' ' or 'NA' in str(v)):
                v = "N/A"
            cpuDict[k].append(v)
    return d

# Checks to see if the CPU list file exists
def validInputFile():
    if(not os.path.exists(cpuListFileName)):
        print("Error: Could not find the file specified.")
        print("File \'"+cpuListFileName+"\' does not exist")
        return False
    return True

# Gets a list of all the CPUs from the 
# list of CPUs file
def getCPUs():
    lines = ""
    cpus = []
    with open(cpuListFileName, 'r') as f:
        lines = f.readlines()
    for line in lines:
        cpus.append(line.strip())
    return cpus

# Fills in any blanks in data after the 
# CPUs data has been gathered 
def fillGaps():
    # Make sure all categories were filled out
    targetLen = len(cpuDict["Name"])
    for k,v in cpuDict.items():
        while(targetLen>len(v)):
            cpuDict[k].append("N/A")

# Exports all the CPU data to the specified 
# csv file
def exportToCSV():
    print("Generating \'"+csvFileName+"\'...")
    with open(csvFileName, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(cpuDict.keys())
        writer.writerows(zip(*cpuDict.values()))

# Adds any auxiliary data to the respective cpu
def addAuxData(currentData):
    for k,v in currentData.items():
        # If k is not in cpuDict it is auxiliary
        if not k in cpuDict:
            count = 0
            cpuDict[k] = [None] * len(cpuDict["Name"])
            for curName in cpuDict["Name"]:
                if(curName in currentData["Name"]):
                    cpuDict[k][count] = currentData[k][currentData["Name"].index(curName)]
                else:
                    cpuDict[k][count] = "N/A"

                count += 1

# Adds a ranking based on overall score and 
# single threaded score
def rankCPUs():
    overallScores = [None] * len(cpuDict["Name"])
    singleThreadScores = [None] * len(cpuDict["Name"])
    for x in range(len(cpuDict["Name"])):
        overallScores[x] = int(cpuDict["Overall Score"][x])
        singleThreadScores[x] = int(cpuDict["Single Thread Rating"][x])

    overallScores.sort(reverse=True)
    singleThreadScores.sort(reverse=True)

    cpuDict["Overall Rank"] = [None] * len(cpuDict["Name"])
    cpuDict["Single Threaded Rank"] = [None] * len(cpuDict["Name"])

    for x in range(len(cpuDict["Name"])):
        cpuDict["Overall Rank"][x] = overallScores.index(int(cpuDict["Overall Score"][x]))+1
        cpuDict["Single Threaded Rank"][x] = singleThreadScores.index(int(cpuDict["Single Thread Rating"][x]))+1

# If the output CSV file exists, it gets read in
# so if you added additional info to the csv
# that info will be transfered, if the cpu exists
def readCSV():
    d={}
    if(os.path.exists(csvFileName)):
        with open(csvFileName, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for k, v in row.items():
                    if not k in d:
                        d[k] = []
                    d[k].append(v)
    return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='API to pull CPU data from cpubenchmark.net')
    parser.add_argument('-i', nargs=1, metavar="file", help="input file containing a list of CPUs")
    parser.add_argument('-o', nargs=1, metavar="file", help="output file to save data to")

    args = parser.parse_args()
    if(args.i is not None):
        cpuListFileName = str(args.i[0])
    if(args.o is not None):
        csvFileName = str(args.o[0])

    if(not validInputFile()):
        exit()

    try:
        cpus = getCPUs()

        currentData = readCSV()
        currentCPU = ""

        print("Gathering Results...")
        for cpu in cpus:
            currentCPU = cpu
            result = get(baseURL+cpu)
            soup = bs(result.content, "html.parser")

            sup = soup.find_all('sup')
            for x in sup:
                x.replaceWith('')

            dualCPU = getCPUName(soup)
            getChipType(soup)
            getSocketType(soup)
            getTimeOfRelease(soup)
            getOverallScore(soup)
            getSingleThreadedScore(soup)
            getDetails(soup, dualCPU)

            fillGaps()
        
        rankCPUs()
        addAuxData(currentData)
        exportToCSV()
        print("done.")
    except:
        print("\nAn error occurred gathering CPU data on the following CPU \'"+currentCPU+"\'.")
        print("Make sure the CPU is valid and/or formatted correctly, as seen below:")
        print("Intel Xeon X5650 @ 2.67GHz&cpuCount=2")
        print("Apple M1 Pro 10 Core")
        print("Intel Core i7-6920HQ @ 2.90GHz")
        print("Intel Core i9-9900K @ 3.60GHz")
        print("Intel Xeon E5-2670 v2 @ 2.50GHz")

