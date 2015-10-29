from flask import Flask
from flask import got_request_exception, jsonify
from flask_restful import Resource, Api, fields, marshal_with

app = Flask(__name__)
api = Api(app)

@app.route('/')
def hello_world():
    return 'Hello World!'

def log_exception(sender, exception, **extra):
    """ Log an exception to our logging framework """
    sender.logger.debug('Got exception during processing: %s', exception)

got_request_exception.connect(log_exception, app)

searchResults_fields = {
    'id' : fields.Integer(default=0),
    'resultID' : fields.Integer,
    'thumbLocalLink' : fields.String(default=''),
    'source' : fields.String(default=''),
    'fullFigureLink' : fields.String(default=''),
    'articleTitle' : fields.String(default=''),
    'articleLink' : fields.String(default=''),
    'articleLinkPDF' : fields.String(default=''),
    'figsonlyLink' : fields.String(default=''),
    'caption' : fields.String(default=''),
    'imageType' : fields.String(default=''),
    'date' : fields.DateTime,
    'subscriptionStatus' : fields.String(default='')
}

class searchResults(Resource):
    @marshal_with(searchResults_fields, envelope='searchResults')
    def get(self):
        retval = {}
        return retval

api.add_resource(searchResults, '/searchResults' )

# these response headers allow for client side code to request resources
@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
  return response

if __name__ == '__main__':
    app.run(debug=True)
