import sys
sys.path.append('/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline')
import json

from data_utils.predict_utils import load_local_data, set_seed
from taggingpipeline.mainpipeline.tag_service import Service
from data_utils.format_data import all_attr
from data_utils.metrics_utils import merge_excel


if __name__ == '__main__':
    data_path = 'data_utils/spu/overcoat->.xlsx'
    info_path = '../datas/info.xlsx'
    start_tag_path = './start_tag.json'
    pre_res = {attr.lower(): [] for attr in all_attr}
    set_seed(2023)

    # load cfgpath
    with open(start_tag_path, 'r') as f:
        cfg = json.load(f)
    f.close()

    res_dir = cfg['res_dir']
    gettag_url_interface = cfg['gettag_url']
    get_product_skc_interface = cfg['get_product_skc']
    product_source = cfg['get_product_skc']["product_url"]
    question_json = cfg['questionjson']
    upload_tag_param = cfg['upload_tags']

    # get all data
    all_product_info = load_local_data(data_path, info_path)

    # load gt and get corresponding data
    paths = ['./output/20231122.xlsx',  './output/20231124_first.xlsx']
    gt_all, _, _ = merge_excel(paths)
    gt = {attr.lower(): [] for attr in all_attr}

    # label all data
    servicetag = Service(question_json)
    for product_info in all_product_info[:10]:
        # get corresponding gt
        gt_ind = list(gt_all['skc_id']).index(product_info['skc_id'])
        for attr in gt_all:
            gt[attr].append(gt_all[attr][gt_ind])

        # predict all tags
        tag_pre = servicetag.tag_main(product_info['imgs'], product_info['info'], gettag_url_interface)
        # format tag pre
        tag_res = {attr.lower(): None for attr in all_attr}
        for item in tag_pre:
            tag_res[item['label']] = item['value']
        tag_res['spu'] = product_info['spu']
        tag_res['skc_id'] = product_info['skc_id']
        tag_res['link'] = product_info['imgs']
        for attr in pre_res:
            pre_res[attr].append(tag_res[attr])

    # compute metrics
    s = 1

