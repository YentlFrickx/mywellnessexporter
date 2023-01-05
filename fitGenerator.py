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

prev_distance = 0
altitude = 0
totalAscent = 0
totalDescent = 0


class FitActivity:
    def __init__(self, file_path, success):
        self.file_path = file_path
        self.success = success


def create_message(sport, sample, time_diff):
    global altitude
    global prev_distance
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

    distance += speed * time_diff
    elevation_gain = (distance - prev_distance) * (grade / 100)
    prev_distance = distance
    altitude += elevation_gain

    if elevation_gain > 0:
        totalAscent += elevation_gain
    elif elevation_gain < 0:
        totalDescent += elevation_gain

    message.distance = distance
    message.speed = speed
    message.altitude = altitude
    return message


def convert(json_data):
    data = json_data['data']

    if data["equipmentType"] == "Skillbike":
        sport = Sport.CYCLING
    elif data["equipmentType"] == "Treadmill":
        sport = Sport.RUNNING
    else:
        return FitActivity("Unsupported equipment", False)
    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    duration = round(data["data"][0]["rawValue"]*60)
    start_dt = datetime.now() + timedelta(seconds=duration)

    message = FileIdMessage()
    message.type = FileType.ACTIVITY
    message.manufacturer = Manufacturer.TECHNOGYM.value
    message.product = 0
    message.timeCreated = round(start_dt.timestamp() * 1000)
    message.serialNumber = 0x12345678
    builder.add(message)

    start_timestamp = round(start_dt.timestamp() * 1000)
    message = EventMessage()
    message.event = Event.TIMER
    message.event_type = EventType.START
    message.timestamp = start_timestamp
    builder.add(message)

    records = []  # track points

    end_dt = start_dt

    sample_index = 0
    hr_index = 0

    sample_array = data["analitics"]["samples"]

    if 'hr' in data["analitics"]:
        hr_array = data["analitics"]["hr"]
        end_dt = hr_create_records(end_dt, hr_array, hr_index, records, sample_array, sample_index, sport, start_dt)
    else:
        end_dt = create_records(end_dt, records, sample_array, sample_index, sport, start_dt)

    builder.add_all(records)
    # stop event
    message = EventMessage()
    message.event = Event.TIMER
    message.eventType = EventType.STOP_ALL
    message.timestamp = end_dt.timestamp() * 1000
    builder.add(message)

    general_data = data["data"]

    # Every FIT course file MUST contain a Lap message
    elapsed_time = end_dt.timestamp() * 1000 - start_timestamp

    message = SessionMessage()
    message.timestamp = end_dt.timestamp() * 1000
    message.start_time = start_timestamp
    message.total_elapsed_time = elapsed_time / 1000
    message.total_timer_time = elapsed_time / 1000
    message.total_distance = general_data[1]["rawValue"] * 1000
    message.total_ascent = totalAscent
    message.total_descent = totalDescent
    message.sport = sport
    builder.add(message)

    message = LapMessage()
    message.timestamp = end_dt.timestamp() * 1000
    message.start_time = start_timestamp
    message.total_elapsed_time = elapsed_time / 1000
    message.total_timer_time = elapsed_time / 1000
    message.total_distance = general_data[1]["rawValue"] * 1000
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
    return FitActivity(f'''${filename}.fit''', True)


def hr_create_records(end_dt, hr_array, hr_index, records, sample_array, sample_index, sport, start_dt):
    while not ((sample_index >= len(sample_array) - 1) and (hr_index >= len(hr_array) - 1)):
        if sample_index == len(sample_array):
            sample_index -= 1
        if hr_index == len(hr_array):
            hr_index -= 1

        sample = sample_array[sample_index]
        sample_time = sample["t"]
        hr = hr_array[hr_index]
        hrTime = hr["t"]

        if sample_time == hrTime or sample_time < hrTime:
            current_dt = start_dt + timedelta(seconds=sample["t"])
            message = create_message(sport, sample, 0)
            message.heart_rate = hr["hr"]

            sample_index += 1
            if sample_time == hrTime:
                hr_index += 1
        else:
            current_dt = start_dt + timedelta(seconds=hr["t"])
            if sample_index > 0:
                sample = sample_array[sample_index - 1]
            message = create_message(sport, sample, hrTime - sample["t"])
            message.heart_rate = hr["hr"]
            hr_index += 1

        message.timestamp = current_dt.timestamp() * 1000
        end_dt = current_dt
        records.append(message)
    return end_dt

def create_records(end_dt, records, sample_array, sample_index, sport, start_dt):
    while sample_index < len(sample_array):
        sample = sample_array[sample_index]
        sample_time = sample["t"]
        current_dt = start_dt + timedelta(seconds=sample_time)
        message = create_message(sport, sample, 0)

        message.timestamp = current_dt.timestamp() * 1000
        end_dt = current_dt
        records.append(message)
        sample_index += 1
    return end_dt


if __name__ == '__main__':
    file = open('Details.json')
    jsonData = json.load(file)
    jsonData["data"]["time"] = "13:00"
    convert(jsonData)
    exit(0)
