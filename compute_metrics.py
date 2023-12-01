import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from fix_tag import phase_tag


metric_attrs = ['COLOR', 'Saturation', 'Brightness', 'MATERIAL', 'PATTERN', 'TRENDS', 'PROCESS', 'OCCASION', 'LOCATION',
                'STYLE', 'SEASON', 'Fit', 'Event', 'Neckline', 'Collar', 'Sleeve Shape', 'Sleeve Length', 'Cuff',
                'Shoulder', 'Back', 'Waist', 'Waistband', 'Length', 'Cut', 'Rise', 'Design']


def load_data(data_root, data_name):
    datas = pd.read_excel(f'{data_root}/{data_name}', sheet_name=None)
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
    metric_attrs = list(map(lambda i: i.lower(), metric_attrs))
    keys = list(gt.keys())
    for attr in keys:
        gt.update({attr.lower(): gt.pop(attr)})
        pre.update({attr.lower(): pre.pop(attr)})
        if attr.lower() in metric_attrs + ['color_ori', 'first_category', 'second_category']:
            gt[attr.lower()] = list(map(lambda i: i.lower() if isinstance(i, str) else i, gt[attr.lower()]))
            pre[attr.lower()] = list(map(lambda i: i.lower() if isinstance(i, str) else i, pre[attr.lower()]))

    for attr in gt:
        gt[attr] = np.array(gt[attr])
        pre[attr] = np.array(pre[attr])
    assert np.all(gt['skc_id'] == pre['skc_id']), 'wrong'
    return gt, pre, no_exist


def compute_acc(gt, pre):
    tf = [i == j for i, j in zip(gt, pre)]
    # wrong_ind = np.where(np.array(tf)==False)
    return tf.count(True)/len(tf), tf


def compute_metrics(attr, gt, pre, labels, save_root=None):
    acc, wrong_ind = compute_acc(gt, pre)
    plot_confusion_matrix(attr, gt, pre, labels, save_root)
    return acc, wrong_ind


def plot_confusion_matrix(attr, gt, pre, labels, save_root=None):
    cm = confusion_matrix(gt, pre, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot()
    plt.title(attr)
    if save_root:
        if not os.path.exists(save_root): os.makedirs(save_root)
        plt.savefig(f'{save_root}/{attr}.png')
    plt.show()


def remove_wrong_data(data, wrong_ind):
    for attr in data:
        data[attr] = data[attr][wrong_ind]
    return data


if __name__ == '__main__':
    res = {}
    data_name = 'all.xlsx'
    save_root = './output/confusion_matrix'

    gt, pre, no_exist = load_data('./output', data_name)
    category_map, common_tag_map, category_tag_map, choose_item_map = phase_tag('./data_utils/tag_gt.json')

    # compute acc of first category
    first_cat_acc, first_wrong_ind = compute_metrics('first_category', gt['first_category'], pre['first_category'],
                                                     list(category_map.keys()), save_root)
    res['first_category'] = first_cat_acc
    # remove the wrong data of first category and compute the acc of second category by each first category
    gt = remove_wrong_data(gt, first_wrong_ind)
    pre = remove_wrong_data(pre, first_wrong_ind)
    for first in category_map:
        ind = np.where(gt['first_category']==first)[0]
        print(first, len(ind))
        if len(ind) > 0:
            second_cat_acc, sec_wrong_ind = compute_metrics(first, gt['second_category'][ind],
                                                            pre['second_category'][ind], category_map[first], save_root)
            res[first] = second_cat_acc

    # remove the wrong data of second category, and then compute metrics
    for attr in res:
        if attr in common_tag_map.keys():
            metrics = compute_metrics(attr, gt[attr], pre[attr])
        elif attr in category_tag_map.keys():
            metrics = compute_metrics(attr, gt[attr], pre[attr])

