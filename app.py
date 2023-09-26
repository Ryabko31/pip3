import re
from sysconfig import parse_config_h
from flask import Flask, jsonify, request

from google.protobuf.message import DecodeError
import requests

from helpers.BSSIDApple_pb2 import BSSIDResp
# from google.protobuf.message import DecodeError

app = Flask(__name__)



@app.route('/api/search', methods=['GET'])
def get_hello():
    bssid_param = request.args.get('mac')
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Accept-Charset': 'utf-8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-us',
        'User-Agent': 'locationd/1753.17 CFNetwork/711.1.12 Darwin/14.0.0'
    }
    # bssid_param = "94:08:c7:60:ff:55"
    # Set up the POST data
    data_bssid = f'\x12\x13\n\x11{bssid_param}\x18\x00\x20\01'
    data = '\x00\x01\x00\x05en_US\x00\x13com.apple.locationd\x00\x0a' + '8.1.12B411\x00\x00\x00\x01\x00\x00\x00' + chr(
        len(data_bssid)) + data_bssid
    # Set the endpoint for the request
    endpoint = 'https://gs-loc.apple.com/clls/wloc'
    # Make the HTTP POST request using the requests library
    response = requests.post(
        endpoint,
        headers=headers,
        data=data,
       )
    
    # Parse the binary content of the response into a BSSIDResp protobuf object.
    bssid_response = BSSIDResp()
    try:
        bssid_response.ParseFromString(response.content[10:])
    except DecodeError as e:
        return f'Failed to decode response: {e}'
    lat_match = re.search('lat: (\S*)', str(bssid_response))
    lon_match = re.search('lon: (\S*)', str(bssid_response))
    try:
        # Extract the latitude and longitude values from the response
        lat = lat_match.group(1)
        lon = lon_match.group(1)

        if '18000000000' not in lat:
            # format the latitude and longitude values
            lat = float(lat[:-8] + '.' + lat[-8:])
            lon = float(lon[:-8] + '.' + lon[-8:])
            # create the output dictionary
            data = {
                'module': 'apple',
                'bssid': bssid_param,
                'latitude': lat,
                'longitude': lon
            }
            return data
        else:
            return {
                'module': 'apple',
                'error': 'Latitude or longitude value not found in response'
            }
    except Exception as e:
        if not lat_match or not lon_match:
            # Return the error message in a dictionary
            return {
                'module': 'apple',
                'error': 'Latitude or longitude value not found in response'
            }
        # Return the exception message in a dictionary
        return {
            'module': 'apple',
            'error': str(e)
        }

    
    
    return jsonify(bssid_response.ParseFromString(response.content[10:]))

if __name__ == '__main__':
    app.run(debug=True)
    