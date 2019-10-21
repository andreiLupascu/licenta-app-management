from flask_jwt_extended import jwt_required
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import os
from bson.json_util import dumps, loads
from werkzeug.utils import secure_filename
import uuid
from app import helpers

app = Flask(__name__)

UPLOAD_DIRECTORY = 'C:\\Users\\ANDREI\\Desktop\\est'
RESOLUTION_DIRECTORY = 'C:\\Users\\ANDREI\\Desktop\\rest'
# TODO ASTEA NU AICI

app.config['MONGO_URI'] = os.getenv('APP_MONGODB_URI')
app.config['JWT_SECRET_KEY'] = os.getenv('APP_SECRET_KEY')
app.config['UPLOAD_DIRECTORY'] = UPLOAD_DIRECTORY
app.config['RESOLUTION_DIRECTORY'] = RESOLUTION_DIRECTORY

mongo = PyMongo(app)


# queryParam resolution=True to change filename to random UUID
# TODO move to Commons module/ leave committee module just for committees
@app.route("/upload", methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in request."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "No file selected for upload."}), 400
    if file and helpers.pdf_file_check(file.filename):
        if bool(request.args.get('resolution')) is True:
            filename = secure_filename(str(uuid.uuid4())+".pdf")
            # TODO replace old UUID-named file with new one on each upload (clear directory?/ save UUID with topic name
            file.save(os.path.join(app.config['RESOLUTION_DIRECTORY'], filename))
            return jsonify({
                "msg": "Resolution saved successfully!",
                "fileName": filename
            }), 200
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_DIRECTORY'], filename))
            return jsonify({"msg": f"File {filename} saved successfully!"}), 200
    else:
        print(file.filename)
        return jsonify({"msg": "Selected file extension is not allowed."}), 400


@app.route("/committees", methods=['GET'])
def committees():
    title = request.args.get('title')
    if title == "":
        online_users = mongo.db.committee.find()
        users = dumps(online_users)
    else:
        online_users = mongo.db.committee.find_one({"title": title})
        users = dumps(online_users)
    return users


if __name__ == '__main__':
    app.run()
