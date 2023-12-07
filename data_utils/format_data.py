import os
import pandas as pd

all_attr = ['spu', 'skc_id', 'link', 'first_category', 'second_category', 'color_ori', 'COLOR', 'Saturation',
            'Brightness', 'MATERIAL', 'PATTERN', 'TRENDS', 'PROCESS', 'OCCASION', 'LOCATION', 'STYLE', 'SEASON',
            'Fit', 'Event', 'Neckline', 'Collar', 'Sleeve Shape', 'Sleeve Length', 'Cuff', 'Shoulder', 'Back', 'Waist',
            'Waistband', 'Length', 'Cut', 'Rise', 'Design']


def format_data(data_root, output_root, data_name):
    datas = pd.read_excel(f'{data_root}/{data_name}', sheet_name=None, converters={'skc_id': str})
    gt_ori = datas['gt'].to_dict('list')
    pre_ori = datas['pre'].to_dict('list')
    gt = {attr: [] for attr in all_attr}
    pre = {attr: [] for attr in all_attr}
    gt_nums = len(gt_ori['link'])
    pre_nums = len(pre_ori['link'])

    # complete all attributes
    for attr in gt:
        gt[attr] = gt_ori[attr] if attr in gt_ori else [None] * gt_nums
        pre[attr] = pre_ori[attr] if attr in pre_ori else [None] * pre_nums
        # number's length longer than 16 will be saved as 10e
        # gt['skc_id'] = list(map(str, gt['skc_id']))
        # pre['skc_id'] = list(map(str, pre['skc_id']))

    # copy attr which exist in ori but do not have in all_attr
    for attr in gt_ori:
        if attr not in gt:
            gt[attr] = gt_ori[attr]
    for attr in pre_ori:
        if attr not in pre:
            pre[attr] = pre_ori[attr]

    # complete gt' skc_id and spu from pre by using attribute link
    # not every pre data have been revised,
    if any(gt['spu'] + gt['skc_id']):
        for gt_ind in range(gt_nums):
            gt_link = gt['link'][gt_ind]
            pre_ind = pre['link'].index(gt_link) if gt_link in pre['link'] else -1
            if pre_ind == -1:
                raise gt_link
            gt['spu'][gt_ind] = pre['spu'][pre_ind]
            gt['skc_id'][gt_ind] = pre['skc_id'][pre_ind]

    gt_df = pd.DataFrame(gt)
    pre_df = pd.DataFrame(pre)
    with pd.ExcelWriter(f"{output_root}/{data_name}") as writer:
        gt_df.to_excel(writer, sheet_name='gt', index=False)
        pre_df.to_excel(writer, sheet_name='pre', index=False)


if __name__ == '__main__':
    """
    format the revised tags to one formation
    need to revise attrs of origin table：color_ori, COLOR, first_category, second_category
    """
    data_name = '11131204.xlsx'
    format_data('../output/origin', '../output', data_name)
