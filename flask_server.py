"""
Cross-origin MFMCi Server
===================
This is a minimal server for using MFMCi to serve your domain.

:copyright: (C) 2016 by Sean McGregor.
:license:   MIT, see LICENSE for more details.
"""
from flask import Flask, jsonify, request, send_file
from flask.ext.cors import cross_origin
from MFMCi import MFMCi
import importlib
import subprocess
import os
import argparse
import csv

print """
Starting Flask Server...
Note, you may be able to specify a domain at this point by adding it as a
positional argument. For examples: `python flask_server.py wildfire`.

Please Wait (loading database)
"""

parser = argparse.ArgumentParser(description='Start the MFMCi server.')
parser.add_argument('domain', metavar='D', type=str, nargs='?',
                    help='the domain to synthesize trajectories for',
                    default='wildfire')
parser.add_argument('visualize', metavar='V', type=str, nargs='?',
                    help='What we want to visualize. Options include surrogate or errr',
                    default='surrogate')
parser.add_argument('touch', metavar='t', type=str, nargs='?',
                    help='The name of the file to touch',
                    default='server_started')
parser.add_argument('python', metavar='P', type=str, nargs='?',
                    default='python')
args = vars(parser.parse_args())

domain_name = args["domain"]
annotate_module = importlib.import_module("databases." + domain_name + ".annotate")
initialization_object = annotate_module.mdpvis_initialization_object
mfmci = MFMCi(database_path="databases/{}/database.csv".format(domain_name),
              normalization_database="databases/{}/database.csv".format(domain_name),
              possible_actions=annotate_module.POSSIBLE_ACTIONS,
              visualization_variables=annotate_module.VISUALIZATION_VARIABLES,
              pre_transition_variables=annotate_module.PRE_TRANSITION_VARIABLES,
              post_transition_variables=annotate_module.POST_TRANSITION_VARIABLES,
              process_row=annotate_module.PROCESS_ROW,
              non_stationary=True)

policy_module = importlib.import_module("databases.{}.policies".format(domain_name))
policy_factory = policy_module.policy_factory

reward_module = importlib.import_module("databases.{}.rewards".format(domain_name))
reward_factory = reward_module.reward_factory

app = Flask('mfmci', static_folder='.', static_url_path='')

@app.route("/", methods=['GET'])
@cross_origin()
def site_root():
    '''
        This view has CORS enabled for all domains, representing the simplest
        configuration of view-based decoration. You can test this endpoint
        with:

        $ curl --include -X GET http://127.0.0.1:5000/ \
            --header Origin:www.examplesite.com

        Which should return something like:

        >> HTTP/1.0 200 OK
        Content-Type: text/html; charset=utf-8
        Content-Length: 186
        Access-Control-Allow-Origin: www.examplesite.com
        Server: Werkzeug/0.10.4 Python/2.7.9
        Date: Tue, 19 May 2015 17:13:39 GMT

        THE DOCUMENT FOUND BELOW
    '''
    return '''
        <h1>Hello World!</h1>
        <p style='font-size: 150%;'>Your server is running and ready for
        integration.</p>
        <p  style='font-size: 150%;'>To test the other endpoints, visit
          <a href="/initialize">/initialize</a>,
          <a href="/trajectories">/trajectories</a>,
          <a href="/optimize">/optimize</a>, or
          <a href="/state">/state</a>
        '''

@app.route("/initialize", methods=['GET'])
@cross_origin(allow_headers=['Content-Type'])
def cross_origin_initialize():
    '''
        Asks the domain for the parameters to seed the visualization.
    '''
    return jsonify(initialization_object)

def cross_origin_trajectories_error(request):
    '''
        Asks the domain for the trajectories generated by the
        requested parameters.
    '''

    target_quantile = 0.5

    def _get_variable_height(variable_name, mc_trajectories):
        """
        Get the distance in the variable's units that the fan chart will cover.
        :param variable_name:
        :return:
        """
        maximum = float("-Inf")
        minimum = float("Inf")
        for trajectory in mc_trajectories:
            for time_step in trajectory:
                minimum = min(minimum, float(time_step[variable_name]))
                maximum = max(maximum, float(time_step[variable_name]))
        return maximum - minimum

    def _get_quantile(quantile, variable_name, time_step, trajectories):
        """
        :param quantile: float [0,1] for the entry we are looking for.
        :param variable_name: the name of the variable we want the quantile for.
        :param time_step: the time step we want the quantile for.
        :param trajectories: The trajectories we are getting the quantile for.
        :return:
        """
        l = []
        for trajectory in trajectories:
            l.append(float(trajectory[time_step][variable_name]))
        l.sort()
        return l[int(quantile*len(l))]

    def get_objective(mc_trajectories, mfmc_trajectories, variable_name, time_step, heights):

        actual = _get_quantile(target_quantile, variable_name, time_step, mc_trajectories)
        synthesized = _get_quantile(target_quantile, variable_name, time_step, mfmc_trajectories)
        if heights[variable_name] == 0:
            assert abs(actual-synthesized) == 0, "actual: {}, {}, {}, {}, {}".format(abs(actual-synthesized), actual, synthesized, v, t)
            return 0.0
        else:
            return abs(actual-synthesized)/heights[v]

    if int(request.args["Use Location Policy"]) == 1:
        database_path = "databases/wildfire/ground_truth/location_policy.csv"
    elif int(request.args["Use Landscape Policy"]) == 1:
        database_path = "databases/wildfire/ground_truth/fuel_policy.csv"
    else:
        database_path = "databases/wildfire/ground_truth/intensity_policy.csv"

    trajectories = []
    trajectory = []
    with open(database_path, 'rb') as csvfile:
        transitionsReader = csv.DictReader(csvfile)
        transitions = list(transitionsReader)
        for idx, transitionDictionary in enumerate(transitions):

            if int(transitionDictionary["onPolicy"]) == 0:
                continue
            if len(trajectory) > 0:
                assert int(trajectory[-1]["year"]) == int(transitionDictionary["year"]) - 1

            for k in annotate_module.OBJECTIVE_VARIABLES:
                transitionDictionary[k] = float(transitionDictionary[k])
            trajectory.append(transitionDictionary)
            if int(transitionDictionary["year"]) == annotate_module.OBJECTIVE_HORIZON - 1:
                trajectories.append(trajectory)
                trajectory = []
    # get height of each variable
    heights = {}
    for v in annotate_module.OBJECTIVE_VARIABLES:
        heights[v] = _get_variable_height(v, trajectories)

    mfmc_trajectories = mfmci.get_visualization_trajectories(
        count=annotate_module.OBJECTIVE_TRAJECTORY_COUNT, horizon=annotate_module.OBJECTIVE_HORIZON,
        policy=policy_factory(request.args)
    )

    # get the error for each time step and each variables
    ret = []
    for y in range(0, annotate_module.OBJECTIVE_HORIZON):
        cur = {}
        for v in annotate_module.OBJECTIVE_VARIABLES:
            err = get_objective(trajectories, mfmc_trajectories, v, y, heights)
            cur[v] = err
        ret.append(cur)

    #  Standardize the magnitude
    cur = {}
    for v in annotate_module.OBJECTIVE_VARIABLES:
        cur[v] = 1
    ret.append(cur)

    json_obj = {"trajectories": [ret]}
    resp = jsonify(json_obj)
    return resp


def get_monte_carlo_trajectories(request):
    '''
    Get the ground truth trajectories
    :return:
    '''
    if int(request.args["Use Location Policy"]) == 1:
        database_path = "databases/wildfire/ground_truth/location_policy.csv"
    elif int(request.args["Use Landscape Policy"]) == 1:
        database_path = "databases/wildfire/ground_truth/fuel_policy.csv"
    else:
        database_path = "databases/wildfire/ground_truth/intensity_policy.csv"

    print "rendering {}".format(database_path)

    trajectories = []
    trajectory = []
    with open(database_path, 'rb') as csvfile:
        transitionsReader = csv.DictReader(csvfile)
        transitions = list(transitionsReader)
        for idx, transitionDictionary in enumerate(transitions):

            if int(transitionDictionary["onPolicy"]) == 0:
                continue
            annotate_module.PROCESS_ROW(transitionDictionary)
            step = {}
            for k in annotate_module.VISUALIZATION_VARIABLES:
                step[k] = float(transitionDictionary[k])
            trajectory.append(step)
            if int(transitionDictionary["year"]) == annotate_module.OBJECTIVE_HORIZON - 1:
                trajectories.append(trajectory)
                trajectory = []
    return trajectories


def cross_synthesize(request):
    '''
        Asks the domain for the trajectories generated by the
        requested parameters.
    '''
    reward_function = reward_factory(request.args)
    monte_carlo = int(request.args["Render Ground Truth"])
    if monte_carlo:
        json_obj = {"trajectories": get_monte_carlo_trajectories(request)}
    else:
        count = int(request.args["Sample Count"])
        horizon = int(request.args["Horizon"])
        trajectories = mfmci.get_visualization_trajectories(
            count=count, horizon=horizon,
            policy=policy_factory(request.args)
        )
        json_obj = {"trajectories": trajectories}
    resp = jsonify(json_obj)
    return resp

@app.route("/trajectories", methods=['GET'])
@cross_origin(allow_headers=['Content-Type'])
def cross_origin_trajectories():
    '''
        Asks the domain for the trajectories generated by the
        requested parameters.
    '''
    if args["visualize"] == "surrogate":
        return cross_synthesize(request)
    else:
        return cross_origin_trajectories_error(request)

@app.route("/optimize", methods=['POST','GET'])
@cross_origin(allow_headers=['Content-Type'])
def cross_origin_optimize():
    '''
        Asks the domain to optimize the policy using SMAC.
    '''
    count = int(request.args["Sample Count"])
    horizon = int(request.args["Horizon"])
    runs_limit = int(request.args["Number of Runs Limit"])

    rewards_suppression=int(request.args["rewards_suppression"])
    rewards_timber=int(request.args["rewards_timber"])
    rewards_ecology=int(request.args["rewards_ecology"])
    rewards_air=int(request.args["rewards_air"])
    rewards_recreation=int(request.args["rewards_recreation"])

    rungroup = "{}-{}-{}-{}-{}".format(
        str(rewards_suppression),
        str(rewards_timber),
        str(rewards_ecology),
        str(rewards_air),
        str(rewards_recreation))

    annotate_module.write_smac_parameters(request.args)
    subprocess.call(
        ['./smac/smac --use-instances false --numberOfRunsLimit ' + str(runs_limit) + ' --pcs-file smac.pcs --algo "' + args["python"] + ' smac.py -domain ' + domain_name + ' -count ' + str(count) + ' -horizon ' + str(horizon) + " -rewards_suppression " + str(rewards_suppression) + " -rewards_timber " + str(rewards_timber) + " -rewards_ecology " + str(rewards_ecology) + " -rewards_air " + str(rewards_air) + " -rewards_recreation " + str(rewards_recreation) + '" --run-objective QUALITY --rungroup ' + rungroup + ' --seed 1'],
        shell=True)

    directory_listing = os.listdir("smac-output/" + rungroup + "/state-run1/")
    out_file = ""
    for file_name in directory_listing:
        if file_name.find("paramstrings-it") == 0:
            out_file = file_name
            break
    f = open("smac-output/" + rungroup + "/state-run1/" + out_file, "r")
    last_line = ""
    for line in f:
        last_line = line
    f.close()

    # Example last line of file:
    # 5: days='56', erc='17'
    params = {}
    for param in last_line[last_line.index(" ")+1:].split(" "):
        parts = param.split("=")
        params[parts[0]] = int(parts[1].strip("',").strip("',\n"))

    resp = jsonify(annotate_module.post_process_smac_output(params))
    return resp

@app.route("/state", methods=['POST','GET'])
@cross_origin(allow_headers=['Content-Type'])
def cross_origin_state():
    '''
        Asks for the image of a particular state.
    '''
    image_file_name = request.args["image"]
    print "sending %s" % image_file_name
    return send_file(annotate_module.get_image(image_file_name), mimetype='image/jpeg')

# Binds the server to port 8938 and listens to all IP addresses.
if __name__ == "__main__":
    print("Starting server...")
    with open("servers/" + args["touch"], 'w') as touched:
        pass
    app.run(host='0.0.0.0', port=8938, debug=False, use_reloader=False, threaded=True)
    #app.run(host='0.0.0.0', port=8938, debug=True, use_reloader=False, threaded=True)
    print("Server stopped")
