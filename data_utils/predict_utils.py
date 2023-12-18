import pandas as pd
import os
import multiprocessing
import json
import re
from tqdm import tqdm
import numpy as np
import torch
import random
from bs4 import BeautifulSoup
from collections import Counter
from taggingpipeline.mainpipeline.utils import res_post_process


def format_save_info(product_info, save_root, save_name):
    """
    format and save all information to save root while infer
    """
    all_infos = {i: [] for i in ['spu', 'skc_id', 'link', 'info', 'merchantCategoryName', 'color_ori', 'feature',
                                 'desc', 'merchantId', 'imgs', 'videos', 'title', 'price', 'connectVideoCount',
                                 'createTime', 'homepageStatus', 'onSaleSkuCount', 'originalPrice',
                                 'publishTime', 'spuStatus', 'status', 'tagCount', 'totalSkuCount', 'updateTime']}

    for item in product_info:
        item['imgs'] = os.path.join(save_root, 'imgs', item['id'])
        item['skc_id'] = item['id']
        item['color_ori'] = item['color']
        for attr in all_infos:
            if attr in item:
                all_infos[attr].append(item[attr])
            else:
                all_infos[attr].append(None)
    df = pd.DataFrame(all_infos)
    df.to_excel(os.path.join(save_root, save_name + '.xlsx'), index=False)


def load_local_data(data_path, info_path):
    all_datas, no_img_skc, no_info_skc, repeat_data = [], [], [], {}
    datas = pd.read_excel(data_path).to_dict('list')
    infos = pd.read_excel(info_path).to_dict('list')
    # remove the repeat skc in datas todo 优化
    datas['skc_id'] = np.array(datas['skc_id'])
    datas['spu'] = np.array(datas['spu'])
    skc_num = Counter(datas['skc_id'])
    for skc, num in skc_num.items():
        if num == 1:
            continue
        ind = np.where(datas['skc_id'] == skc)[0]
        true_ind = datas['skc_id'] != skc
        true_ind[ind[1]] = True
        repeat_data[skc] = len(ind) - 1
        for attr in datas:
            datas[attr] = datas[attr][true_ind]

    for ind, skc_id in tqdm(enumerate(datas['skc_id'])):
        if skc_id in infos['skc_id']:
            info_ind = infos['skc_id'].index(skc_id)
            # if the img path do not have any img, continue
            if len(os.listdir(infos['imgs'][info_ind])) == 0:
                no_img_skc.append(skc_id)
                continue
            # save data
            input_data = {'spu': datas['spu'][ind], 'skc_id': str(skc_id), 'imgs': infos['imgs'][info_ind], 'info': infos['info'][info_ind]}
            if isinstance(infos['info'][info_ind], str):
                input_info = json.loads(infos['info'][info_ind])
                # input_info['desc'] = remove_html_tags(input_info['desc']).strip()
                input_info['desc'] = remove_special_characters(input_info['desc'])  # remove repeat \n
                # input_info['desc'] = infos['desc'][info_ind]
                input_data['info'] = input_info
            all_datas.append(input_data)
        else:
            no_info_skc.append(skc_id)
    return all_datas, no_img_skc, no_info_skc, repeat_data


def remove_special_characters(res):
    # res: list
    # return: list
    res = re.sub(r'[!"#$%&\'*+,.:;<=>?@[\\]^_`{|}~• ]+', ' ', str(res))
    res = re.sub(r'\n+', r'\n', res)
    res = res.replace('</s>', '')
    res = res.replace(' Check. ', ' ')
    return res


def remove_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    cleaned_text = soup.get_text()
    return cleaned_text


def set_seed(seed):
    torch.manual_seed(seed)   # current CPU
    torch.cuda.manual_seed(seed)  # current GPU
    torch.cuda.manual_seed_all(seed)  # if you are using multi-GPU.
    np.random.seed(seed)  # Numpy module.
    random.seed(seed)  # Python random module.
    os.environ['PYTHONHASHSEED'] = str(seed)

    torch.backends.cudnn.benchmark = False # 禁用benchmark，保证可复现
    torch.backends.cudnn.deterministic = True  # 只限制benchmark的确定性


if __name__ == "__main__":
    skc_id_path = 'spu/overcoat->.xlsx'
    info_path = '../../datas/info.xlsx'
    all_datas = load_local_data(skc_id_path, info_path)


