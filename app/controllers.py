from flask_jwt_extended import jwt_required, JWTManager
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import os
from bson.json_util import dumps, loads
from werkzeug.utils import secure_filename
import pathlib
from app import helpers
import logging
from flask import send_from_directory
from flask_cors import CORS

app = Flask(__name__)
app.config.from_envvar('FLASK_CONFIG_FILE')
app.logger.setLevel(logging.DEBUG)
CORS(app)
mongo = PyMongo(app)
jwt = JWTManager(app)


# file_type is either resolution or news-article
# relies on files being stored on host server, same for uploads
@app.route("/api/files/<file_type>/<file_name>", methods=['GET'])
def get_file(file_type, file_name):
    try:
        if file_type == 'resolution':
            return send_from_directory(os.path.join(app.config['RESOLUTION_DIRECTORY']),
                                       mimetype='application/pdf',
                                       filename=file_name)
        elif file_type == 'news-article':
            return send_from_directory(os.path.join(app.config['NEWS_DIRECTORY']),
                                       mimetype='application/pdf',
                                       filename=file_name)
    except Exception:
        app.log_exception(Exception)
        return jsonify({"msg": "Something went wrong"}), 400


# returns all file names for given type, used internally in the admin front-end
@app.route("/api/files/<file_type>/names", methods=['GET'])
@jwt_required
def get_file_names(file_type):
    try:
        if file_type == 'resolution':
            file_list = os.listdir(os.path.join(app.config['RESOLUTION_DIRECTORY']))
            return jsonify(file_list)
        elif file_type == 'news-article':
            file_list = os.listdir(os.path.join(app.config['NEWS_DIRECTORY']))
            return jsonify(file_list)
    except Exception:
        app.log_exception(Exception)
        return jsonify({"msg": "Something went wrong"}), 500


# queryParam resolution=True to change upload directory to the resolutions directory
@app.route("/api/files/upload", methods=['POST'])
@jwt_required
def upload_file():
    if 'file' not in request.files:
        app.logger.info(request)
        return jsonify({"msg": "Not a valid file upload."}), 400
    file = request.files['file']
    if file.filename == '':
        app.logger.info(request)
        return jsonify({"msg": "No file selected for upload."}), 400
    if file and helpers.pdf_file_check(file.filename) and file.content_type == "application/pdf":
        if bool(request.args.get('resolution')) is True:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['RESOLUTION_DIRECTORY'], filename))
            return jsonify({
                "msg": "Resolution saved successfully!",
                "fileName": filename,
                "fileLocation": pathlib.Path(app.config['RESOLUTION_DIRECTORY']).as_uri()
            }), 200
        elif bool(request.args.get('news-article')) is True:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['NEWS_DIRECTORY'], filename))
            return jsonify({
                "msg": "News article saved successfully!",
                "fileName": filename,
                "fileLocation": pathlib.Path(app.config['NEWS_DIRECTORY']).as_uri()
            }), 200
        else:
            app.logger.info(request)
            return jsonify({"msg": "Must either pass ?resolution=true or ?news-article=true as params."}), 400
    else:
        app.logger.info(file.filename)
        return jsonify({"msg": "Selected file extension is not allowed."}), 400


# query-able by title or by committee id, not both yet :)
@app.route("/api/committees", methods=['GET'])
def read_committees():
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


# query-able by title or tags, tags go as ?tags=example&tags=example2 etc
@app.route("/api/newsroom", methods=['GET'])
def read_newsroom():
    title = request.args.get('title')
    tags = request.args.getlist('tags')
    id = request.args.get('id')
    if title:
        news_article = mongo.db.newsroom.find({"title": title})
        article_to_json = dumps(news_article)
    elif tags:
        news_articles = []
        for tag in tags:
            news_article = mongo.db.newsroom.find({'tags': tag})
            news_articles.append(news_article)
        flat_list_of_articles = helpers.flatten(news_articles)
        titles = []
        set_of_articles = []
        for article in flat_list_of_articles:
            if article['title'] not in titles:
                set_of_articles.append(article)
                titles.append(article['title'])
        article_to_json = dumps(set_of_articles)
    elif id:
        news_article = mongo.db.newsroom.find({"id": id})
        article_to_json = dumps(news_article)
    else:
        news_articles = mongo.db.newsroom.find()
        article_to_json = dumps(news_articles)
    return article_to_json


# takes entire JSON object and upserts given mongoDB document with id as query field(IDs change = bad)
# only works with 1 committee at a time ( frontend should submit committee updates from each committee's page
@app.route("/api/committees", methods=['POST', 'PUT'])
@jwt_required
def process_committees():
    if request.method == 'POST':
        return jsonify({"msg": "Only PUT method is implemented at this moment."}), 405
    elif request.method == 'PUT':
        try:
            committee = request.get_json()
            committee_dict = loads(dumps(committee))
            mongo.db.committee.update({'id': committee_dict['id']}, committee_dict, True)
            return jsonify({"msg": "Update successful"}), 200
        except Exception:
            app.log_exception(Exception)
            return jsonify({"msg": "Something went wrong"}), 400


# same rules as method above
@app.route("/api/newsroom", methods=['POST', 'PUT'])
@jwt_required
def process_newsroom():
    if request.method == 'POST':
        return jsonify({"msg": "Only PUT method is implemented at this moment."}), 405
    elif request.method == 'PUT':
        try:
            article = request.get_json()
            article_dict = loads(dumps(article))
            for article in article_dict:
                mongo.db.newsroom.update({'id': article['id']}, article, True)
            return jsonify({"msg": "Update successful"}), 200
        except Exception:
            app.log_exception(Exception)
            return jsonify({"msg": "Something went wrong"}), 400


if __name__ == '__main__':
    app.run(port=5001)
