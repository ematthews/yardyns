#!/usr/bin/env python
#
# This utility works when you have a simple A record
# value saved in AWS Route 53 to a domain (zone) that is
# requested.
#
# If the A record has more than one value, then this script
# will likely break your configuration!

import sys
import json
import time
import argparse

from urllib2 import urlopen
from ConfigParser import RawConfigParser
from boto.route53 import connection, record


# Abort the remainder of the script and print error message.
def exit_error(message=None, exit_code=1):
    print("")
    print("ERROR: {message}".format(message=message))
    print(sys.exc_info()[0])
    sys.exit(exit_code)


# Retrieve the IP address from a public site
def what_is_my_ipv4():
    public_ip_url = "http://jsonip.com"
    try:
        ip = json.load(urlopen(public_ip_url))['ip']
    except:
        exit_error("Unable to retrieve public IP address.")

    return ip


def main(
        aws_access_key_id=None,
        aws_secret_access_key=None,
        update_zone=None,
        hostname=None,
        timeout=None,
        ttl=None,
        ip=None,
):
    # If not manually setting an IP address, retrieve from public site
    if ip is None:
        ip4_address = what_is_my_ipv4()
    else:
        ip4_address = ip

    # Connect to AWS Route53
    print("Connecting to Route 53 ......."),
    try:
        conn = connection.Route53Connection(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        print("Done")
    except:
        exit_error("Unable to connect to Route 53 service, check AWS keys.")

    # Retrieve the zone that we wish to update
    print("Retrieving zone .............."),
    try:
        zone = conn.get_zone(update_zone)
        print("Done")
    except:
        exit_error("Unable to retrieve the zone (domain name) {zone}.".format(
            zone=update_zone
        ))

    ip4_hostname = "{hostname}.{zone}".format(
        hostname=hostname,
        zone=update_zone,
    )

    print("Checking if changes made ....."),
    try:
        record = zone.get_a(ip4_hostname)
        configured_ip = record.resource_records[0]
    except:
        exit_error("Unable to retrieve existing A record for {hostname}.".format(
            hostname=ip4_hostname,
        ))

    # Exit cleanly if the IP address has not changed.
    if configured_ip == ip4_address:
        print("IP address not changed.")
        sys.exit(0)
    else:
        print("Done")

    print("IP address changed ........... {hostname} => {ip}".format(
        hostname=ip4_hostname,
        ip=ip4_address,
    ))

    try:
        update = zone.update_a(
            name=ip4_hostname,
            value=ip4_address,
            ttl=ttl,
        )
    except:
        exit_error("Unable to update A record for {record}".format(
            record=ip4_hostname
        ))

    # Wait for confirmation, up to timeout
    print("Waiting for confirmation "),
    start_time = time.time()
    end_time = start_time + timeout

    while True:
        # Skip print command because of extra spaces/newlines
        sys.stdout.write(".")
        sys.stdout.flush()

        # Request updated status from AWS
        update.update()

        # Stop checking when it is no longer pending or we run out of time
        check_time = time.time()
        if update.status != 'PENDING' or check_time >= end_time:
            break
        else:
            time.sleep(2)
    print(" Done")

    # How long did it take to confirm?
    duration = check_time - start_time

    # Confirm that the results are clean
    if update.status == 'INSYNC':
        print("Changes propagated successfully.")
    else:
        exit_error("Changes not confirmed")

if __name__ == "__main__":
    # Require the configuration file to be passed via command line
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config',
        help="Configuration file containing settings.",
        dest="config_file",
        action='store',
    )
    parser.add_argument('-i', '--ip',
        help="Manually configure a specific address.",
        dest="ipv4",
        action='store',
        default=None,
    )

    try:
        args = parser.parse_args()

        # Allow for IP address override via command line
        if args.ipv4 is not None:
            IPv4 = args.ipv4
        else:
            IPv4 = None
    except:
        exit_error("Invalid arguments.")

    # Retrieve the configuration from the file
    try:
        config = RawConfigParser()
        config.read(args.config_file)
    except:
        exit_error("Unable to read configuration file!")

    try:
        UPDATE_TIMEOUT = int(config.get('general', 'UPDATE_TIMEOUT'))
        AWS_ACCESS_KEY_ID = str(config.get('general', 'AWS_ACCESS_KEY_ID'))
        AWS_SECRET_ACCESS_KEY = str(config.get('general', 'AWS_SECRET_ACCESS_KEY'))

        TTL = int(config.get('route53', 'TTL'))
        ZONE = str(config.get('route53', 'ZONE'))
        HOSTNAME = str(config.get('route53', 'HOSTNAME'))
    except:
        exit_error("Missing required values in configuration file")

    main(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        update_zone=ZONE,
        hostname=HOSTNAME,
        timeout=UPDATE_TIMEOUT,
        ttl=TTL,
        ip=IPv4,
    )
