#!/usr/bin/python3
#
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
# (if [ -d stravalib ]; then pushd stravalib; git pull; else git clone https://github.com/hozn/stravalib.git && pushd stravalib; fi; git clean -fdx)
#
# INST=false; if [ ! -d env ]; then pip3 install --upgrade virtualenv; python3 -m virtualenv --no-site-packages --distribute env; INST=true; fi; source env/bin/activate; if ${INST}; then pushd stravalib/; python3 setup.py develop; popd; fi; unset INST
#
# Step #1 mandatory the first time, re-export data whenever you need to run this program
#     # Register with Strava at https://www.strava.com/settings/api and receive a clientid and a secret
#     export CLIENTID=your_Client_ID
#     export SECRET=your_Client_Secret
#
# Step #2 mandatory the first time, re-export data whenever you need to run this program
#     # Find out the code= parameter
#     python3 ./Strava.py --authorize --clientid=4030
#     # Run firefox on the outputed URL
#     # Copy the code= parameter on the new URL in the firefox browser
#     export CODE=your_code
#
# To create the variables file:
#     cat << '__EOF__' > variables
#     export CLIENTID=your_Client_ID
#     export SECRET=your_Client_Secret
#     export CODE=your_code
#     __EOF__
#
# To re-export your variables:
#     source variables
#
# To setup your environment:
#     ./configure
#     source env/bin/activate
#
# Step #3
#     # Run the program!
#     python3 ./Strava.py --clientid=${CLIENTID} --secret=${SECRET} --code=${CODE}
#

# 0.1 on 2014-12-26
__version__   = "0.1"
__date__      = "2014-12-18"
__author__    = "Mark Hamzy (hamzy@yahoo.com)"

# 0.2 on 2015-09-07
__version__   = "0.2"
__date__      = "2015-09-07"
__author__    = "Mark Hamzy (hamzy@yahoo.com)"

import sys
import argparse
import stravalib
import datetime
import units

def mondays_in_year (dt):

    list = []
    year = dt.year
    while dt.year == year:
        list.append (dt)
        dt -= datetime.timedelta(days=7)

    return list

def create_spin_classes (client):

    title  = "Monday 5:45 Spin"
    hour   = 17
    minute = 45
    for day in mondays_in_year (datetime.datetime (2014, 5, 12, hour, minute)):

        activity = client.create_activity(title, "Ride", day, 2700, distance=19312.1)
        print ("Creating %s returned activity %s" % (title, activity))

        if activity is not None:
            activity = client.update_activity(activity.id, gear_id="b1534808")
            print ("Adding gear to activity returned %s" % (activity, ))

    import pdb
    pdb.set_trace()

if __name__ == "__main__":

    client = stravalib.client.Client ()

    parser = argparse.ArgumentParser(description='Perform Strava queries.')
    parser.add_argument("-i", "--clientid",  action="store",      type=str,  dest="clientid",  help="Client ID")
    parser.add_argument("-c", "--code",      action="store",      type=str,  dest="code",      help="Code")
    parser.add_argument("-s", "--secret",    action="store",      type=str,  dest="secret",    help="Secret")
    parser.add_argument("-a", "--authorize", action="store_true",            dest="authorize", help="Authorize")
    parser.add_argument("-y", "--year",      action="store",      type=int,  dest="year",      help="Year",      default=datetime.date.today().year)

    ns = parser.parse_args ()

    if ns.authorize:

        if not ns.clientid:
            parser.error ("missing --clientid")

        authorize_url = client.authorization_url(client_id=ns.clientid, redirect_uri="http://localhost/authorized", scope="view_private,write")
        print (authorize_url)
        input("Press Enter to continue...")

    if not ns.clientid or not ns.code or not ns.secret:

        parser.print_help ()
        parser.error ("missing one or more required arguments")

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

    activities = client.get_activities(before=dtEnd, after=dtBegin)
    results    = list(activities)

    bike_rides = {'distance' : 0.0, 'number': 0}
    rpm_rides  = {'distance' : 0.0, 'number': 0}
    runs       = {'distance' : 0.0, 'number': 0}
    swims      = {'distance' : 0.0, 'number': 0}

    for activity in results:

        print ("Processing %s" % (activity.name,))

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

        elif activity.type == 'Run':
            activity_map = runs

        elif activity.type == 'Swim':
            activity_map = swims

        elif activity.type == 'Yoga':
            pass

        else:
            print("Error: Unknown activity type of '%s'" % (activity.type,), file=sys.stderr)
            continue

        activity_map['distance'] += distance
        activity_map['number'] += 1

    print ("There were %d RPM classes" % (rpm_rides['number'],))
    print ("There were %d bike rides for %f miles" % (bike_rides['number'], bike_rides['distance'],))
    print ("There were %d runs       for %f miles" % (runs['number'],  runs['distance'],))
    print ("There were %d swims      for %f miles" % (swims['number'], swims['distance'],))

    # (_, num_week, _) = datetime.date.today().isocalendar()

    import pdb
    pdb.set_trace()
