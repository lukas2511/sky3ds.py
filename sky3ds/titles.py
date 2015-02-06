#!/usr/bin/env python3

import os
import json
import sys
from xml.dom import minidom
from appdirs import user_data_dir

if sys.version_info.major == 3:
    import urllib.request
else:
    import urllib2

data_dir = user_data_dir('sky3ds', 'Aperture Laboratories')
template_txt = os.path.join(data_dir, 'template.txt')
template_json = os.path.join(data_dir, 'template.json')
titles_json = os.path.join(data_dir, 'titles.json')

def get_template(serial, sha1):
    template_json_fp = open(template_json)
    templates = json.load(template_json_fp)
    template_json_fp.close()

    return next((template for template in templates if template["sha1"] == sha1 and template["serial"] == serial), None)

def convert_template_to_json():
    template_txt_fp = open(template_txt)
    templates = template_txt_fp.read().split("** : ")[1:]
    template_txt_fp.close()
    out_templates = []
    for template in templates:
        template = template.split("\n")[:-3]
        out_templates.append({
            'serial': template[0],
            'sha1': template[2][6:].lower(),
            'card_data': " ".join(template[3:])
        })

    template_json_fp = open(template_json, "w")
    template_json_fp.write(json.dumps(out_templates))
    template_json_fp.close()

def update_title_db():
    source = "http://3ds.essh.co/xml.php"
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19'

    if sys.version_info.major == 3:
        xml_data = urllib.request.urlopen(urllib.request.Request(source, headers={'User-Agent': user_agent})).read().decode('utf8')
    else:
        xml_data = urllib2.urlopen(urllib2.Request(source, headers={'User-Agent': user_agent})).read().decode('utf8')

    for bad_char in [0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0b, 0x0e, 0x0f]:
        xml_data = xml_data.replace(chr(bad_char), "")
    xmldoc = minidom.parseString(xml_data.encode('utf-8'))
    itemlist = xmldoc.getElementsByTagName('release')

    releases = {}

    error = 0

    for release in itemlist:
        try:
            media_id = release.getElementsByTagName('titleid')[0].firstChild.nodeValue
            product_code = release.getElementsByTagName('serial')[0].firstChild.nodeValue
            releases.update({"%s-%s" % (product_code, media_id): {
                'id': release.getElementsByTagName('id')[0].firstChild.nodeValue,
                'name': release.getElementsByTagName('name')[0].firstChild.nodeValue,
                'product_code': product_code,
                'media_id': media_id,
                'region': release.getElementsByTagName('region')[0].firstChild.nodeValue,
                'publisher': release.getElementsByTagName('publisher')[0].firstChild.nodeValue,
                'languages': release.getElementsByTagName('languages')[0].firstChild.nodeValue,
                'imgcrc': release.getElementsByTagName('imgcrc')[0].firstChild.nodeValue,
                'firmware': release.getElementsByTagName('firmware')[0].firstChild.nodeValue,
            }})
        except:
            error += 1
            pass

    titles_json_fp = open(titles_json, "w")
    titles_json_fp.write(json.dumps(releases))
    titles_json_fp.close()
    print("Title database updated (%d entries, %d failed)" % (len(releases), error))

def rom_info(product_code, media_id):
    try:
        titles_json_fp = open(titles_json)
        releases = json.load(titles_json_fp)
        titles_json_fp.close()
        product_code = product_code[0:3] + "-" + product_code[6:10]

        selector = "%s-%s" % (product_code, media_id)
        if not selector in releases:
            if product_code[7] == "A":
                product_code = product_code[0:7] + 'P'
                selector = "%s-%s" % (product_code, media_id)
        release = releases["%s-%s" % (product_code, media_id)]
        return release

    except:
        return False


