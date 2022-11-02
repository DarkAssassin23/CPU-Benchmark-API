#!/usr/bin/env python3
from requests import get
from bs4 import BeautifulSoup as bs
from multiprocessing import Process, Queue
import csv, os, argparse, time, re

baseURL = "https://www.cpubenchmark.net/cpu.php?cpu="
# Default List of CPUs file
cpuListFileName = "cpus.txt"
# Default csv file
csvFileName = "cpuData.csv"
numPhysicalCPUs = 1
numCPUs = os.cpu_count()
processes = []
cpuDataDict = {
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
def getCPUName(soup, cpuDict):
    nameLine = soup.find_all('span', class_="cpuname")
    for n in nameLine:
        print(n.text)
        cpuDict["Name"].append(n.text)
        if("[Dual CPU]" in n.text):
            return 2
        elif("[Quad CPU]" in n.text):
            return 4
        else:
            return 1

# Extracts the single thread rating of the CPU from the website
def getSingleThreadedScore(soup, cpuDict):
    data = soup.get_text()
    location = data.find("Single Thread Rating:")
    str = data[location:data.find('\n',location)]
    if(str==""):
        str = "Single Thread Rating: N/A"
    d = dict(x.split(":") for x in str.split("\n"))
    for k, v in d.items():
        cpuDict[k].append(v.strip())

# Extracts the class of the CPU from the website
# ex. Laptop, Desktop, Server
def getChipType(soup, cpuDict):
    data = soup.get_text()
    location = data.find("Class:")
    str = data[location:data.find('\n',location)]
    if(str==""):
        str = "Class: N/A"
    d = dict(x.split(":") for x in str.split("\n"))
    for k, v in d.items():
        if(v==' '):
            v = "N/A"
        cpuDict["CPU Class"].append(v.strip())

# Extracts the type of socket the CPU is made for from the website
def getSocketType(soup, cpuDict):
    data = soup.get_text()
    location = data.find("Socket:")
    str = data[location:data.find('\n',location)]
    if(str==""):
        str = "Socket: N/A"
    d = dict(x.split(":") for x in str.split("\n"))
    for k, v in d.items():
        if(v==' '):
            v = "N/A"
        cpuDict[k].append(v.strip())

# Extracts the quarter and year the CPU was released from the website
def getTimeOfRelease(soup, cpuDict):
    data = soup.get_text()
    location = data.find("CPU First Seen on Charts:")
    str = data[location+25:data.find('\n',location)]

    cpuDict["Launched"].append(str)

# Extracts the Overall Score of the CPU from the website
def getOverallScore(soup, cpuDict):
    data = soup.get_text()
    # Index starts at the A and we want the end of the line
    # so we add the length of the string we're trying to find
    # to the index
    toFind = "Average CPU Mark"
    start = data.index(toFind)+len(toFind)
    # Ensure we go far enough past the line to find to 
    # get the score
    end = data[:start+len(toFind)].rindex("\n") 
    overallScore = data[start:end].strip()

    cpuDict["Overall Score"].append(overallScore)

# Extracts the additional details about the CPU from the website
# ex. TDP, Number of Cores, Number of Threads, Clockspeeds, etc.
def getDetails(soup, numPhysicalCPUs, cpuDict):
    data = soup.find_all('p')
    string = ""
    for x in data:
        clockspeed = re.search("Clockspeed", x.text)
        turbo = re.search("Turbo Speed", x.text)
        tdp = re.search("TDP", x.text)
        coresThreads = re.search("Cores", x.text)
        realData = ""
        if((not clockspeed == None)):
            realData = clockspeed.string
        if((not turbo == None)):
            realData = turbo.string
        if((not tdp == None)):
            realData = tdp.string
        if((not coresThreads == None)):
            realData = coresThreads.string

        if(not realData == ""):
            if(("Cores" in realData or "TDP" in realData) and numPhysicalCPUs > 1):
                if(not "Cores" in realData):
                    string += realData+"\n"
                else:
                    if("Threads" in realData):
                        string += realData[:realData.find("Threads")]+"\n"
                        string += realData[realData.find("Threads"):]+"\n"
                    else:
                        string += realData[:realData.find(" ", realData.find(" ")+1)]+"\n"
                        string += "Threads: "+realData[realData.find(":")+1:realData.find(" ", realData.find(" ")+1)]+"\n"

            elif(not("TDP Down" in realData) and not("TDP Up" in realData)):
                if("Cores:" in realData and numPhysicalCPUs == 1):
                    if("Threads" in realData):
                        if("Total Cores" in realData):
                            string += realData[realData.find("Cores"):realData.find("Cores,")]+"\n"
                            string += "Threads:"+realData[realData.find(",")+1:realData.find("Threads")]+"\n"
                        elif("Primary" in realData or "Performance" in realData):
                            string += "Clockspeed:"+realData[realData.find("Threads,")+8:realData.find("Base")]+"\n"
                            string += "Turbo Speed:"+realData[realData.find("Base,")+5:realData.find("Turbo")]+"\n"
                        elif("Secondary" in realData or "Efficient" in realData):
                            pass
                        else:
                            string += realData[:realData.find("Threads")]+"\n"
                            string += realData[realData.find("Threads"):]+"\n"
                    else:
                        string += realData[:realData.find(" ", realData.find(" ")+1)]+"\n"
                        string += "Threads: "+realData[realData.find(":")+1:realData.find(" ", realData.find(" ")+1)]+"\n"
                elif(len(realData)<30):
                    string += realData+"\n"

    d = dict(x.split(":") for x in string.strip().split("\n"))
    for k, v in d.items():
        if("TDP" in k or "Cores" in k or "Threads" in k):
            if("TDP" in k):
                tdp = v.strip().split(" ")
                tdp[0] = int(round(float(tdp[0]))) * numPhysicalCPUs
                v = str(tdp[0])+" "+tdp[1]
            else:
                v = int(v)*numPhysicalCPUs
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
        # Find where comments start and ignore everything
        # after the start of the comment
        if(line.find("#") != -1 or line.find("//") != -1):
            if(min(line.find("#"), line.find("//")) != -1):
                line = line[:min(line.find("#"), line.find("//"))]
            else:
                line = line[:max(line.find("#"), line.find("//"))]
        if(not line.strip() == ''):
            cpus.append(line.strip())
    return cpus

# Fills in any blanks in data after the
# CPUs data has been gathered
def fillGaps(cpuDict):
    # Make sure all categories were filled out
    targetLen = len(cpuDict["Name"])
    for k,v in cpuDict.items():
        while(targetLen>len(v)):
            cpuDict[k].append("N/A")

# Exports all the CPU data to the specified
# csv file
def exportToCSV(cpuDict):
    print("Generating \'"+csvFileName+"\'...")
    try:
        with open(csvFileName, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(cpuDict.keys())
            writer.writerows(zip(*cpuDict.values()))
    except:
        print("Error: unable to write to \'"+csvFileName+"\'. Make sure you have "+
            "permission to write to this file and it is not currently open and try again")

# Adds any auxiliary data to the respective cpu
def addAuxData(currentData, cpuDict):
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
def rankCPUs(cpuDict):
    overallScores = []
    singleThreadScores = []
    for x in range(len(cpuDict["Name"])):
        if(not (cpuDict["Overall Score"][x] == "N/A")):
            overallScores.append(int(cpuDict["Overall Score"][x]))
        else:
            overallScores.append(0)
        if(not (cpuDict["Single Thread Rating"][x] == "N/A")):
            singleThreadScores.append(int(cpuDict["Single Thread Rating"][x]))
        else:
            singleThreadScores.append(0)

    overallScores.sort(reverse=True)
    singleThreadScores.sort(reverse=True)

    cpuDict["Overall Rank"] = [None] * len(cpuDict["Name"])
    cpuDict["Single Threaded Rank"] = [None] * len(cpuDict["Name"])
    
    for x in range(len(cpuDict["Name"])):
        if(cpuDict["Overall Score"][x] == "N/A"):
            cpuDict["Overall Rank"][x] = "N/A";
        else:
            cpuDict["Overall Rank"][x] = overallScores.index(int(cpuDict["Overall Score"][x]))+1
        if(cpuDict["Single Thread Rating"][x] == "N/A"):
            cpuDict["Single Threaded Rank"][x] = "N/A"
        else:
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

# Function to get the results for the list of cpu's provided
def gatherResults(cpus, queue):
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
    try:
        for cpu in cpus:
            currentCPU = cpu
            result = get(baseURL+cpu)
            soup = bs(result.content, "html.parser")

            sup = soup.find_all('sup')
            for x in sup:
                x.replaceWith('')

            numPhysicalCPUs = getCPUName(soup, cpuDict)
            getChipType(soup, cpuDict)
            getSocketType(soup, cpuDict)
            getTimeOfRelease(soup, cpuDict)
            getOverallScore(soup, cpuDict)
            getSingleThreadedScore(soup, cpuDict)
            getDetails(soup, numPhysicalCPUs, cpuDict)

            fillGaps(cpuDict)
        queue.put(cpuDict)
        return cpuDict
    except:
        print("\nAn error occurred gathering CPU data on the following CPU \'"+currentCPU+"\'.")
        print("Make sure the CPU is valid and/or formatted correctly")
        print("To see examples of correct formatting, add the \'-e\' flag\n")
        queue.put(None)
    
# Evenly splits the number of cpu's to get by
# the desired number of processes to run, up to
# the maximum number the computer has, to get the
# data in parallel to speed up the process
def multiProcess(cpus, processesToRun):
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
    
    if(processesToRun > numCPUs):
        processesToRun = numCPUs
    if(processesToRun > len(cpus)):
        processesToRun = len(cpus)
        
    queue = Queue(processesToRun)
    numCPUsPerProcess = len(cpus) // processesToRun
    extra = len(cpus) % processesToRun
    start = 0
   
    for x in range(processesToRun):
        cpusToGet = []
        end = start+numCPUsPerProcess
        if(extra>0):
            end += 1
            extra -= 1
          
        cpusToGet = cpus[start:end]
        start = end
        
        p = Process(target=gatherResults, args=(cpusToGet, queue))
        processes.append(p)
        p.start()
    
    while(not queue.full()):
        pass
        
    for x in range(processesToRun):
        d = queue.get()
        for k,v in d.items():
            for x in v:
                cpuDict[k].append(x)

    return cpuDict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='API to pull CPU data from cpubenchmark.net')
    parser.add_argument('-i', nargs=1, metavar="file", help="input file containing a list of CPUs")
    parser.add_argument('-o', nargs=1, metavar="file", help="output file to save data to")
    parser.add_argument('-p', nargs='?', type=int, const=numCPUs, metavar="processes",
        help="the number of processes you would like to run. If left blank, it will run with the maximum number of available CPUs")
    parser.add_argument('-e', action='store_true', help="examples of how CPUs should be formatted")

    singleThreaded = True
    cpusToUse = 0
    
    args = parser.parse_args()
    if(args.e):
        print("Exmaple CPU's:")
        print("Intel Xeon X5650 @ 2.67GHz&cpuCount=2")
        print("Apple M1 Pro 10 Core")
        print("Intel Core i7-6920HQ @ 2.90GHz")
        print("Intel Core i9-9900K @ 3.60GHz")
        print("Intel Xeon E5-2670 v2 @ 2.50GHz")
        exit()
        
    if(args.i is not None):
        cpuListFileName = str(args.i[0])
    if(args.o is not None):
        csvFileName = str(args.o[0])
    if(args.p is not None):
        cpusToUse = args.p
        singleThreaded = False

    if(not validInputFile()):
        exit()

    try:
        start = time.time()
        cpus = getCPUs()

        currentData = readCSV()
        currentCPU = ""

        if(singleThreaded):
            cpuDataDict = gatherResults(cpus, Queue(1))
        else:
            cpuDataDict = multiProcess(cpus, cpusToUse)
        rankCPUs(cpuDataDict)
        addAuxData(currentData, cpuDataDict)
        exportToCSV(cpuDataDict)
        finalTime = time.time() - start

        print("done.")
        print("Finished in: "+str(finalTime)+" seconds")
        
    except:
        print("\nAn error occurred during processing")
