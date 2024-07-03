import json
import os

# Test roundtrip conversion for k8s api types in json
def test_json(helpers):
    json_dir = "cbor/test/test_json"
    for root, dirs, files in os.walk(json_dir):
        # Loop through all files in test_json directory
        for file in files:
            # Only consider .json files
            if file.endswith('.json'):
                path = os.path.join(root,file)
                print("Testing " + path)
                f = open(os.path.join(path))
                obj = json.load(f)
                helpers.assert_roundtrip(obj)
                f.close()
