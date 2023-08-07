# ID: z5405329
# Name: Puquan Chen

import pandas as pd
from flask import Flask
from flask import request
from flask_restx import Resource, Api
from flask_restx import fields
import sqlite3
from datetime import datetime
import requests
import json
import pandas as pd
from flask_restx import reqparse
import time
import matplotlib.pyplot as plt
from flask import send_file
import geopandas as gpd
import matplotlib
import re

matplotlib.use('agg')
plt.switch_backend('Agg')



app = Flask(__name__)
api = Api(app,
          default="Calendar",
          title="REST API MyCalender",
          description="This is a Flask-RestX API for calender service, users can add event for a specific date, check weather for a date and retrieve events information from database.",)


error_model = api.model('error', {
    "message": fields.String(description="Error message")
})

href_model = api.model('href', {
    "herf": fields.String("/event/[link]", description="href link of the event")
})



CreateEvent_model = api.model('Event Creation return', {
    "id": fields.Integer("[id]", description="unique Event ID in the database"),
    "last-update": fields.FormattedString("YYYY-MM-DD HH:mm:SS", description="latest update time of the event"),
    "_links": fields.Nested(api.model('Event href link self',{
        'self' : fields.Nested(href_model)
    })) 
})

DeleteEvent_model = api.model('Delete Event return', {
    "message": fields.String("The event with id [id] was removed from the database!"),
    "id": fields.Integer("[id]", description="unique Event ID in the database"),
})


Statistic_model = api.model("Statistic report", {
    "total": fields.Integer(description="total number of events in the database"),
    "total-current-week": fields.Integer(description="total number of events in the current week"),
    "total-current-month": fields.Integer(description="total number of events in the current month"),
    "per-days": fields.Nested(api.model("per-days", {
        "[key]:": fields.Integer(description="total number of events in the spepcific")})),
})


Update_model = api.model("Event update return", {
    "id": fields.Integer(description="unique Event ID in the database"),
    "last-update": fields.FormattedString("YYYY-MM-DD HH:mm:SS", description="latest update time of the event"),
    "_links": fields.Nested(api.model('Event href link self',{
        'self' : fields.Nested(href_model)
    }))
})

Update_model_input = api.model("Event update Input", {
    "from": fields.FormattedString("HH:mm:SS", description="event start time, format: hh:mm:ss, the start time should be earlier than the end time"),
    "to": fields.FormattedString("HH:mm:SS", description="event end time, format: hh:mm:ss, the end time should be later than the start time"),
    "description": fields.String,
    "name": fields.String,
    "date": fields.FormattedString("DD-MM-YYYY", description="event date, format: DD-MM-YYYY"),
    "street": fields.String,
    "suburb": fields.String,
    "state": fields.String,
    "post-code": fields.String
})


event_model = api.model('Event', {
    "name": fields.String(description="Event name", required=True),
    "date": fields.FormattedString("DD-MM-YYYY", description="event date, format: DD-MM-YYYY", required=True),
    "from": fields.FormattedString("HH:mm:SS", description="event start time, format: hh:mm:ss, the start time should be earlier than the end time", required=True),
    "to": fields.FormattedString("HH:mm:SS", description="event end time, format: hh:mm:ss, the end time should be later than the start time", required=True),
    "location": fields.Nested(api.model('location', {
        "street": fields.String(description="street name", required=True), 
        "suburb": fields.String(description="suburb name, the suburb name is used for weather forecast and location check function", required=True), 
        "state": fields.String(description="state name", required=True),
        "post-code": fields.String(description="post code", required=True),
    })),
    "description": fields.String(description="event description", required=True), 
})

event_list_model = api.model('Event List', {
    "page": fields.Integer(description="page number"),
    "page-size": fields.Integer(description="page size"),
    "events": fields.List(fields.Nested(event_model)),
    "_links": fields.Nested(api.model('Event list href link self',{
        "self" : fields.Nested(href_model),
        "next" : fields.Nested(href_model),
    }))
})


conn = sqlite3.connect('z5405329.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, name varchar, date varchar, start varchar, end varchar, street varchar, suburb varchar, state varchar, postcode varchar, description varchar, updated_at varchar)")



# parser configuration for each api
statistic_parser = reqparse.RequestParser()
statistic_parser.add_argument("format", type=str, required=True, choices=(
    'json', 'image'), help="Format of statistic report, can be json or image")


weatherMap_parser = reqparse.RequestParser()
weatherMap_parser.add_argument("date", type=str, required=True, help="you must input the date to show the weather forecast.")

retrieve_parser = reqparse.RequestParser()
retrieve_parser.add_argument('order', type=str, default="+id", help="order is a comma separated string value to sort the list based on the given criteria. \n"
                             "string should have two part, first part: '+'/'-', where + indicates ordering ascendingly, and - indicates descendingly. \n"
                             "The second part is an attribute name which is one of {id,name, datetime}")
retrieve_parser.add_argument(
    'page', type=int, default=1, help="Enter the page number")
retrieve_parser.add_argument(
    'size', type=int, default=10, help="Enter the size")
retrieve_parser.add_argument('filter', type=str, default="id,name", help="filter is a comma separated values\n"
                             "which is in {id, name, date, from, to, and location}\n")



# helper function
def get_currentTime():
    return datetime.now().strftime("%Y-%d-%m %H:%M:%S")

def get_now():
    return int(round(time.time()))

def get_holidayName(year, country_code, date):
    r = requests.get(
        "https://date.nager.at/api/v2/publicholidays/{}/{}".format(year, country_code))
    json_data = json.loads(r.content.decode("utf-8"))
    temp = date.split("-")
    format_date = temp[2] + '-' + temp[1] + '-' + temp[0]
    for i in json_data:
        data_date = i["date"]
        if format_date == data_date:
            return i['localName']
    return "None"


def getPosition(suburbName):
    try:
        df = pd.read_csv("georef-australia-state-suburb.csv", sep=";")
        list = df[df['Official Name Suburb'] ==
                  suburbName]["Geo Point"].tolist()
        lat = list[0].split(", ")[0]
        lng = list[0].split(", ")[1]
        return lat, lng
    except:
        return None
    

def getTimepoint(date):
    current_time = datetime.now().strftime("%d-%m-%Y")
    day_diff = abs(datetime.strptime(date, "%d-%m-%Y") -
                   datetime.strptime(current_time, "%d-%m-%Y")).days
    if int(day_diff) <= 7:
        timepoint = 3 + day_diff * 24
        return timepoint
    else:
        return None
    
    
def getWeather(lat, lng, date, product="civil", output="json", unit="metric",):
    param = dict(lon=lng, lat=lat, product=product, output=output, unit=unit)
    timepoint = getTimepoint(date)
    if timepoint:
        r = requests.get("http://www.7timer.info/bin/api.pl", params=param)
        respond = r.json()
        wether_data = respond.get("dataseries", [])
        data = {}
        for i in wether_data:
            if i['timepoint'] == timepoint:
                data["wind-speed"] = str(i['wind10m']['speed']) + ' KM'
                data["weather"] = i['weather'][:-3]
                data["humidity"] = i['rh2m']
                data["temperture"] = str(i['temp2m'])
        return data
    else:
        return None


def checkWeekend(date):
    date = datetime.strptime(date, "%d-%m-%Y")
    if date.weekday() in [5, 6]:
        return True
    else:
        return False
    
# ref: https://stackoverflow.com/questions/37169362/what-would-be-the-pythonic-way-to-find-out-if-a-given-date-belongs-to-the-curren
def check_sameWeek(date):
    d1 = datetime.strptime(date, '%d-%m-%Y')
    d2 = datetime.today()
    return d1.isocalendar()[1] == d2.isocalendar()[1] \
        and d1.year == d2.year
        

def check_sameMonth(date):
    d1 = datetime.strptime(date, '%d-%m-%Y')
    d2 = datetime.today()
    return d1.month == d2.month \
        and d1.year == d2.year
    
    
def date_parse_py(date):
    return f"{date[6:10]}{date[3:5]}{date[0:2]}"


def addlabels(x,y):
    for i in range(len(x)):
        plt.text(i, y[i], y[i], ha = 'center')
        
def addlabelsGeo(x, y, text):
    for i in range(len(x)):
        plt.text(x[i]-2, y[i] +1 , text[i], ha='left', fontsize=8)

def is_valid_date(date_string):
    # check if the date is in the correct format (dd-mm-yyyy)
    regex = r'^\d{2}-\d{2}-\d{4}$'

    match = re.match(regex, date_string)
    
    if match:
        return True
    else:
        return False
    

def is_valid_time(time_string):
    regex = r'^\d{2}:\d{2}:\d{2}$'
    match = re.match(regex, time_string)
    if match:
        return True
    else:
        return False
    
def is_valid_payload(payload):
    for key in payload.keys():
        if key == "date":
            date = payload[key]
            if is_valid_date(date) == False:
                return False
        elif key == "from":
            time = payload[key]
            if is_valid_time(time) == False:
                return False
        elif key == "to":
            time = payload[key]
            if is_valid_time(time) == False:
                return False

    if "from" in payload.keys() and "to" in payload.keys():
        if payload["from"] > payload["to"]:
            return False
    return True

    

# global variable
date_parse_str = "substr(date, 7, 4) || substr(date, 4, 2) || substr(date, 1, 2)"



@api.route('/events/')
class CreateEvent(Resource):
    @api.expect(event_model, validate=True)
    @api.response(201, "The event was created successfully", CreateEvent_model)
    @api.response(400, 'Invalid input data', error_model)
    @api.doc(description="Create an Event")
    def post(self):
        try: 
            conn = sqlite3.connect('z5405329.db')
            cursor = conn.cursor()
            body = request.json
            
            if not is_valid_payload(body):
                return {"message": "Invalid input data, your input data may in wrong format, please check. date: DD-MM-YYYY, from: HH:MM:SS, to: HH:MM:SS, or An Event start time cannot be after end time, or lack of input elements"}, 400

            name = body['name']
            date = body['date']
            start = body['from']
            end = body['to']
            street = body['location']["street"]
            suburb = body['location']["suburb"]
            state = body['location']["state"]
            postcode = body['location']["post-code"]
            desc = body['description']
            updated_at = get_currentTime()
            cursor.execute(f"select * from events where ({date_parse_str} || ' ' || start) <= ? and ({date_parse_str} || ' ' || end) >= ?",
                        (date_parse_py(date) + " " + end, date_parse_py(date) + " " + start))
            
            record = cursor.fetchone()
            
            if record is not None:
                return {"message": "Event overlaps with another event, please change input data"}, 400
            
            cursor.execute("INSERT INTO events (name, date, start, end, street, suburb, state, postcode, description, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)",
                        (name, date, start, end, street, suburb, state, postcode, desc, updated_at))
            
            return_json = {
                    "id": cursor.lastrowid,
                    "last_updated": updated_at,
                    "_links": {
                        "self": {
                            "href": "/events/{}".format(cursor.lastrowid)
                        }
                    }
            }
            
            conn.commit()
            cursor.close()
            conn.close()        
            return return_json, 201
        
        except Exception as e:
            return {"message": f"Invalid input data format: {str(e)}"}, 400


@api.route('/events/<int:id>')
@api.param('id', 'The id of the event')
class retriveEvent(Resource):
    @api.response(200, "The event was retrived successfully")
    @api.response(404, 'Event not found', error_model)
    @api.response(403, "Validation Error for event attributes", error_model)
    @api.doc(description="retrive an event details by its id")
    
    def get(self, id):
        conn = sqlite3.connect('z5405329.db')
        cursor = conn.cursor()
        cursor.execute(
            'select * from events where events.id == "{}"'.format(id))
        record = cursor.fetchone()
        if record is None:
            cursor.close()
            conn.close()
            return {"message": "Event id {} doesn't exist".format(id)}, 404
        
        holidayName = get_holidayName(record[2][6:], "AU", record[2])
        weekend = checkWeekend(record[2])
        
        position = getPosition(record[6])
        
        if position:
            weather = getWeather(position[0], position[1], record[2])
        else:
            return {"message": "Cannot get position, the suburb name not in the database or in wrong spelling"}, 403
        
        cursor.execute(f"select * from events where ({date_parse_str} || ' ' || end) < ? ", (date_parse_py(record[2]) + " " + record[3],))
        prev = cursor.fetchone()
        cursor.execute(f"select * from events where ({date_parse_str} || ' ' || start) > ? ", (date_parse_py(record[2]) + " " + record[4],))
        next = cursor.fetchone()
        
        if (position and weather):
            return_json = {
                "id": record[0],
                "last_updated": record[10],
                "name": record[1],
                "date": record[2],
                "from": record[3],
                "to": record[4],
                "location": {
                    "street": record[5],
                    "suburb": record[6],
                    "state": record[7],
                    "postcode": record[8],
                },
                "description": record[9],
                "_metadata": {
                    "wind-speed": weather["wind-speed"],
                    "weather": weather["weather"],
                    "humidity": weather["humidity"],
                    "temperture": weather["temperture"],
                    "holiday": holidayName,
                    "weekend": weekend
                },
                "_links": {
                    "self": {
                        "href": "/events/{}".format(id)
                    }
                }
            }
            
        else:
            return_json = return_json = {
                "id": record[0],
                "last_updated": record[10],
                "name": record[1],
                "date": record[2],
                "from": record[3],
                "to": record[4],
                "location": {
                    "street": record[5],
                    "suburb": record[6],
                    "state": record[7],
                    "postcode": record[8],
                },
                "description": record[9],
                "_metadata": {
                    "wind-speed": "None",
                    "weather": "None",
                    "humidity": "None",
                    "temperture": "None",
                    "holiday": holidayName,
                    "weekend": weekend
                },
                "_links": {
                    "self": {
                        "href": "/events/{}".format(id)
                    }
                }
            }
        if prev is not None:
            return_json["_links"]["previous"] = {
                "href": "/events/{}".format(prev[0])
            }
        if next is not None:
            return_json["_links"]["next"] = {
                "href": "/events/{}".format(next[0])
            }
        cursor.close()
        conn.close()
        return return_json, 200
    
    # delete event by id
    @api.response(404, 'Event was not found', error_model)
    @api.response(200, 'Successful', DeleteEvent_model)
    @api.doc(description="Delete a event by its ID")
    def delete(self, id):
        conn = sqlite3.connect('z5405329.db')
        cursor = conn.cursor()
        cursor.execute('select * from events where events.id == "{}"'.format(id))
        record = cursor.fetchone()
        
        if record is None:
            cursor.close()
            conn.close()
            return {"message": "Event id {} doesn't exist".format(id)}, 404
        
        
        cursor.execute('delete from events where events.id == "{}"'.format(id))        
        conn.commit()
        cursor.close()
        conn.close()
        return_message = {
            "message": "The event with id {} was removed from the database!".format(id),
            "id": id,
        }
        
        return return_message, 200
    
    # update an event
    @api.expect(Update_model_input, validate=True)
    @api.response(200, 'Successful', Update_model)
    @api.response(404, 'Event was not found', error_model)
    @api.response(400, 'Validation error', error_model)
    @api.response(403, 'Input Time range is invalid', error_model)
    @api.doc(description="Update a event by its ID",
             body={'id': 'Event id'},)
    
    def patch(self, id):
        conn = sqlite3.connect('z5405329.db')
        cursor = conn.cursor()
        cursor.execute('select * from events where events.id == "{}"'.format(id))
        record = cursor.fetchone()
        
        if record is None:
            cursor.close()
            conn.close()
            return {"message": "Event id {} does not exist".format(id)}, 404
        
        body = request.json
        
        if is_valid_payload(body) == False:
            return {"message": "Invalid payload, some values are not in correct format"}, 400
        
        
        validKey_list = ["name", "date", "from", "to", "street", "suburb", "state", "post-code", "description"]
        
        bodyKey_list = list(body.keys())
        
        keyColumn_map = {
            "name": "name",
            "date": "date",
            "from": "start",
            "to": "end",
            "street": "street",
            "suburb": "suburb",
            "state": "state",
            "post-code": "postcode",
            "description": "description"
        }
        
        timeStamp_check = {
            "date": record[2],
            "from": record[3],
            "to": record[4]
        }
        
        for key in bodyKey_list:
            if key not in validKey_list:
                cursor.close()
                conn.close()
                return {"message": f"key {key} is not a valid property for updating"}, 400
                #api.abort(400, f"{key} is not a modifiable property.")
            if key == "date":
                timeStamp_check["date"] = body[key]
            if key == "from":
                timeStamp_check["from"] = body[key]
            if key == "to":
                timeStamp_check["to"] = body[key]
                
        cursor.execute(f"select * from events where ({date_parse_str} || ' ' || start) <= ? and ({date_parse_str} || ' ' || end) >= ?",
                       (date_parse_py(timeStamp_check["date"]) + " " + timeStamp_check["to"], date_parse_py(timeStamp_check["date"]) + " " + timeStamp_check["from"]))
        
        record = cursor.fetchone()
        
        
        if timeStamp_check["from"] > timeStamp_check["to"]:
            cursor.close()
            conn.close()
            return {"message": "Event start time is after event end time"}, 403
        
        if record is not None and record[0] != id:
            cursor.close()
            conn.close()
            return {"message": "Event overlaps with another event"}, 403
        
        for key in bodyKey_list:
            cursor.execute(f"update events set {keyColumn_map[key]} = ? where id = ?", (body[key], id))
        
        cursor.execute(f"update events set updated_at = ? where id = ?", (get_currentTime(), id))
        conn.commit()
        
        cursor.execute('select * from events where events.id == "{}"'.format(id))
        record = cursor.fetchone()
        conn.close()
        
        json_return = {
            "id": id,
            "last-update": record[10],
            "_links": {
                "self": {
                    "href": "/events/{}".format(id)
                }
            }
        }
        
        return json_return, 200
        
        
@api.route('/events/statistics')
class Statistic_event(Resource):
    @api.response(200, 'Successfully generate statistics report if format = json, elif format = image, return the generated image)', Statistic_model)
    @api.produces(["image/png"])
    @api.response(400, 'Validation Error', error_model)
    @api.doc(description="Return the statistics of events",
             params={
                 "format": "Format of statistic, can be json or image",
             })
    
    
    def get(self):
        args = statistic_parser.parse_args()
        format = args["format"]
        
        conn = sqlite3.connect('z5405329.db')
        cursor = conn.cursor()
        
        cursor.execute('select * from events')
        record = cursor.fetchall()
        count_total = len(record)
    
        count_currentWeek = 0
        count_currentMonth = 0
        per_day = {}
        
        for i in record:
            date = i[2]
            if check_sameWeek(date):
                count_currentWeek += 1
            if check_sameMonth(date):
                count_currentMonth += 1

        for i in record:
            date = i[2]
            if date not in per_day.keys():
                per_day[date] = 1
            else:
                per_day[date] += 1

        return_json = {
            "total": count_total,
            "total-current-week": count_currentWeek,
            "total-current-month": count_currentMonth,
            "per-days": per_day
        }
        
        
        
        if format == "json":
            return return_json, 200
        
        elif format == "image":
            y = [return_json["total"], return_json["total-current-week"],
                 return_json["total-current-month"]]
            x = ["total event", "current week event", "current month event"]
            plt.figure(figsize=(10, 10))
            plt.subplot(2, 1, 1)
            plt.bar(x, y, width=0.3)
            addlabels(x, y)
            plt.tick_params(axis='x', labelsize=15)
            plt.title("Event Statistics")
            plt.ylabel("Event Count")
            plt.xlabel("Counting Method")
            date = []
            for i in return_json["per-days"].keys():
                date.append([i, return_json["per-days"][i]])

            sorted_list = sorted(
                date, key=lambda t: datetime.strptime(t[0], '%d-%m-%Y'))
            x = []
            y = []
            for i in sorted_list:
                x.append(i[0])
                y.append(i[1])
            plt.subplot(2, 1, 2)
            plt.plot(x, y, linestyle='solid')
            addlabels(x, y)
            plt.title("Event Statistics by Day")
            plt.ylabel("Event Count")
            plt.xlabel("Date")
            plt.tick_params(axis='x', rotation=45, labelsize=8)
            plt.subplots_adjust(left=0.1,
                                bottom=0.1,
                                right=0.9,
                                top=0.9,
                                wspace=0.4,
                                hspace=0.4)
            
            plt.savefig("statistic.png")
            return send_file("statistic.png", mimetype='image/png')
        

@api.route('/weather')
class show_weatherMap(Resource):
    @api.doc(description="Return the statistics of events",
             params={
                 "date": "Date of weather information, format: dd-mm-yyyy, e.g. 01-01-2020, you must input a day within 7 days from today",
             })
    @api.response(200, 'Successfully generate weather map')
    @api.produces(["image/png"])
    @api.response(400, 'Bad Request', error_model)
    @api.response(403, 'Invalid Date Input', error_model)
    def get(self):
        
        args = weatherMap_parser.parse_args()
        date = args["date"]
        
        if is_valid_date(date) == False:
            return {"message": "input date format is invalid"}, 403
            
        df = pd.DataFrame({
            'City': ['Sydney', 'Melbourne', 'Brisbane', 'Adelaide', 'Canberra', 'Darwin', 'Perth', 'Alice Springs', 'Broome', 'Hobart', 'Cairns'],
            'Longitude': [151.2094, 144.9631, 153.0281, 138.6011, 149.1269, 130.8411, 115.8605, 133.8807, 122.2331, 147.3294, 145.7710],
            'Latitude': [-33.865, -37.8136, -27.4678, -34.9289, -35.2931, -12.4381, -31.9522, -23.6980, -17.9561, -42.8821, -16.9186]
        })
    
        weather_infomationStr = []
        for i in range(len(df['City'])):
            api_return = getWeather(df['Latitude'][i], df['Longitude'][i], date)
            if api_return:
                print(api_return)
                weather = api_return['weather']
                temperature = api_return['temperture']
                city = df['City'][i]
                string = "{} \n {} {}".format(city, temperature, weather)
                weather_infomationStr.append(string)
            else:
                return {"message": "You must input a date within 7 days to get weather forecast"}, 403
        
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        australia = world.loc[world['name'] == 'Australia']
        boundaries = australia['geometry']
        base = boundaries.plot()
        # Plot the city points
        gdf.plot(ax=base, marker='o', color='red', markersize=35)
        # add labels to the points (temperature and weather)
        addlabelsGeo(gdf['Longitude'], gdf['Latitude'], weather_infomationStr)
        
        plt.savefig("weather_map.png")
        return send_file("weather_map.png", mimetype='image/png')
        
        

@api.route('/events')        

class RetrieveListEvent(Resource):
    @api.doc(description="Retrieve the list of Events",
             params={
                 'order': "order is a comma separated string value to sort the list based on the given criteria. \n"
                             "string should have two part, first part: '+'/'-', where + indicates ordering ascendingly, and - indicates descendingly. \n"
                             "The second part is an attribute name which is one of {id, name, datetime}, default value is '+id'",
                 'page': "The page number, which is an int, default value is 1",
                 'page_size': "The size of page, min=1, default value is 10",
                 'filter': "filter is a comma separated values\n"
                           "which is one of {id, name, date, from, to, and location}, default value is 'id,name'"
                })
    @api.response(400, 'Validation Error', error_model)
    @api.response(200, 'Successfully retrieve the list of events', event_list_model)
    
    
    def get(self):
        args = retrieve_parser.parse_args()
        #print(args)
        
        
        if "order" not in args:
            args["order"] = "+id"
        if "page" not in args:
            args["page"] = 1
        if "size" not in args:
            args["size"] = 10
        if "filter" not in args:
            args["filter"] = "id,name"
        
        # check the order should be +/- and valid field
        print(args["order"])
        order_clause  = ""
        for x in args["order"].split(","):
            order = 'asc'
            if "+" in x:
                order = 'asc'
            elif "-" in x:
                order = 'desc'
            else:
                return {"message": "order should be +/- and valid field"}, 400
            # check order has valid field
            order_by = x.strip("+").strip("-")
            
            if order_by not in ['id', 'name', 'datetime']:
                return {"message": "order should be +/- and valid field"}, 400
            
            if order_by == "datetime":
                order_by = "strftime(date, '%y-%m-%d')"
            
            # finially format order clause
            order_clause += f'{order_by} {order},'
        
        # remove the extra comma
        order_clause = order_clause[:-1]
        print(order_clause)

        # also check filter has valid field
        filter = ""
        for x in args["filter"].split(","):
            if x not in ['id', 'name', 'date', 'from', 'to', 'location']:
                return {"message": "filter should be one of {id, name, date, from, to, location}"}, 400

            if x == "from":
                filter += '\"start\",'
                continue
            if x == "to":
                filter += '\"end\",'
                continue
            
            # location is a special case
            if x == "location":
                filter += '\"street\",\"suburb\",\"state\",\"post-code\",'
            else:
                filter += f'\"{x}\",'

        # remove the extra comma
        
        filter = filter[:-1]
        #print(filter)

        if not isinstance(args["page"], int) or args["page"] < 1:
            return {"message": "page should be integer that > 1"}, 400
        if not isinstance(args["size"], int) or args["size"] < 1:
            return {"message": "page_size should be integer that > 1"}, 400
        
        # assigne variable
        page = args["page"]
        page_size = args["size"]
        
        conn = sqlite3.connect('z5405329.db')
        cursor = conn.cursor()
        
        print(f'select {filter} from events order by {order_clause} limit {page_size} offset {(page-1)*page_size}')
        cursor.execute(f'select {filter} from events order by {order_clause} limit {page_size} offset {(page-1)*page_size}')
        
        # fetch all the rows from the query
        record = cursor.fetchall()
        # print(record)
        
        # close the connection
        conn.close()

        data = []
        for x in record:
            temp_data = dict(zip(filter.replace('\"', '').split(","), x))
            if "location" in args["filter"].split(","):
                location = {
                    "street": temp_data.pop("street"),
                    "suburb": temp_data.pop("suburb"),
                    "state": temp_data.pop("state"),
                    "post-code": temp_data.pop("post-code"),
                }
                temp_data.update({"location": location})
            data.append(temp_data)

        return_value = {
            'page': page,
            'page_size': page_size,
            'events': data,
            '_links': {
                'self': {
                    'href': f'/events?order={args["order"]}&page={args["page"]}&size={args["size"]}&filter={args["filter"]}'
                },
                'next': {
                    'href': f'/events?order={args["order"]}&page={int(args["page"])+1}&size={args["size"]}&filter={args["filter"]}'
                }
            }
        }

        
        return return_value, 200
            
        
        

if __name__ == '__main__':
    app.run(debug=True, port=8080)