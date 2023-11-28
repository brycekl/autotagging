import os
import requests
from PIL import Image
import multiprocessing
import argparse 

import json 
import copy
import os 
import requests
from queue import Queue
import pandas as pd
import time

# from taggingpipeline.mainpipeline.tag_service import Service
import sys
sys.path.append('/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline')
print(sys.path)
from tagging_llava import InitLLA



result = []


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    parser.add_argument('--url', type=str, default='https://example.com/path/to/image.jpg', help='url')
    parser.add_argument('--res_dir', type=str, default='./downloaded_images', help='res_dir')
    parser.add_argument('--questionjson', type=str, default='/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/prompts/quesion.json', help='question.json path')
    parser.add_argument('--version', type=str, default='20231026_clothing_v2', help='question.json path')
    parser.add_argument('--outcsvpath', type=str, default='/root/autodl-tmp/autotagging/taggingpipeline/test/res.csv')


    args = parser.parse_args()

    start_time = time.time()

    if not os.path.exists(args.res_dir):
        os.makedirs(args.res_dir)
    
    qw_s = InitLLA(args.questionjson)

    init_time = time.time()

    imgsinfo0 = {'imgs':'/root/autodl-tmp/autotagging/taggingpipeline/test_data/test_easy_7_imgs',
                'info':'{Color:   Green, \n Product desciption: Take your collared look up a notch. We made this notch collar blouse with a relaxed, slim fit with a clean and crisp look for an everyday appeal. Perfectly made to be layered or worn solo. Plus, silk fiber contains 18 kinds of amino acids that make it amazing for skin nourishment, hypo-allergenic, and naturally thermoregulating to help maintain body temperature., \n details: [\n Crafted from 90% mulberry silk for luxe feel, and 10% spandex for a little stretch  \t, \n 19mm fabric weight for a premium drape and hand-feel, \n This material is certified by OEKO-TEX Standard 100 (Certificate Number: SH015140381& SH050127759) which ensures that no hazardous substances are present",Made with care in China  \n ],size&fit:[Slim fit, consider sizing up for a more relaxed look]}'
                }
    # imgsinfo1 =  {'id': 1712371384807624705, 
    #              'imgs': '/root/autodl-tmp/autotagging/taggingpipeline/output/datav1_4_20231017_clothing_v1_20231021_1348/imgs/1712371384807624705_13_48_44', 
    #              'info': {
    #                         'title': '5" Airbrush High-Waist Biker Short - Macadamia', 
    #                         'desc': '<p>The biker is back and itâ\x80\x99s better than ever. Meet the new ultimate short for practice and pavement: the 5â\x80\x9d High-Waist Biker Short, made in our signature lifting, sculpting Airbrush fabric, with a high waist, moisture-wicking technology and 4-way stretch that moves with you. Equal parts forward and functional in a new sport-ready 5â\x80\x9d inseam.  Pair with a statement Alo bra tank or tee.</p>\n<ul>\n<li>Sculpts, lifts &amp; smooths</li>\n<li>On-trend high waist &amp; 5â\x80\x9d inseam</li>\n<li>Designed &amp; uniquely fit to flatter every size</li>\n<li>Wear-tested by our in-house team for the perfect fit</li>\n</ul>', 
    #                         'link': 'https://www.aloyoga.com/products/w6311r-airbrush-high-waist-5-biker-short-macadamia'}}

    # imgsinfo2 = {'id': 1711285017147125761, 
    #             'imgs': '/root/autodl-tmp/autotagging/taggingpipeline/output/datav1_4_20231017_clothing_v1_20231021_1500/imgs/1711285017147125761_15_00_46', 
    #             'info': {
    #                 'ftitle': 'The Dream PantÂ®', 
    #                 'desc': 'Tailored look, sweatpant feel. Made of soft double-knit fabric, the Dream PantÂ® features an elastic waist, pintuck detailing, and a sleek tapered leg. Plus, it has a flat finish, so it looks polished, but itâ\x80\x99s comfortable enough to nap in. The best part? Itâ\x80\x99s wrinkle resistant. From morning meetings to afternoon errands to late-night loungingâ\x80\x94this pant looks (and feels) like a dream.', 
    #                 'features': '{"fit": ["Inseam: 27.5\\"", "Slim fit at hips. Relaxed fit through thigh. Tapered leg. "], "washCcare": ["Machine wash cold. Hang to dry."], "sustainability": ["Ever-Better Factory"]}', 
    #                 'link': 'https://www.everlane.com/products/womens-live-in-pant-black'}}
    # imgsinfo3 = {'id': 1711285011015053314, 
    #              'imgs': '/root/autodl-tmp/autotagging/taggingpipeline/output/datav1_4_20231017_clothing_v1_20231021_1458/imgs/1711285011015053314_14_58_40',
    #              'info': {
    #                  'title': 'The Utility Barrel Pant', 
    #                  'desc': 'The shape of things to come. Made of lightweight cotton twill with just a touch of stretch, the Utility Barrel Pant is complete with a waist-nipping high rise, a cool curved leg, and an easy cropped length. Plus, it has utilitarian details, like accent stitching and patch pockets for a craftsman-inspired look. ',
    #                    'features': '{"fit": ["High-rise", "Slim fit through hips. Relaxed barrel leg. Tapered and cropped at ankle.", "Customers say this style runs large. Consider sizing down for a more snug fit.", "Regular Inseam: 26.5\\"", "Tall Inseam: 28.5\\""], "washCcare": ["Machine wash cold inside out, tumble dry low."], "sustainability": ["Organic Cotton", "Cleaner Chemistry"]}', 
    #                    'link': 'https://www.everlane.com/products/womens-utility-barrel-pant-navy'}}


    # imgsinfos = [imgsinfo2,imgsinfo3]
    qname = "what is the category  of this merchandise? \n options:['jacket', 'pants', 'sweater', 'jumpsuit', 'sweatshirt', 'top', 'outerwear', 'shorts', 'activewear', 'denim', 'dresses', 'lounge/pajamas', 'skirt'] \n please select an answer from the above options,no need to answer in full sentences, please answer your options directly and just give one option please answer 'none' if there is no match in the options"
    imgsinfos = [imgsinfo0]

    for imgsinfo in imgsinfos:
        tag_perp = qw_s.tag_main(imgsinfo['imgs'],qname,args.version)


        print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        print('imgsinfo',imgsinfo)
        print('tag_perp',tag_perp)
        print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')


        print('===============================')
        print('RESULT:')

        print(result)
        print('===============================')

