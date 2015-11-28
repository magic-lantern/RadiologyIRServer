from flask import Flask, got_request_exception
from flask_restful import Resource, Api, fields, marshal_with, reqparse
import requests
import xml.etree.ElementTree as etree
import uuid
import pysolr
import re


############################
# Application wide variables
app = Flask(__name__)
app.config['BUNDLE_ERRORS'] = True
api = Api(app)
url_parameters = ['modality', 'gender', 'indication', 'areaimaged', 'technique', 'comparison', 'findings', 'conclusions']
############################

@app.route('/')
def hello_world():
    return '<html><body>' \
           + '<p>JSON API RESTFUL URL available at <a href="/searchResults">/searchResults</a></p>' \
           + '<p>To test individual backends try:</p>' \
           + '<ul>' \
           + '<li><a href="/yottalook">/yottalook</a> - Yottalook search engine results</li>' \
           + '<li><a href="/solr">/solr</a> - Solr search engine results</li>' \
           + '</ul>' \
           + '</body></html>'

def log_exception(sender, exception, **extra):
    """ Log an exception to our logging framework """
    sender.logger.debug('Got exception during processing: %s', exception)
    for name, value in extra.items():
        sender.logger.debug('{0} = {1}'.format(name, value))

got_request_exception.connect(log_exception, app)

searchResults_fields = {
    'id' : fields.Integer(default=0),
    'resultID' : fields.Integer,
    'imageLink' : fields.String(default=''),
    'source' : fields.String(default=''),
    'resultTitle' : fields.String(default=''),
    'linkTitle' : fields.String(default=''),
    'articleLink' : fields.String(default=''),
    'figsonlyLink' : fields.String(default=''),
    'content' : fields.String(default=''),
    'modality' : fields.String(default=''),
    'date' : fields.String(default=''),
}


class yottalookSearch(Resource):

    def xml_to_dict(xmlstr):
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
            document = {}

            # map XML value to dictionary object - could use XML elements directly, but plan to change output
            # format eventually, so this will be needed soon
            document['id'] = uuid.uuid5(uuid.NAMESPACE_URL, val.find('FullFigureLink').text).int
            document['resultID'] = val.find('ResultID').text
            document['imageLink'] = val.find('ThumbLocalLink').text
            document['source'] = val.find('Source').text
            document['resultTitle'] = val.find('Caption').text
            document['linkTitle'] = val.find('ArticleTitle').text
            document['articleLink'] = val.find('ArticleLink').text
            document['figsonlyLink'] = val.find('FigsonlyLink').text
            document['content'] = val.find('Caption').text
            document['modality'] = val.find('ImageType').text
            document['date'] = val.find('Date').text

            retval.append(document)

        return retval

    def search():
        # get request parameters
        get_parser = reqparse.RequestParser()
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
        # modality is a special case, so skip it and handle later
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

            return yottalookSearch.xml_to_dict(r)

    @marshal_with(searchResults_fields, envelope='searchResults')
    def get(self):
        return yottalookSearch.search()

api.add_resource(yottalookSearch, '/yottalook' )


class solrSearch(Resource):

    def search():
        # get request parameters
        get_parser = reqparse.RequestParser()
        solrquery = ''
        retval = []

        for u in url_parameters:
            get_parser.add_argument(
                u,
                dest = u,
                help = 'Text from ' + u + ' field',
            )
        args = get_parser.parse_args()

        # handle the special cases
        modality = args['modality']
        if modality != None and modality != 'all':
            if modality == 'XR':
                solrquery = 'content:"modality conventional radiograph"~3 AND '
            elif modality == 'NM':
                solrquery = 'content:"modality nuc med"~7 OR content:"Nuclear Medicine" AND '
            else:
                solrquery = 'content:"modality ' + modality + '"~7 AND '

        gender = args['gender']
        if gender != None:
            if gender == 'female':
                solrquery = 'content:"patient: female"~7 AND '
            elif gender == 'male':
                solrquery = 'content:"patient: male"~7 AND '

        # handle remaining cases
        for u in url_parameters[2:]:
            if args[u] != None:
                solrquery += 'content:"' + args[u] + '" AND '
        if solrquery.endswith(' AND '):
            solrquery = solrquery[:-5]

        # Setup a Solr instance.
        solr = pysolr.Solr('http://localhost:8983/solr/mypacs')

        # sample SOLR result
        # {
        #     'date':'2012-04-27T15:58:26Z',
        #     'boost':0.0,
        #     'lastModified':'2012-04-27T15:58:26Z',
        #     'url':'http://www.mypacs.net/cases/220339.html',
        #     'contentLength':'6876',
        #     'digest':'85dd4d2462da0ffecabe5ca711621cb4',
        #     'title':[
        #         'ANKLE PAIN FOLLOWING TRAUMA'
        #     ],
        #     'tstamp':'2015-12-20T04:54:49.803Z',
        #     'id':'net.mypacs.www:http/cases/220339.html',
        #     'content':'ANKLE PAIN FOLLOWING TRAUMA MyPACS.net: Radiology Teaching Files > Case 220339 \xa0 ANKLE PAIN FOLLOWING TRAUMA Contributed by: Lee Hoagland, Radiologist, University of Wisconsin, Madison, Wisconsin, USA. Patient: female History: Fall. Images: [small] larger Fig. 1: Axial CT through the distal tibia. Fig. 2: Sagittal CT reconstruction of the ankle. Fig. 3: Coronal CT reconstruction of the distal tibia. Findings: Fracture of the distal tibial epiphysis extending into the physis with widening of the lateral aspect of the growth plate. The medial portion of the physis is fused. Diagnosis: Juvenile Tillaux Fracture Comments: Nice case, Lee. Welcome to the club. -- Dean Thornton , 2003-11-13 Additional Details: Case Number: 220339 Last Updated: 2011-09-24 Anatomy: Skeletal System\xa0\xa0\xa0 Pathology: Trauma Modality: CT Access Level: Readable by all users The reader is fully responsible for confirming the accuracy of this content. Text and images may be copyrighted by the case author or institution. You can help keep MyPACS tidy: if you notice a case which is not useful (e.g. a test case) or inaccurate, please contact us .',
        #     '_version_':1518338815171756034,
        #     'type':[
        #         'text/html',
        #         'text',
        #         'html'
        #     ]
        # }


        print("solrquery: ", solrquery)
        results = solr.search(solrquery)
        counter = 1
        for result in results:
            document = {}
            document['id'] = uuid.uuid5(uuid.NAMESPACE_URL, result['url']).int
            document['resultID'] = counter
            document['source'] = 'MyPACS'
            document['resultTitle'] = result['title'][0]
            document['linkTitle'] = result['title'][0]
            document['articleLink'] = result['url']
            document['content'] = result['content']

            modality_pattern = re.compile('Modality: (.*) Access Level:')
            modality_result = modality_pattern.search(result['content'])
            if modality_result:
                document['modality'] = modality_result.groups()[0]
            else:
                document['modality'] = "See Article"

            lastupdated_pattern = re.compile('Last Updated: (\d{4}-\d{2}-\d{2})')
            lastupdated_result = lastupdated_pattern.search(result['content'])
            if lastupdated_result:
                document['date'] = lastupdated_result.groups()[0]

            counter += 1
            retval.append(document)

        # total number of matches found (will only see the first 10)
        print("    Total Solr results found: ", results.hits)

        if retval:
            return retval
        else:
            return {}

    @marshal_with(searchResults_fields, envelope='searchResults')
    def get(self):
        return solrSearch.search()



api.add_resource(solrSearch, '/solr' )


class searchResults(Resource):


    @marshal_with(searchResults_fields, envelope='searchResults')
    def get(self):
        # call yottalookSearch
        yr = yottalookSearch.search()

        # call solrSearch
        sr = solrSearch.search()

        if yr:
            print("Yottalook returned results")
        if sr:
            print("Solr returned restults")


        # combine results and return
        return yr + sr

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
