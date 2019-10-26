from flask_jwt_extended import jwt_required, JWTManager
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import os
from bson.json_util import dumps, loads
from werkzeug.utils import secure_filename
import uuid
from app import helpers

app = Flask(__name__)
app.config.from_envvar('FLASK_CONFIG_FILE')

mongo = PyMongo(app)
jwt = JWTManager(app)

# queryParam resolution=True to change upload directory to the resolutions directory
@app.route("/api/files/upload", methods=['POST'])
@jwt_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in request."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "No file selected for upload."}), 400
    if file and helpers.pdf_file_check(file.filename):
        if bool(request.args.get('resolution')) is True:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['RESOLUTION_DIRECTORY'], filename))
            return jsonify({
                "msg": "Resolution saved successfully!",
                "fileName": filename
            }), 200
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['NEWS_DIRECTORY'], filename))
            return jsonify({
                "msg": "News article saved successfully!",
                "fileName": filename
            }), 200
    else:
        print(file.filename)
        return jsonify({"msg": "Selected file extension is not allowed."}), 400

#query-able by title or by committee id, not both yet :)
@app.route("/api/committees", methods=['GET'])
def committees():
    title = request.args.get('title')
    committee_id = request.args.get('id')
    if title:
        committee = mongo.db.committee.find_one({"title": title})
        committee_to_json = dumps(committee)
    elif committee_id:
        committee = mongo.db.committee.find_one({"id": committee_id})
        committee_to_json = dumps(committee)
    else:
        committee = mongo.db.committee.find()
        committee_to_json = dumps(committee)
    return committee_to_json


if __name__ == '__main__':
    app.run(port=5001)
