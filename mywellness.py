
import json
import xml.etree.cElementTree as ET
from datetime import datetime, timedelta

f = open('example.json')
jsonData = json.load(f)
data = jsonData['data']
print(jsonData['data']['equipmentType'])
f.close()

root = ET.Element("TrainingCenterDatabase")
root.attrib["xmlns"] = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
root.attrib["xmlns:ns3"] = "http://www.garmin.com/xmlschemas/ActivityExtension/v2"
activities = ET.SubElement(root, "Activities")
activity = ET.SubElement(activities, "Activity", Sport="Biking")

startDT = datetime(2022,10,27,15)
startTime = startDT.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

ET.SubElement(activity, "Id").text = startTime
lap = ET.SubElement(activity, "Lap", StartTime=startTime)
creator = ET.SubElement(activity, "Creator")
creator.attrib["xsi:type"] = "Device_t"
ET.SubElement(creator, "Name").text = "Yentl with barometer"

generalData = data["data"]
ET.SubElement(lap, "TotalTimeSeconds").text = '%.2f' % (generalData[0]["rawValue"]*60)
ET.SubElement(lap, "DistanceMeters").text = '%.2f' % (generalData[1]["rawValue"]*1000)
ET.SubElement(lap, "MaximumSpeed") # TBD
ET.SubElement(lap, "Calories") #TBD (zelf in te vullen?)
ET.SubElement(lap, "AverageHeartRateBpm") # TBD
ET.SubElement(lap, "MaximumHeartRateBpm") # TBD
ET.SubElement(lap, "Cadence") # TBD
ET.SubElement(lap, "TriggerMethod").text = "Manual"

track = ET.SubElement(activity, "Track")

samples = data["analitics"]["samples"]
prevSample = samples[0]
prevElevation = 0
for sample in samples:
    power = sample["vs"][0]
    cadence = sample["vs"][1]
    speed = sample["vs"][2]/3.6
    grade = sample["vs"][3]
    distance = sample["vs"][4]
    elevation = sample["vs"][5]

    elevationGain = (sample["vs"][4] - prevSample["vs"][4])*(grade/100)
    prevSample = sample
    prevElevation+=elevationGain
    
    currentDT = startDT + timedelta(seconds=sample["t"])
    trackpoint = ET.SubElement(track, "Trackpoint")
    ET.SubElement(trackpoint, "Time").text = currentDT.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    ET.SubElement(trackpoint, "DistanceMeters").text = '%.2f' % distance
    ET.SubElement(trackpoint, "Cadence").text = '%.2f' % cadence
    ET.SubElement(trackpoint, "AltitudeMeters").text = '%.2f' % prevElevation

    extensions = ET.SubElement(trackpoint, "Extensions")
    ns3 = ET.SubElement(extensions, "ns3:TPX")
    ET.SubElement(ns3, "ns3:Speed").text = '%.2f' % speed
    ET.SubElement(ns3, "ns3:Watts").text = '%.2f' % power


tree = ET.ElementTree(root)
tree.write("filename.tcx", encoding='utf-8',xml_declaration=True)