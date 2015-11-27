from flask import Flask, got_request_exception
from flask_restful import Resource, Api, fields, marshal_with, reqparse
import requests
import xml.etree.ElementTree as etree
import uuid
import time

app = Flask(__name__)
app.config['BUNDLE_ERRORS'] = True
api = Api(app)

@app.route('/')
def hello_world():
    return 'Hello World!'

def log_exception(sender, exception, **extra):
    """ Log an exception to our logging framework """
    sender.logger.debug('Got exception during processing: %s', exception)
    for name, value in extra.items():
        sender.logger.debug('{0} = {1}'.format(name, value))

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
    'date' : fields.String(default=''),
    'subscriptionStatus' : fields.String(default='')
}

class searchResults(Resource):

    def xml_to_dict(self, xmlstr):
        # XML Sample result
        #
        # <Figure>
        #   <ResultID>1</ResultID>
        #   <ThumbLocalLink>http://www.yottalook.com/images/thumbnails/small/cf6539a170fe8de1b15f581563580182540bdbf2.jpg</ThumbLocalLink>
        #   <Source>AJR</Source>
        #   <FullFigureLink>http://www.ajronline.org/content/198/3/W217/F5.expansion.html</FullFigureLink>
        #   <ArticleTitle>Review: Inflammatory Pseudotumor: The Great Mimicker</ArticleTitle>
        #   <ArticleLink>http://www.ajronline.org/content/198/3/W217.full</ArticleLink>
        #   <ArticleLinkPDF>http://www.ajronline.org/content/198/3/W217.reprint</ArticleLinkPDF>
        #   <FigsonlyLink>http://www.ajronline.org/content/198/3/W217.figsonly</FigsonlyLink>
        #   <Caption>Fig. 4A —14-year-old girl with history of asthma. A,Axial (A)...</Caption>
        #   <ImageType>CT</ImageType>
        #   <Date>2012-03-01</Date>
        #   <SubscriptionStatus>n</SubscriptionStatus>
        # </Figure>
        #
        root = etree.fromstring(xmlstr)
        retval = []

        # # some exmples for parsing the xml string
        # # YottalookWS
        # print("root : ", root.findall("."))
        # # YottalookImages
        # print("root[0] : ", root[0].findall("."))
        # # results
        # print("root[0][1] : ", root[0][1].findall("."))
        # # first figure (first result)
        # print("root[0][1][0] : ", root[0][1][0].findall("."))
        # # get all figure elements
        # print("root .//Figure: ", root.findall(".//Figure"))
        #

        for idx, val in enumerate(root.findall('.//Figure')):
            figure = {}

            # map XML value to dictionary object - could use XML elements directly, but plan to change output
            # format eventually, so this will be needed soon
            figure['id'] = uuid.uuid5(uuid.NAMESPACE_URL, val.find('FullFigureLink').text).int
            figure['resultID'] = val.find('ResultID').text
            figure['thumbLocalLink'] = val.find('ThumbLocalLink').text
            figure['source'] = val.find('Source').text
            figure['fullFigureLink'] = val.find('FullFigureLink').text
            figure['articleTitle'] = val.find('ArticleTitle').text
            figure['articleLink'] = val.find('ArticleLink').text
            figure['articleLinkPDF'] = val.find('ArticleLinkPDF').text
            figure['figsonlyLink'] = val.find('FigsonlyLink').text
            figure['caption'] = val.find('Caption').text
            figure['imageType'] = val.find('ImageType').text
            figure['date'] = val.find('Date').text
            figure['subscriptionStatus'] = val.find('SubscriptionStatus').text

            retval.append(figure)

        return retval



    @marshal_with(searchResults_fields, envelope='searchResults')
    def get(self):
        # get request parameters
        get_parser = reqparse.RequestParser()
        url_parameters = ['modality', 'indication', 'areaimaged', 'technique', 'comparison', 'findings', 'conclusions']
        for u in url_parameters:
            get_parser.add_argument(
                u,
                dest = u,
                help = 'Text from ' + u + ' field',
            )
        args = get_parser.parse_args()

        # build the parameterized URL for Yottalook
        yottalook_url = 'http://www.yottalook.com/api_images_2_0.php'
        query_terms = ''
        for u in url_parameters[1:]:
            if args[u] != None:
                if " " in args[u]:
                    query_terms += '"' + args[u] + '"+'
                else:
                    query_terms += args[u] + '+'
        if query_terms.endswith('+'):
            query_terms = query_terms[:-1]

        yottalook_url += '?q=' + query_terms

        # due to needing to customize query_terms, not including it as part of params dictionary
        payload = {
            'app_id' : '4b94305d853d3e7c91ed4774aa428f75',
            'mod'    : args.modality,
            'cl'     : 50,
        }

        prepared = requests.Request(url=yottalook_url).prepare()
        prepared.prepare_url(prepared.url, payload)
        #&t=yy required to be at the end of the URL
        prepared.prepare_url(prepared.url, {'t' : 'yy'})

        resp = requests.get(prepared.url)
        print("    DEBUG URL : " + resp.url)

        if resp.status_code != 200:
            # This means something went wrong.
            print('GET YOTTALOOK returned status code: ', resp.status_code)
            return {}
        else:
            r = resp.text
            r = r.split('\n', 1)[-1]

            return self.xml_to_dict(r)

api.add_resource(searchResults, '/searchResults' )

# these response headers allow for client side code to request resources
@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
  return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
