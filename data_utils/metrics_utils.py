import os
import shutil

import pandas as pd
import json
import numpy as np
from data_utils.format_data import all_attr
from collections import Counter


def get_skc2img(skc2img_root, repeat_skc, img_root='/root/autodl-tmp/datas'):
    # img_root = '/root/autodl-tmp/tmp_res/tag_res/output'

    dir_names = os.listdir(img_root)
    for dir_name in dir_names:
        if os.path.isfile(os.path.join(img_root, dir_name)):
            continue
        img_path = os.path.join(img_root, dir_name, 'imgs') if dir_name != 'imgs' else os.path.join(img_root, dir_name)
        if not os.path.exists(img_path):
            os.removedirs(os.path.dirname(img_path))
            continue
        for skc_id in os.listdir(img_path):
            if skc_id in skc2img_root:
                if skc_id not in repeat_skc:
                    repeat_skc[skc_id] = [skc2img_root[skc_id]]
                repeat_skc[skc_id].append(img_path)
            skc2img_root[skc_id] = img_path


def get_multi_path_skc2img(paths=['/root/autodl-tmp/tmp_res_before_1206/tag_res/output',
                                  '/root/autodl-tmp/tmp_res_zr/tag_res/output',
                                  '/root/autodl-tmp/datas']):
    """
    get the corresponding relationship of skc_id and img path, from multi paths
    """
    # paths = ['/root/autodl-tmp/tmp_res/tag_res/output', '/root/autodl-tmp/datas']
    skc2img_root, repeat_skc = {}, {}
    for path in paths:
        get_skc2img(skc2img_root, repeat_skc, path)
    return skc2img_root, repeat_skc


metric_attrs = ['COLOR', 'Saturation', 'Brightness', 'MATERIAL', 'PATTERN', 'TRENDS', 'PROCESS', 'OCCASION', 'LOCATION',
                'STYLE', 'SEASON', 'Fit', 'Event', 'Neckline', 'Collar', 'Sleeve Shape', 'Sleeve Length', 'Cuff',
                'Shoulder', 'Back', 'Waist', 'Waistband', 'Length', 'Cut', 'Rise', 'Design']


def load_data(data_path, data_name=None):
    f"""
    load data from {data_path}/{data_name}, choose the pre data according to gt data(not every pre data has gt)
    """
    if data_name:
        data_path = os.path.join(data_path, data_name)
    datas = pd.read_excel(data_path, sheet_name=None, converters={'skc_id': str})
    gt = datas['gt'].to_dict('list')
    pre_ori = datas['pre'].to_dict('list')
    pre = {attr: [] for attr in pre_ori}
    no_exist = []
    # gt the corresponding pre data from original pre according to gt sck_id
    for gt_ind, id in enumerate(gt['skc_id']):
        ind = pre_ori['skc_id'].index(id) if id in pre_ori['skc_id'] else -1
        if ind == -1:
            no_exist.append(id)
            for attr in gt:
                gt[attr].pop(gt_ind)
        else:
            for attr in pre:
                pre[attr].append(pre_ori[attr][ind])

    # Fixme lower all letter
    global metric_attrs
    metric_attrs_lower = list(map(lambda i: i.lower(), metric_attrs))
    keys = list(gt.keys())
    for attr in keys:
        gt.update({attr.lower(): gt.pop(attr)})
        pre.update({attr.lower(): pre.pop(attr)})
        if attr.lower() in metric_attrs_lower + ['color_ori', 'first category', 'subcategory']:
            gt[attr.lower()] = list(map(lambda i: i.lower() if isinstance(i, str) else i, gt[attr.lower()]))
            pre[attr.lower()] = list(map(lambda i: i.lower() if isinstance(i, str) else i, pre[attr.lower()]))

    # convert to numpy for convenient cope
    for attr in gt:
        gt[attr] = np.array(gt[attr])
        pre[attr] = np.array(pre[attr])
    assert np.all(gt['skc_id'] == pre['skc_id']), 'wrong'
    return gt, pre, no_exist


def merge_excel(paths, save_root=None):
    # must use data_utils/format_data to format data first
    all_attr_lower = [i.lower() for i in all_attr]
    pre, gt, no_exist = {attr: [] for attr in all_attr_lower}, {attr: [] for attr in all_attr_lower}, []
    if not save_root:
        save_root = os.path.dirname(paths[0])
    save_name = ''

    for path in paths:
        save_name += os.path.basename(path).split('.')[0]
        gt_tmp, pre_tmp, no_exist_tmp = load_data(os.path.dirname(path), os.path.basename(path))
        for attr in all_attr_lower:
            gt[attr].extend(gt_tmp[attr])
            pre[attr].extend(pre_tmp[attr])
        no_exist.extend(no_exist_tmp)

    # convert to numpy for convenient cope
    for attr in all_attr_lower:
        gt[attr] = np.array(gt[attr])
        pre[attr] = np.array(pre[attr])

    # delete the repeat data after merge
    skc_num = Counter(gt['skc_id'])
    for skc, num in skc_num.items():
        if num == 1:
            continue
        ind = np.where(gt['skc_id'] == skc)[0]
        true_ind = gt['skc_id'] != skc
        true_ind[ind[1]] = True
        for attr in all_attr_lower:
            gt[attr] = gt[attr][true_ind]
            pre[attr] = pre[attr][true_ind]
    assert np.all(gt['skc_id'] == pre['skc_id']), 'wrong'

    gt_df = pd.DataFrame(gt)
    pre_df = pd.DataFrame(pre)
    with pd.ExcelWriter(f"{save_root}/{save_name}.xlsx") as writer:
        gt_df.to_excel(writer, sheet_name='gt', index=False)
        pre_df.to_excel(writer, sheet_name='pre', index=False)

    return gt, pre, no_exist


def merge_wrong_data_info(wrong_predict, infos, save_path):
    """
    after compute metrics and save wrong_predict, this function helps merge more information together
    """
    wrong_predict['merchantCategoryName'] = []
    wrong_predict['color_ori'] = []
    wrong_predict['info'] = []
    for ind, skc_id in enumerate(wrong_predict['skc_id']):
        info_ind = infos['skc_id'].index(skc_id)
        for attr in ['merchantCategoryName', 'color_ori', 'info']:
            wrong_predict[attr].append(infos[attr][info_ind])
    wrong_predict['skc_id'] = [str(i) for i in wrong_predict['skc_id']]
    df = pd.DataFrame(wrong_predict)
    df.to_excel(save_path, index=False)


def get_wrong_imgs(wrong_predict_path, save_root=None):
    imgs_root = '../../datas/imgs'
    if not save_root:
        save_root = os.path.dirname(wrong_predict_path) + '/wrong_img'
    wrong_predict = pd.read_excel(wrong_predict_path, converters={'skc_id': str}).to_dict('list')
    need_wrong = ['*->t-shirt']
    for ind, wrong in enumerate(wrong_predict['wrong']):
        wrong = json.loads(wrong)
        skc_id = wrong_predict['skc_id'][ind]
        for i, j in wrong.items():
            # gt_cat = j.split('->')[0]
            # pre_cat = j.split('->')[1]
            os.makedirs(os.path.join(save_root, i, j), exist_ok=True)
            shutil.copytree(os.path.join(imgs_root, skc_id), os.path.join(save_root, i, j, skc_id))


if __name__ == '__main__':
    # skc2img_root, repeat_skc = {}, {}
    # get_skc2img(skc2img_root, repeat_skc)
    get_wrong_imgs('../output/overcoat2/wrong.xlsx')
