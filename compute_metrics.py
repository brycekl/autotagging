import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from fix_tag import phase_tag
from data_utils.metrics_utils import get_multi_path_skc2img, merge_excel, load_data
from shutil import copytree


def compute_acc(gt, pre):
    """
    compute acc
    """
    # todo how to compute acc for multi choice
    tf = [i == j for i, j in zip(gt, pre)]
    # wrong_ind = np.where(np.array(tf)==False)
    return tf.count(True)/len(tf), tf


def compute_metrics(attr, gt, pre, labels, save_root=None):
    # compute acc for the attr and plot confusion matrix
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


def save_wrong_data(gt, pre, wrong_ind, save_root, skc2_img_root, wrong_predict, pre_attr):
    """
    save wrong data(img, maybe desc later) for analysis
    paras:
        gt:
        pre:
        wrong_ind: the index of wrong data of skc_id
        save_root: the save root of images of wrong data
        skc2_img_root: the dict of map relation between skc_id and img_root {skc_id: img_root}
        wrong_predict: dict for save the wrong data's spu, skc_id and the wrongs
        pre_attr: the predicted attribute
    """
    if not os.path.exists(save_root):
        os.makedirs(save_root)

    wrong_ind = [not i for i in wrong_ind]
    wrong_skc = gt['skc_id'][wrong_ind]
    for skc_id in wrong_skc:
        skc_ind = np.where(gt['skc_id'] == skc_id)[0]
        assert len(skc_ind) == 1, skc_id
        skc_ind = skc_ind[0]

        # save predict result to wrong_predict
        wrong_attr = {pre_attr: gt[pre_attr][skc_ind] + '->' + pre[pre_attr][skc_ind]}
        if skc_id in wrong_predict['skc_id']:
            wrong_predict_ind = wrong_predict['skc_id'].index(skc_id)
            wrong_predict['wrong'][wrong_predict_ind][pre_attr] = wrong_attr[pre_attr]
        else:
            for attr in wrong_predict:
                if attr == 'wrong':
                    wrong_predict[attr].append(wrong_attr)
                    continue
                wrong_predict[attr].append(gt[attr][skc_ind])

        # save wrong img
        img_root = skc2_img_root.get(skc_id)
        if img_root and not os.path.exists(f'{save_root}/{skc_id}'):
            copytree(f'{img_root}/{skc_id}', f'{save_root}/{skc_id}')


def remove_wrong_data(data, wrong_ind):
    for attr in data:
        data[attr] = data[attr][wrong_ind]
    return data


if __name__ == '__main__':
    res = {}  # for saving the acc result of different attributes
    data_name = '20231122.xlsx'
    paths = ['./output/20231122.xlsx',  './output/20231124_first.xlsx']
    wrong_predict = {'spu': [], 'skc_id': [], 'wrong': []}

    # load datas and set save root
    gt, pre, no_exist = load_data('./output', data_name)
    if paths:
        gt, pre, no_exist = merge_excel(paths)
        data_name = 'merge.xlsx'
    category_map, common_tag_map, category_tag_map, choose_item_map = phase_tag('./data_utils/tag_gt.json')
    skc2img_root, repeat_skc = get_multi_path_skc2img()
    cm_save_root = './output/confusion_matrix' + data_name.split('.xlsx')[0]
    wi_save_root = './output/wrong_data_skc/' + data_name.split('.xlsx')[0]

    # compute acc of first category
    first_cat_acc, first_wrong_ind = compute_metrics('first_category', gt['first_category'], pre['first_category'],
                                                     list(category_map.keys()), cm_save_root)
    res['first_category'] = first_cat_acc
    save_wrong_data(gt, pre, first_wrong_ind, wi_save_root, skc2img_root, wrong_predict, 'first_category')

    # remove the wrong data of first category and compute the acc of second category by each first category
    gt_sec = remove_wrong_data(gt.copy(), first_wrong_ind)
    pre_sec = remove_wrong_data(pre.copy(), first_wrong_ind)
    for first_cat in category_map:
        # get the data of current first category
        ind = np.where(gt_sec['first_category'] == first_cat)[0]
        gt_tmp = {i: j[ind] for i, j in gt_sec.items()}
        pre_tmp = {i: j[ind] for i, j in pre_sec.items()}
        print(first_cat, len(ind))
        if len(ind) > 0:
            second_cat_acc, sec_wrong_ind = compute_metrics(first_cat, gt_tmp['second_category'],
                                                            pre_tmp['second_category'], category_map[first_cat],
                                                            cm_save_root)
            res[first_cat] = second_cat_acc
            save_wrong_data(gt_tmp, pre_tmp, sec_wrong_ind, wi_save_root, skc2img_root, wrong_predict, 'second_category')

    # compute acc for common tag
    # for attr, options in common_tag_map.items():
    #     acc, wrong_ind = compute_metrics(attr, gt[attr], pre[attr], list(options), cm_save_root)
    #     res[attr] = acc
    #     save_wrong_data(gt, pre, wrong_ind, wi_save_root, skc2img_root, wrong_predict, attr)

    # save wrong predict excel table
    df = pd.DataFrame(wrong_predict)
    df.to_excel(f'{wi_save_root}/wrong.xlsx', index=False)

    # todo compute metrics for category tag
    # remove the wrong data of second category, and then compute metrics
    for attr in res:
        if attr in common_tag_map.keys():
            metrics = compute_metrics(attr, gt[attr], pre[attr])
        elif attr in category_tag_map.keys():
            metrics = compute_metrics(attr, gt[attr], pre[attr])

