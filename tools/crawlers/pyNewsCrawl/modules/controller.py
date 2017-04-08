import os
import sys
import subprocess


class crawlerController():
    def __init__(self):
        # change working dir to script location
        #os.chdir(os.path.dirname(sys.argv[0]))
        self.crawlerList = self.getCrawlerNames()
        self.activeList, self.inactiveList = self.findActive()
        if self.activeList:
            print("Temp files exist, exiting...")
            exit()
        self.processes = []

    def main(self):
        while True:
            command = input("Enter a command like 'status', or type 'help'.")
            if command == 'start all':
                self.startAll()
                continue
            elif command == 'start script':
                name = input('Input script name.')
                self.startScript(name)
                continue
            elif command == 'stop all':
                self.stopAll()
                continue
            elif command == "stop script":
                name = input('Input script name.')
                self.stopScript(name)
                continue
            elif command == "status":
                self.getStatus()
                continue
            elif command == "exit":
                exit()
            elif command == "reset all":
                self.resetAll()
            elif command == "reset script":
                name = input('Input script name.')
                self.resetScript(name)
            else:
                print("'status' : display running and inactive scripts\n")
                print("'start all' : run all currently inactive scripts.\n")
                print("'start script' : run a single script.\n")
                print("'stop all' : stop all running scripts.\n")
                print("'stop script' : stop a single script.\n")
                print("'exit' : exit the program and shut down all scripts.\n")

    # function finds crawler scripts in working dir, makes list of names
    def getCrawlerNames(self):
        crawlerList = []
        for file in os.listdir("."):
            if ((file.endswith(".py") and file != "baseCrawler.py"
                 and file != "controller.py")):
                crawlerList.append(file[:-3])
        return(crawlerList)

    # function looks for temp files and makes lists of active/inactive scripts
    def findActive(self):
        activeList = []
        inactiveList = []
        for crawlerName in self.crawlerList:
            path = crawlerName + "/temp/"
            try:
                # look for any file in crawlerName/temp/ folder
                if any(os.path.isfile(os.path.join(path, i)) for
                        i in os.listdir(path)):
                    activeList.append(crawlerName)
                else:
                    inactiveList.append(crawlerName)
            except FileNotFoundError:
                inactiveList.append(crawlerName)
                print(crawlerName + " has never been run.")
        return(activeList, inactiveList)

    # prints current running/inactive script status
    def getStatus(self):
        self.getCrawlerNames()
        self.activeList, self.inactiveList = self.findActive()
        print(" #====Active Scripts====#")
        for each in self.activeList:
            print(each)
        print("#====Inactive Scripts====#")
        for each in self.inactiveList:
            print(each)

    # run all scripts that are currently not running
    def startAll(self):
        for each in self.inactiveList:
            self.startScript(each)

    # stop all scripts
    def stopAll(self):
        for each in self.processes:
            each[0].kill()

    # stop a single script
    def stopScript(self, name):
        for each in self.processes:
            if name == each[1]:
                each[0].kill()
                return None

    # start a specific script with a certain timing
    def startScript(self, name):
        pathToScript = './' + name + ".py"
        p = subprocess.Popen([sys.executable, pathToScript],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.processes.append([p, name])

controller = crawlerController()
controller.main()
