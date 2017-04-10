"""etl module Extracts XML from MARC21 records, transforms the MARC XML to
BIBFRAME 2.0 RDF XML, and finally de-duplicates and loads the RDF into a 
triplestore."""

__author__ = "Jeremy Nelson, Mike Stabile"

import click
import datetime
import os
import pymarc
import rdflib
import requests
import sys

from lxml import etree

PROJECT_HOME =  os.path.split(
    os.path.abspath(os.path.dirname(__file__)))[0]
sys.path.append(PROJECT_HOME)

import bibcat.rml.processor as processor
from instance import config

MARC2BF_XSLT = etree.XSLT(
    etree.parse(config.MARC2BIBFRAME))

KEAN_PROCESSOR = processor.XMLProcessor(base_url=config.BASE_URL,
    rml_rules=[os.path.join(PROJECT_HOME, "custom/kean-rml.ttl"),
               os.path.join(PROJECT_HOME, 
               "bibcat/rdfw-definitions/rml-bibcat-marc-dedup.ttl")])

def extract(marc_filepath):
    """Takes a MARC21 file, iterates through each MARC record 
    and yields MARC XML""" 
    reader = pymarc.MARCReader(open(marc_filepath, "rb"), to_unicode=True)
    for record in reader:
        yield pymarc.record_to_xml(record, namespace=True)

def load(bf_rdf):
    """Takes a BIBFRAME 2.0 rdflib.Graph and loads into triplestore

    args:
        bf_rdf(rdflib.Graph): RDF Graph
    """
    if hasattr(config, "TRIPLESTORE_URL"):
        triplestore_url = config.TRIPLESTORE_URL
    else:
        # Default is a local Blazegraph instance
        triplestore_url = "http://localhost:9999/blazegraph/sparql"
    result = requests.post(triplestore_url,
        data=bf_rdf.serialize(format='turtle'),
        headers={"Content-Type": "text/turtle"})
    if result.status_code < 400:
        return result.text

def transform(raw_xml):
    """Takes MARC XML and returns transformed BIBFRAME 2.0 RDF XML after
    applying Kean specific RML rules to BIBFRAME RDF,

    Args:
        raw_xml(str): MARC XML

    Returns:
        return rdflib.Graph
    """
    marc_xml = etree.XML(raw_xml)
    bf_xml = MARC2BF_XSLT(marc_xml, baseuri="'http://bibcat.kean.edu/'")
    bf_rdf = rdflib.Graph()
    bf_rdf.parse(data=etree.tostring(bf_xml))
    KEAN_PROCESSOR.output = bf_rdf
    for item_iri in bf_rdf.subjects(predicate=processor.NS_MGR.rdf.type,
                                    object=processor.NS_MGR.bf.Item):
        KEAN_PROCESSOR.run(bf_xml, item_iri=item_iri)
    return bf_rdf

             
@click.command()
@click.option("--marc_filepath", prompt="Full file path to MARC21 record")
def process(marc_filepath):
    """Takes a MARC21 file path and performs ETL process to Triplestore"""
    start = datetime.datetime.utcnow()
    click.echo("Started transforming MARC to BF at {} for {}".format(
        start.isoformat(),
        marc_filepath))
    for i, marc_xml in enumerate(extract(marc_filepath)):
        bf_rdf = transform(marc_xml)
        load(bf_rdf)
        if not i%100 and i > 0:
            click.echo(".", nl=False)
        if not i%1000:
            click.echo(i, nl=False)
    end = datetime.datetime.utcnow()
    click.echo("Finished ETL for {} at {}, total time={} minutes".format(
        marc_file,
        end.isoformat(),
        (end-start).seconds / 60.0))

if __name__ == '__main__':
    process()
        
