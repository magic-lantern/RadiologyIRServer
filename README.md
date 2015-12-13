# RadiologyIRServer
Server side component to perform search and marshall data for [RadiologyIR](https://github.com/magic-lantern/RadiologyIR) client. Built using Flask and supporting [Solr](http://lucene.apache.org/solr/) and [Yottalook WS API](http://yottalook.com/api). As this application was designed with an Ember Data client, the REST services provided follow the [JSON API](jsonapi.org) specification.

Search Analytics in the form of query tracking, search back end response tracking, and client side click tracking made possible via [MongoDB](https://www.mongodb.org/)

This application was developed and tested with Python 3 (specifically 3.4). It likely could work with Python 2 but would require some changes.

## Installation & Usage

Update ir_server.py to point to your Solr instance and collection/core by changing this line to match your environment:

```
solr = pysolr.Solr('http://localhost:8983/solr/mypacs')
```
Also, update code to point to your MongoDB instance by changing this line as appropriate:

```
client = MongoClient("mongodb://localhost:27017")
```

I recommend creating a virtual python environment. I've used [Anaconda](https://www.continuum.io/downloads) There are numerous methods for creating a virtual environment - feel free to choose the one you like best. The following commands will create a virtual environment, install required dependencies, and launch the application:

```
conda env create -f flask_conda_env.yml
source activate flask
python ir_server.py
```
A pip requirements.txt file is also provided if you prefer to use pip and a different python virtual environment.

Open http://localhost:5000 in your browser to verify.

## License

For code written by [magic-lantern](https://github.com/magic-lantern), see the [LICENSE](LICENSE.md) file for license rights and limitations (Apache License, Version 2.0).
Code from other parties may have different licensing terms.
