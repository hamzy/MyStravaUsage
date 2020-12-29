#!/usr/bin/env python3
#
# https://developers.strava.com/
# https://strava.github.io/api/
#
# https://www.strava.com/settings/api
#
# https://groups.google.com/forum/#!forum/strava-api
#
# https://github.com/hozn/stravalib/
#
# https://pythonhosted.org/stravalib/index.html
#
# Step #0 active the python virtual environment
#     python3 -m virtualenv --no-site-packages --distribute venv
#     source venv/bin/activate
#     pip3 install stravalib
#     pip3 install mechanize
#
# Step #1 create a file with your password in it
#     echo -n 'p4ssw0rd' > passfile
#
# Step #2 mandatory the first time, re-export data whenever you need to run this program
#     # Register with Strava at https://www.strava.com/settings/api and receive a clientid and a secret
#     export CLIENTID=your_Client_ID
#     export SECRET=your_Client_Secret
#
# Step #3 run the program
#     ./Strava.py --clientid=${CLIENTID} --secret=${SECRET} --username='hamzy@yahoo.com' --passfile=passfile
#

# To download an activity:
#   original - http://www.strava.com/activities/870974253/export_original
#   TCX      - ihttp://www.strava.com/activities/870974253/export_tcx

# https://strava.github.io/api/v3/streams/

# https://pypi.org/project/stravalib/
# https://github.com/hozn/stravalib

# 0.1 on 2014-12-26
__version__   = "0.1"
__date__      = "2014-12-18"
__author__    = "Mark Hamzy (hamzy@yahoo.com)"

# 0.2 on 2015-09-07
__version__   = "0.2"
__date__      = "2015-09-07"
__author__    = "Mark Hamzy (hamzy@yahoo.com)"

# 0.3 on 2020-12-26
__version__   = "0.3"
__date__      = "2020-12-26"
__author__    = "Mark Hamzy (hamzy@yahoo.com)"

import argparse
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import mechanize
from multiprocessing import Process
import stravalib
import sys
import threading
from urllib import parse

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Strava oauth response</title></head>", "utf-8"))
        self.wfile.write(bytes("<body><p>Nothing to see here, the URL is what you want.</p></body></html>", "utf-8"))

#web_thread = WebThread('localhost', 8282)
#web_thread.start()
#
#class WebThread (threading.Thread):
#    def __init__(self, hostName, port):
#        threading.Thread.__init__(self)
#        self.hostName = hostName
#        self.port = port
#
#    def run(self):
#        webServer = HTTPServer((self.hostName, self.port), MyServer)
#
#        try:
#            webServer.serve_forever()
#        except KeyboardInterrupt:
#            pass
#
#        webServer.server_close()

def run_webserver(hostName, port):
    webServer = HTTPServer((hostName, port), MyServer)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()

if __name__ == "__main__":

    client = stravalib.client.Client ()

    parser = argparse.ArgumentParser(description='Perform Strava queries.')
    parser.add_argument("-i", "--clientid", action="store", type=str, required=True, dest="clientid", help="Client ID")
    parser.add_argument("-p", "--passfile", action="store", type=str, required=True, dest="passfile", help="filename containing password")
    parser.add_argument("-s", "--secret",   action="store", type=str, required=True, dest="secret",   help="Secret")
    parser.add_argument("-u", "--username", action="store", type=str, required=True, dest="username", help="User Name")
    parser.add_argument("-y", "--year",     action="store", type=int,                dest="year",     help="Year",      default=datetime.date.today().year)

    ns = parser.parse_args ()

    fp = open(ns.passfile, "r")
    ns.password = fp.read()
    fp.close()

    # Strava oauth will use your target web server in its reply.  So make sure it is running.
    p = Process(target=run_webserver, args=('localhost', 8282,))
    p.start()

    # Read the unauthenticated web page for the oauth URL.
    br = mechanize.Browser()
    br.set_handle_robots(False)
    authorize_url = client.authorization_url(client_id=ns.clientid, redirect_uri='http://localhost:8282/authorized')
    response1 = br.open(authorize_url)
    br.select_form(nr=0)
    br.form['email'] = ns.username
    br.form['password'] = ns.password
    # The form now has the user/password.  Try again.
    response2 = br.submit()
    # The response URL has the necessary code value.
    # print (br.geturl())
    # http://localhost:8282/authorized?state=&code=f114ae415a3af02c2710409072868752aaf3c39f&scope=read,activity:read
    oauth_dict = parse.parse_qs(parse.urlsplit(br.geturl()).query)
    # {'code': ['f114ae415a3af02c2710409072868752aaf3c39'], 'scope': ['read,activity:read']}
    ns.code = oauth_dict['code']

    # Kill the process running the web server.
    p.terminate()

    # The last step in the oauth protocol.
    access_token = client.exchange_code_for_token(client_id=ns.clientid,
                                                  client_secret=ns.secret,
                                                  code=ns.code)
    print (access_token)

    athlete = client.get_athlete()

#   create_spin_classes(client)

    dtBegin = datetime.datetime (ns.year, 1,  1)
    dtEnd   = datetime.datetime (ns.year, 12, 31)
#   dtBegin = datetime.datetime (ns.year, 5,  25)
#   dtEnd   = datetime.datetime (ns.year, 5,  27)
#   dtBegin = datetime.datetime (ns.year, 12, 22)
#   dtEnd   = datetime.datetime (ns.year, 12, 23)

    activities   = client.get_activities(before=dtEnd, after=dtBegin)
    results      = list(activities)

    bike_rides    = {'distance' : 0.0, 'number': 0}
    rpm_rides     = {'distance' : 0.0, 'number': 0}
    indoor_runs   = {'distance' : 0.0, 'number': 0}
    outdoor_runs  = {'distance' : 0.0, 'number': 0}
    swims         = {'distance' : 0.0, 'number': 0}
    yogas         = {'distance' : 0.0, 'number': 0}

    activity_days = {}

    for activity in results:

        print ("Processing %s" % (activity.name,))

        if activity.calories != None:
            print ("CALORIES: %s", (activity,))

        activity_days[activity.start_date.timetuple().tm_yday] = True

        distance = stravalib.unithelper.miles(activity.distance).num

        if activity.type == 'Ride':
            if activity.gear_id == "b1022230":
                # 'Raleigh Revenio Carbon 2.0'
                activity_map = bike_rides
            elif activity.gear_id == "b1534808":
                # 'RPM/Spin bike'
                activity_map = rpm_rides
            else:
                print("Error: Unknown gear type of '%s'" % (activity.gear_id,), file=sys.stderr)
                continue

        elif activity.type == 'Run' and activity.start_latlng is None:
            activity_map = indoor_runs

        elif activity.type == 'Run' and activity.start_latlng is not None:
            activity_map = outdoor_runs

        elif activity.type == 'Swim':
            activity_map = swims

        elif activity.type == 'Yoga':
            activity_map = yogas

        else:
            print("Error: Unknown activity type of '%s'" % (activity.type,), file=sys.stderr)
            continue

        activity_map['distance'] += distance
        activity_map['number'] += 1

    print ("You have been active for %d days this year" % (len(activity_days),))
    print ("There were %3d RPM classes" % (rpm_rides['number'],))
    print ("There were %3d Yoga classes" % (yogas['number'],))
    print ("There were %3d outdoor bike rides for %f miles" % (bike_rides['number'], bike_rides['distance'],))
    print ("There were %3d elliptical runs    for %f miles" % (indoor_runs['number'],  indoor_runs['distance'],))
    print ("There were %3d outdoor runs       for %f miles" % (outdoor_runs['number'],  outdoor_runs['distance'],))
    print ("There were %3d swims              for %f miles" % (swims['number'], swims['distance'],))

    # (_, num_week, _) = datetime.date.today().isocalendar()

    import pdb
    pdb.set_trace()
