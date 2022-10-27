import json
import uuid
from datetime import datetime, timedelta

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.activity_message import ActivityMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.messages.event_message import EventMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.record_message import RecordMessage
from fit_tool.profile.profile_type import FileType, Manufacturer, Sport, Event, EventType

prevDistance = 0
altitude = 0
totalAscent = 0
totalDescent = 0

def createMessage(sport, sample, timeDiff):
    global altitude
    global prevDistance
    global totalAscent
    global totalDescent
    message = RecordMessage()
    distance = 0
    grade = 0
    speed = 0

    if sport == Sport.CYCLING:
        power = sample["vs"][0]
        cadence = sample["vs"][1]
        speed = sample["vs"][2] / 3.6
        grade = sample["vs"][3]
        distance = sample["vs"][4]

        message.cadence = cadence
        message.power = power
    elif sport == Sport.RUNNING:
        speed = sample["vs"][0] / 3.6
        grade = sample["vs"][1]
        distance = sample["vs"][2]

    distance += speed * timeDiff
    elevationGain = (distance - prevDistance) * (grade / 100)
    prevDistance = distance
    altitude += elevationGain

    if elevationGain > 0:
        totalAscent += elevationGain
    elif elevationGain < 0:
        totalDescent += elevationGain

    message.distance = distance
    message.speed = speed
    message.altitude = altitude
    return message


def convert(jsonData):
    data = jsonData['data']

    if data["equipmentType"] == "Skillbike":
        sport = Sport.CYCLING
    elif data["equipmentType"] == "Treadmill":
        sport = Sport.RUNNING
    else:
        return "Unsupported equipment"
    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    dateArray = data["date"].split('/')
    timeArray = data["time"].split(':')
    startDT = datetime(int(dateArray[2]), int(dateArray[0]), int(dateArray[1]), int(timeArray[0]), int(timeArray[1]))

    message = FileIdMessage()
    message.type = FileType.ACTIVITY
    message.manufacturer = Manufacturer.TECHNOGYM.value
    message.product = 0
    message.timeCreated = round(startDT.timestamp() * 1000)
    message.serialNumber = 0x12345678
    builder.add(message)

    start_timestamp = round(startDT.timestamp() * 1000)
    message = EventMessage()
    message.event = Event.TIMER
    message.event_type = EventType.START
    message.timestamp = start_timestamp
    builder.add(message)

    records = []  # track points

    endDT = startDT


    sampleIndex = 0
    hrIndex = 0

    sampleArray = data["analitics"]["samples"]
    hrArray = data["analitics"]["hr"]

    # while sampleIndex < len(sampleArray) or hrIndex < len(hrArray):
    while not((sampleIndex >= len(sampleArray)-1) and (hrIndex >= len(hrArray)-1)):
        if sampleIndex == len(sampleArray):
            sampleIndex -= 1
        if hrIndex == len(hrArray):
            hrIndex -= 1

        sample = sampleArray[sampleIndex]
        sampleTime = sample["t"]
        hr = hrArray[hrIndex]
        hrTime = hr["t"]

        if sampleTime == hrTime or sampleTime < hrTime:
            currentDT = startDT + timedelta(seconds=sample["t"])
            message = createMessage(sport, sample, 0)
            message.heart_rate = hr["hr"]

            sampleIndex += 1
            if sampleTime == hrTime:
                hrIndex += 1
        else:
            currentDT = startDT + timedelta(seconds=hr["t"])
            if sampleIndex > 0:
                sample = sampleArray[sampleIndex-1]
            message = createMessage(sport, sample, hrTime - sample["t"])
            message.heart_rate = hr["hr"]
            hrIndex += 1

        message.timestamp = currentDT.timestamp() * 1000
        endDT = currentDT
        records.append(message)


    builder.add_all(records)
    # stop event
    message = EventMessage()
    message.event = Event.TIMER
    message.eventType = EventType.STOP_ALL
    message.timestamp = endDT.timestamp() * 1000
    builder.add(message)

    generalData = data["data"]

    # Every FIT course file MUST contain a Lap message
    elapsed_time = endDT.timestamp() * 1000 - start_timestamp

    message = SessionMessage()
    message.timestamp = endDT.timestamp() * 1000
    message.start_time = start_timestamp
    message.total_elapsed_time = elapsed_time / 1000
    message.total_timer_time = elapsed_time / 1000
    message.total_distance = generalData[1]["rawValue"] * 1000
    message.total_ascent = totalAscent
    message.total_descent = totalDescent
    message.sport = sport
    builder.add(message)

    message = LapMessage()
    message.timestamp = endDT.timestamp() * 1000
    message.start_time = start_timestamp
    message.total_elapsed_time = elapsed_time / 1000
    message.total_timer_time = elapsed_time / 1000
    message.total_distance = generalData[1]["rawValue"] * 1000
    message.total_ascent = totalAscent
    message.total_descent = totalDescent
    builder.add(message)

    message = ActivityMessage()
    message.sport = sport
    message.num_sessions = 1
    builder.add(message)

    fit_file = builder.build()

    filename = str(uuid.uuid4())
    fit_file.to_file(f'''${filename}.fit''')
    return f'''${filename}.fit'''


if __name__ == '__main__':
    file = open('Details.json')
    jsonData = json.load(file)
    jsonData["data"]["time"] = "13:00"
    convert(jsonData)
    exit(0)
