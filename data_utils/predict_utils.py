import pandas as pd
import os


def format_save_info(product_info, save_root):
    """
    format and save all information to save root while infer
    """
    all_infos = {i: [] for i in ['spu', 'skc_id', 'link', 'merchantCategoryName', 'color_ori', 'feature', 'desc',
                                 'merchantId', 'imgs', 'videos', 'title', 'price', 'connectVideoCount',
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
    df.to_excel(os.path.join(save_root, 'info.xlsx'), index=False)
