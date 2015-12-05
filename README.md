# RadiologyIRServer
Server side component to perform search and marshall data for [RadiologyIR](https://github.com/magic-lantern/RadiologyIR) client. Built using Flask and supporting [Solr](http://lucene.apache.org/solr/) and [Yottalook WS API](http://yottalook.com/api). As this application was designed with an Ember Data client, the REST services provided follow the [JSON API](jsonapi.org) specification.

This application was developed and tested with Python 3 (specifically 3.4). It likely could work with Python 2 but would require some changes.

## Installation & Usage

Create a virtual python environment. I've used [Anaconda](https://www.continuum.io/downloads) There are numerous methods for creating a virtual environment - here's the steps for conda:

```
conda create --name myvenv flask
source activate myvenv
```

Update ir_server.py to point to your Solr instance by changing this line:

```
solr = pysolr.Solr('http://localhost:8983/solr/mypacs')
```

Install the required libraries and start the service:

```
conda env create -f flask_conda_env.yml
python ir_server.py
```
A pip requirements.txt file is also provided if you prefer to use pip and a different python virtual environment.

Open http://localhost:5000 in your browser to verify.

## License

For code written by [magic-lantern](https://github.com/magic-lantern), see the [LICENSE](LICENSE.md) file for license rights and limitations (Apache License, Version 2.0).
Code from other parties may have different licensing terms.
