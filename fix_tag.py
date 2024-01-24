import json
import sys

import pandas as pd

from taggingpipeline.mainpipeline.get_info_from_url import upload_tag_res


def revise_datas(data_path, merchandise_tag):
    """

    """
    data_excel = pd.read_excel(data_path).to_dict('list')
    data_excel['skc_id'] = list(map(str, data_excel['skc_id']))
    all_attributes = set(
        [attribute.lower() for merchandise in merchandise_tag for attribute in merchandise_tag[merchandise]])
    revised_data = {'spu': [], 'skc': [], 'firstCategory': [], 'subCategory': [], 'wrong': []}
    for ind, item_id in enumerate(data_excel['skc_id']):
        item = {i: data_excel[i][ind] for i in data_excel}
        item_category = item['category']
        wrong = []
        for attribute in item:
            attribute_low = attribute.lower()
            item_a = item[attribute]
            # 是属性，不在该商品属性中，且有值
            if attribute_low in all_attributes and attribute_low not in merchandise_tag[item_category].keys() \
                    and (isinstance(item_a, str) and item_a):
                data_excel[attribute][ind] = 'should be None'
                wrong.append(attribute)
        if wrong:
            for i, j in zip(revised_data, [item['spu'], item_id, item['一级分类'], item_category, wrong]):
                revised_data[i].append(j)
    return data_excel, revised_data


def upload_tags(revised_data, url='http://44.213.48.82:11181/product/skc/batchTagSkc'):
    gap = 20
    datas = []
    for i in range(len(revised_data['skc'])):
        datas = [] if i % gap == 0 else datas
        element = {'firstCategory': revised_data['firstCategory'][i],
                   'skcId': revised_data['skc'][i],
                   'subCategory': revised_data['subCategory'][i],
                   'tags': {i.lower(): [] for i in revised_data['wrong'][i]}}
        datas.append(element)
        if (i != 0 and (i + 1) % gap == 0) or i == len(revised_data['skc']) - 1:
            print(i, len(datas))
            datas = json.loads(json.dumps(datas))
            ifpost, message = upload_tag_res(url, datas)
            print(ifpost)


def main(tag_gt_path, data_path, output_root):
    _, _, _, merchandise_tag = phase_tag(tag_gt_path)
    revised_excel, revised_data = revise_datas(data_path, merchandise_tag)
    upload_tags(revised_data)
    revised_df = pd.DataFrame(revised_excel)
    revised_df.to_excel(f'{output_root}/out_excel.xlsx')
    revised_data_df = pd.DataFrame(revised_data)
    revised_data_df.to_excel(f'{output_root}/revise.xlsx')


if __name__ == '__main__':
    tag_gt_path = 'data_utils/tag_gt.json'
    if len(sys.argv) == 2:
        data_path = sys.argv[1]
        output_path = 'data_utils'
    elif len(sys.argv) == 3:
        data_path = sys.argv[1]
        output_path = sys.argv[2]
    else:
        data_path = 'data_utils/20231128_033311.xlsx'
        output_path = 'data_utils'
    main(tag_gt_path, data_path, output_path)
