import pandas as pd
import os
import multiprocessing
import json
from tqdm import tqdm
import numpy as np
import torch
import random


def format_save_info(product_info, save_root):
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
    df.to_excel(os.path.join(save_root, 'infos.xlsx'), index=False)


def load_local_data(data_path, info_path):
    all_datas = []
    datas = pd.read_excel(data_path).to_dict('list')
    infos = pd.read_excel(info_path).to_dict('list')
    for ind, skc_id in tqdm(enumerate(datas['skc_id'])):
        info_ind = infos['skc_id'].index(skc_id)
        input_data = {'spu': datas['spu'][ind],'skc_id': str(skc_id), 'imgs': infos['imgs'][info_ind], 'info': json.loads(infos['info'][info_ind])}
        all_datas.append(input_data)
    return all_datas


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


