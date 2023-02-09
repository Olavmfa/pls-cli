# Import required modules
import requests
import json
import argparse

#####################################################################################
############################## DEFINE HELP FUNCTIONS ################################
#####################################################################################

# Send a request
def send_request(base_url, action: str, pnum:str = None):
    url = base_url + action
    if pnum != None:
        url = url + "/" + pnum
    response = requests.get(url=url)
    return response

# Print a response directly as json representation
def print_basic_response(response:requests.Response):
    res = response.json()
    print("")
    print(json.dumps(res, indent=4))
    print("")

# Extract action information from response
def _find_action(response:requests.Response):
    actions = ["isvalid", "isregistered", "gender", "age", "listall", "listbygroups"]
    url = response.url
    action = ""
    for a in actions:
        if a in url:
            action = a
            break
    return action

# Extract personal number information from response
def _find_pnum(response:requests.Response):
    url = response.url
    url_list = url.split("/")
    if len(url_list) == 6:
        return url_list[-1].strip()
    return None

# Print response in a more readable formate than direct json output
def prettyprint_response(response:requests.Response):
    action = _find_action(response)
    res = response.json()
    if action == "listall":
        print("Following is a list of the amount of all personal numbers registered in the data set. \n")
        print("The list includes all personal numbers, valid personal numbers, invalid personal numbers\nand the amount of men and women (given valid personal numbers):\n")
        print_basic_response(response)
    elif action == "listbygroups":
        print("Following is a list of the amount of personal numbers registered in the data set.")
        print("The list is grouped by age groups of 10 years, and further by gender: \n")
        print_basic_response(response)
    else: 
        output = "The request treated personal number " + res["pnum"] + ".\n"
        if action in ["gender", "age"]:
            output += "The personal number is of " + action + " '" + res[action] + "'."
        elif action == "isvalid":
            result = res["is valid pnum"]
            output += "The personal number is" + (" not " if result == "no" else " " )+ "valid."
            if result == "no":
                output += "\nReason: "
                output += res["reason"]
        elif action == "isregistered":
            result = res["is in dataset"]
            output += "The personal number is" + (" not " if result == "no" else " ") + "registered."
            if res["is valid pnum"] == "no":
                output += "\nNotice that the pnum provided is invalid."
        print(output)
        print("")

# Save response to a json file
def save_response(response:requests.Response):
    action = _find_action(response)
    pnum = _find_pnum(response)
    filename = "response_" + action
    if pnum != None:
        filename += "_"+pnum
    filename += ".json"
    rjson = response.json()
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(rjson, f, ensure_ascii=False, indent=4)
    return filename

#####################################################################################
################################# DEFINE CLI LOGIC ##################################
#####################################################################################

# Create a parser
parser = argparse.ArgumentParser(
    prog="pls",
    description="Personal number Lookup Service. Access information concerning registered or specific personal numbers.",
    epilog="Contact abc@def.ijk for further help.",
    )

# Add arguments for desired action, and optional arguments for personal number input, saving the response 
# and providing a more detailed output to user
parser.add_argument("action", choices=["isvalid", "isregistered", "gender", "age", "listall", "listbygroups"])
parser.add_argument("-p", "--pnum", metavar='', help="\t\tpersonal number for lookup")
parser.add_argument("-s", "--save", action="store_true", help="save response to json file")
parser.add_argument("-v", "--verbose", action="store_true", help="print detailed output")
args = parser.parse_args()

# Check if user provided the required personal number for certain actions
if args.action in ["gender", "age", "isregistered", "isvalid"]:
    if not args.pnum:
        print("Action '" + args.action + "' requires a personal number.")
        print("Use optional argument '-p', '--pnum' followed by a personal number.")
        raise SystemExit(2)

# Check if user provided personal number to a function taking no input
else:
    if args.pnum:
        print("Action '" + args.action + "' cannot be used with optional argument '-p', '--pnum'.")
        raise SystemExit(2)

# Define base url to access endpoints
base_url = "http://0.0.0.0:5000/pnums/"

# Send request to correct endpoint
if args.pnum:
    if args.verbose:
        print("\nSending request with action '" + args.action + "' and pnum '" + args.pnum + "'.")
    response = send_request(base_url=base_url, action=args.action, pnum=args.pnum)
else:
    if args.verbose:
        print("\nSending request with action '" + args.action + "'.")
    response = send_request(base_url=base_url, action=args.action)

# Check successful request
if response.status_code != 200:
    if args.verbose:
        print("Unsuccessful request with status code ", response.status_code)
        print("Error message: ")
        if "Error message" in response.json():
            error = response.json().get("Error message")
            print(error)
    else:
        print("Bad request", response.status_code)
    raise SystemExit(1)

# Print response if verbose flag activated
if args.verbose:
    print("\nResponse received.")
    print("\nPrinting response in readable format:\n")
    prettyprint_response(response=response)

# Save response if save flag activted
if args.save:
    if args.verbose:
        print("\nSaving response to json...")
    filename = save_response(response=response)
    if args.verbose:
        print("Response saved to " + filename)

# Print direct json response if verbose flag not activated
if not args.verbose:
    print_basic_response(response)