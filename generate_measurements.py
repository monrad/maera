import requests
import time
import datetime
import argparse
from configobj import ConfigObj
from ripe.atlas.cousteau import (
    Ping,
    AtlasSource,
    AtlasCreateRequest
)

config = ConfigObj("maera.conf")

# set current time:
now = datetime.datetime.now()

parser = argparse.ArgumentParser(description="Generate Atlas measurements")
parser.add_argument("--target", "-t", help="Target to ping", required=True)
parser.add_argument("--addressfamily", "-a",
                    help="Address Family to use, default is 4",
                    type=int, choices=[4, 6],
                    default=4)
parser.add_argument("--numberofpkts", "-",
                    help="Number of packets to send default is 16",
                    type=int, choices=range(1, 17), default=16)
parser.add_argument("--public", help="Set to make public measurements",
                    action="store_true", default=False)
parser.add_argument("--resolveonprobe", help="Set to resolve DNS on probes",
                    action="store_true", default=False)
parser.add_argument("--filter-asn", help="Filter Probes by ASN")
parser.add_argument("--filter-cc", help="Filter Probes by Country Code")
parser.add_argument("--filter-tags", help="Filter by tags e.g NAT")
args = parser.parse_args()

atlas_download_api_key = config["atlas_download_api_key"]
atlas_create_api_key = config["atlas_create_api_key"]
atlas_site = config["atlas_site"]

filters = ""
if args.addressfamily == 4:
    tags = "&tags=system-ipv4-works"
elif args.addressfamily == 6:
    tags = "&tags=system-ipv6-works"
else:
    raise Warning("Unkown Address Family")

if args.filter_tags:
    tags += "," + args.filter_tags

if args.filter_cc:
    filters += "&country_code=" + args.filter_cc

if args.filter_asn:
    filters += "&asn_v" + str(args.addressfamily) + "=" + args.filter_asn

r = requests.get(atlas_site + "/api/v1/probe/?limit=100&status=1" +
                 tags + filters)
probe_objects = r.json()
all_probes_dict = {}

print "Found " + str(probe_objects["meta"]["total_count"]) + " probes."

# FIXME: Duplicated code from the next while loop, should be made into a fuction.
for probe in probe_objects["objects"]:
	probe_dict = {}
	probe_dict["latitude"] = probe["latitude"]
	probe_dict["longitude"] = probe["longitude"]
	all_probes_dict[probe["id"]] = probe_dict

while probe_objects["meta"]["next"] is not None:
    r = requests.get(atlas_site + probe_objects["meta"]["next"])
    probe_objects = r.json()

    for probe in probe_objects["objects"]:
        probe_dict = {}
        probe_dict["latitude"] = probe["latitude"]
        probe_dict["longitude"] = probe["longitude"]
        all_probes_dict[probe["id"]] = probe_dict

# save probes state
open("data/probe_" + args.target + "_" + now.strftime("%Y%m%dT%H%M") + ".ast",
     "w").write(repr(all_probes_dict))


def chunks(lst, number):
    """Yield successive number-sized chunks from lst."""
    for i in range(0, len(lst), number):
        yield lst[i:i+number]

chunked_probes_list = list(chunks(list(all_probes_dict), 498))

done_measurements = []

ping = Ping(**{
    "af": args.addressfamily,
    "target": args.target,
    # packets is between 1 and 16
    "packets": args.numberofpkts,
    "resolve_on_probe": args.resolveonprobe,
    "is_oneoff": "true",
    "is_public": args.public,
    "description": args.target + " " + now.strftime("%Y%m%dT%H%M")
})

for probes_list in chunked_probes_list:
    stringed_probes_list = [str(x) for x in probes_list]

    source = AtlasSource(**{
        "type": "probes",
        "value": ",".join(stringed_probes_list),
        "requested": str(len(probes_list))
    })

    atlas_request = AtlasCreateRequest(**{
        "key": atlas_create_api_key,
        "measurements": [ping],
        "sources": [source]
    })

    attempts = 0
    while attempts < 5:
        (is_success, response) = atlas_request.create()
        if is_success is True:
            done_measurements.append(response["measurements"][0])
            break
        else:
            if response["ADDITIONAL_MSG"] == '{"error": {"code": 104, "message": "We do not allow more than 10 concurrent measurements to the same target."}}':
                time.sleep(180)
                print "sleeping 180 seconds"
                attempts += 1
            else:
                print done_measurements
                raise Warning(str(response))

open("data/measurements_" + args.target + "_" + now.strftime("%Y%m%dT%H%M") +
     ".ast", "w").write(repr(done_measurements))
