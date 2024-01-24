import os.path
import sys
sys.path.append('/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline')
import json
import numpy as np
import pandas as pd

from data_utils.predict_utils import load_local_data, set_seed
from taggingpipeline.mainpipeline.tag_service import Service
from data_utils.format_data import all_attr, phase_tag
from data_utils.metrics_utils import merge_excel
from compute_metrics import compute_all_metrics


if __name__ == '__main__':
    spu_path = 'data_utils/spu/all_first.xlsx'
    info_path = '../datas/info.xlsx'
    start_tag_path = './start_tag.json'
    all_attr = [i.lower() for i in all_attr]
    pre_res, gt = {attr: [] for attr in all_attr}, {attr: [] for attr in all_attr}

    # save_root = './output/' + os.path.basename(spu_path).split('.')[0]
    save_root = './output/test3'
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
    all_product_info, no_img_skc, no_info_skc, repeat_skc = load_local_data(spu_path, info_path)
    print(f'nums: {len(all_product_info)}')

    # load gt and get corresponding data
    paths = ['./output/20231122.xlsx',  './output/20231124_first.xlsx']
    gt_all, _, _ = merge_excel(paths)

    # label all data
    tag_service = Service(question_json)
    for product_info in all_product_info:
        # get corresponding gt
        product_gt = {}
        gt_ind = list(gt_all['skc_id']).index(product_info['skc_id'])
        for attr in gt_all:
            gt[attr].append(gt_all[attr][gt_ind])
            product_gt[attr] = gt_all[attr][gt_ind]

        # predict all tags , pre_common_tag=False, pre_category_tag=False
        tag_pre = tag_service.tag_main(product_info['imgs'], product_info['info'], gettag_url_interface,
                                       item_gt=product_gt, pre_common_tag=False, pre_category_tag=False)
        # save predict result
        for attr in all_attr:
            if attr in ['spu', 'skc_id']:
                pre_res[attr].append(product_info[attr])
            elif attr == 'link':
                pre_res[attr].append(product_info['imgs'])
            elif attr in tag_pre:
                pre_res[attr].append(tag_pre[attr])
            else:
                pre_res[attr].append('nan')

    # compute metrics
    for attr in gt:
        gt[attr] = np.asarray(gt[attr])
        pre_res[attr] = np.asarray(pre_res[attr])
    category_map, common_tag_map, category_tag_map, choose_item_map = phase_tag('./data_utils/tag_gt.json')
    metrics, wrong_predict = compute_all_metrics(gt, pre_res, category_map, common_tag_map, category_tag_map,
                                                 save_root)
    # save result
    for attr in gt:
        gt[attr] = [i if i != 'nan' else None for i in gt[attr]]
        pre_res[attr] = [i if i != 'nan' else None for i in pre_res[attr]]
    gt_df = pd.DataFrame(gt)
    pre_df = pd.DataFrame(pre_res)
    with pd.ExcelWriter(f"{save_root}/result.xlsx") as writer:
        gt_df.to_excel(writer, sheet_name='gt', index=False)
        pre_df.to_excel(writer, sheet_name='pre', index=False)
