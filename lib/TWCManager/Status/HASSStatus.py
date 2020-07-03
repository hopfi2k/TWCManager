# HomeAssistant Status Output
# Publishes the provided sensor key and value pair to a HomeAssistant instance

from ww import f


class HASSStatus:

    import time
    import threading    
    import requests


    apiKey = None
    config = None
    configConfig = None
    configHASS = None
    debugLevel = 0
    master = None
    msgRateSeconds = 15
    resendRateInSeconds = 3600 
    retryRateInSeconds = 60
    msgQueue = {}    
    status = False
    serverIP = None
    serverPort = 8123
    timeout = 2
    backgroundTasksLock = threading.Lock()
    backgroundTasksThread = None

    def __init__(self, master):
        self.config = master.config
        self.master = master
        try:
            self.configConfig = self.config["config"]
        except KeyError:
            self.configConfig = {}
        try:
            self.configHASS = self.config["status"]["HASS"]
        except KeyError:
            self.configHASS = {}
        self.status = self.configHASS.get("enabled", False)
        self.serverIP = self.configHASS.get("serverIP", None)
        self.serverPort = self.configHASS.get("serverPort", 8123)
        self.apiKey = self.configHASS.get("apiKey", None)
        self.msgRateSeconds = self.configHASS.get("msgRateSeconds", 15)
        self.resendRateInSeconds = self.configHASS.get("resendRateInSeconds", 3600)
        self.retryRateInSeconds = self.configHASS.get("retryRateInSeconds", 60)
        self.debugLevel = self.configConfig.get("debugLevel", 0)

        # Unload if this module is disabled or misconfigured
        if ((not self.status) or (not self.serverIP)
           or (int(self.serverPort) < 1) or (not self.apiKey)):
            self.master.releaseModule("lib.TWCManager.Status","HASSStatus")     
        else:          
            self.backgroundTasksThread = self.threading.Thread(target=self.background_task_thread, args=())
            self.backgroundTasksThread.daemon = True
            self.backgroundTasksThread.start()

    def getTwident(self, twcid):
        # Format TWCID nicely
        if len(twcid) == 2:
            return "%02X%02X" % (twcid[0], twcid[1])
        else:
            return str(twcid.decode("utf-8"))

    def background_task_thread(self):
        while True:
            self.time.sleep(self.msgRateSeconds)
            self.backgroundTasksLock.acquire()
            for msg in self.msgQueue:
                if msg["elapsingTime"] < self.time.time():
                    self.sendingStatusToHASS(msg["sensor"], msg["twcid"], msg["key_underscore"], msg["key_camelcase"], msg["value"], msg["unit"])
            self.backgroundTasksLock.release()

    def getSensorName(self, twcid, key_underscore):
        return "sensor.twcmanager_" + str(self.getTwident(twcid)) + "_" + key_underscore

    def setStatus(self, twcid, key_underscore, key_camelcase, value, unit):
        self.backgroundTasksLock.acquire()
        sensor = self.getSensorName(twcid, key_underscore)  
        self.msgQueue[sensor] = {
                "elapsingTime": self.time.time(), 
                "sensor": sensor, 
                "twcid": twcid, 
                "key_underscore": key_underscore, 
                "key_camelcase": key_camelcase, 
                "value": value, 
                "unit": unit 
            }
        self.backgroundTasksLock.release()

    def sendingStatusToHASS(self, sensor, twcid, key_underscore, key_camelcase, value, unit):

        url = "http://" + self.serverIP + ":" + self.serverPort
        url = url + "/api/states/" + sensor
        headers = {
            "Authorization": "Bearer " + self.apiKey,
            "content-type": "application/json",
        }
        try:
            self.master.debugLog(
                8,
                "HASSStatus",
                f(
                    "Sending POST request to HomeAssistant for sensor {sensor} (value {value})."
                ),
            )

            devclass = ""
            if  str.upper(unit) in ["W","A","V","KWH"]:
                devclass="power"

            if len(unit)>0:
                self.requests.post(
                    url, json={"state": value, "attributes": { "unit_of_measurement": unit, "device_class": devclass, "friendly_name": "TWC " + str(self.getTwident(twcid)) + " " + key_camelcase } }, timeout=self.timeout, headers=headers
                )
            else:
                self.requests.post(
                    url, json={"state": value, "attributes": { "friendly_name": "TWC " + str(self.getTwident(twcid)) + " " + key_camelcase } }, timeout=self.timeout, headers=headers
                )
            # Setting elapsing time to now + resendRateInSeconds
            self.msgQueue[sensor]["elapsingTime"] = self.time.time() + self.resendRateInSeconds               
        except self.requests.exceptions.ConnectionError as e:
            self.master.debugLog(
                4,
                "HASSStatus",
                "Error connecting to HomeAssistant to publish sensor values",
            )
            self.master.debugLog(10, "HASSStatus", str(e))
            self.settingRetryRate(sensor)
            return False
        except self.requests.exceptions.ReadTimeout as e:
            self.master.debugLog(
                4,
                "HASSStatus",
                "Error connecting to HomeAssistant to publish sensor values",
            )
            self.master.debugLog(10, "HASSStatus", str(e))
            self.settingRetryRate(sensor)
            return False
        except Exception as e:
            self.master.debugLog(
                4,
                "HASSStatus",
                "Error during publishing HomeAssistant sensor values",
            )
            self.master.debugLog(10, "HASSStatus", str(e))
            self.settingRetryRate(sensor)
            return False

    def settingRetryRate(self, sensor):
        # Setting elapsing time to now + retryRateInSeconds
        self.msgQueue[sensor]["elapsingTime"] = self.time.time() + self.retryRateInSeconds     
