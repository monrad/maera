#!/usr/bin/env python
import requests
import numpy as np
import pyresample as pr
import argparse
from ast import literal_eval
from configobj import ConfigObj
from ripe.atlas.sagan import PingResult

config = ConfigObj('maera.conf')

parser = argparse.ArgumentParser(description="Generate Atlas map")
parser.add_argument("--measurements", "-m", help="Done measurements AST file",
                    required=True)
parser.add_argument("--rtt-upper", "-r", type=int, default=100, required=False,
                    help="Upper boundary for mapping RTT in ms")
args = parser.parse_args()

upper_rtt = args.rtt_upper

measurements_split = args.measurements.split('_')

target = measurements_split[1]
(time, _) = measurements_split[2].split(".")

probes = "probes_" + args.measurements[1] + args.measurements[2]

atlas_download_api_key = config['atlas_download_api_key']
atlas_create_api_key = config['atlas_create_api_key']
atlas_site = config['atlas_site']

all_probes_dict = literal_eval(open("data/" + "probe_" + measurements_split[1]
                                    + "_" + measurements_split[2]).read())
done_measurements = literal_eval(open("data/" + args.measurements).read())

output = []

for measurement in done_measurements:
    r = requests.get(atlas_site + '/api/v1/measurement/' + str(measurement) +
                     '/result/?key=' + atlas_download_api_key)
    for result in r.json():
        result_dict = {}
        # TODO: check for malformed/error in result
        parsed_result = PingResult(result)
        if parsed_result.rtt_min is None:
            result_dict['rtt'] = -1
        else:
            result_dict['rtt'] = parsed_result.rtt_min
        result_dict['latitude'] = all_probes_dict[parsed_result.probe_id]['latitude']
        result_dict['longitude'] = all_probes_dict[parsed_result.probe_id]['longitude']
        output.append(result_dict)

lons = []
lats = []
data = []

for line in output:
    value = float(line['rtt'])
    if value <= 0:
        continue
    if float(line['latitude']) >= 90:
        continue
    lons.append(float(line['longitude']))
    lats.append(float(line['latitude']))
    data.append(value)

lons = np.array(lons)
lats = np.array(lats)
data = np.array(data)
max_idx = (data > upper_rtt)
data[max_idx] = upper_rtt

areas = [
    "pc_world",
    "ortho2_eu",
    "ortho2_na",
    "ortho2_sa",
    "ortho2_africa",
    "ortho2_singa"
    ]
for area in areas:
    area_def = pr.utils.load_area('areas.cfg', area)
    swath_def = pr.geometry.SwathDefinition(lons, lats)

    result = pr.kd_tree.resample_gauss(swath_def,
                                       data,
                                       area_def,
                                       radius_of_influence=300000,
                                       sigmas=pr.utils.fwhm2sigma(300000),
                                       fill_value=None
                                       )
    print "writing output/" + target + "_" + time + \
          area + "_rtt" + str(upper_rtt) + "_map.png"
    pr.plot.save_quicklook("output/" +
                           target +
                           "_" +
                           time +
                           area +
                           "_rtt" +
                           str(upper_rtt) +
                           '_map.png',
                           area_def,
                           result,
                           num_meridians=0,
                           num_parallels=0,
                           label='Latency (ms)')
