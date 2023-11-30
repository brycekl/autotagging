import json

import pandas


def label_distribution(dataframe, label, pidkey=''):
    # this function use to  get  the distribution of the label，including  each label name and the number of each label
    # dataframe: the dataframe of the data
    # label: the colname of the data
    # return: the distribution of the label

    all_labels = dataframe[label].unique()

    label_distribution_res = {label: {}}
    for i in all_labels:
        label_distribution_res[label][i] = len(dataframe[dataframe[label] == i])

    return label_distribution_res


def label_distribution_all(dataframe):
    dataframe = dataframe.dropna(how='all')
    dataframe['product_id'] = dataframe['product_id'].astype(str)

    # this function use to  get  the distribution of the data，  each label name and the number of each label
    label_ress = {'first category': {}, 'subcategory': {}, "labels": {}}

    cols = dataframe.columns.tolist()
    print('cols', cols)
    cols.remove('idindex')
    cols.remove('product_url')
    cols.remove('product_id')
    for i in cols:
        print('i', i)
        if i == 'first category':
            tmp_res = label_distribution(dataframe, i)
            label_ress.update({'first category': tmp_res})
        else:
            all_tops = dataframe['first category'].unique()
            print('all_tops', all_tops)
            for j in all_tops:
                print('j', j)
                all_subs = dataframe[dataframe['first category'] == j]['subcategory'].unique()
                if i == 'subcategory':
                    tmp_res = label_distribution(dataframe[dataframe['first category'] == j], i)
                    label_ress['subcategory'].update({j: tmp_res})
                else:
                    label_ress["labels"][j] = label_ress["labels"].get(j, {})
                    for k in all_subs:
                        label_ress["labels"][j][k] = label_ress["labels"][j].get(k, [])
                        tmp_res = label_distribution(dataframe[dataframe['subcategory'] == k], i)
                        label_ress["labels"][j][k].append(tmp_res)

    return label_ress


if __name__ == "__main__":
    # test
    outpath = '/root/autodl-tmp/autotagging/taggingpipeline/test/label_distribution.json'
    filepath = '/root/autodl-tmp/tmp_res/tag_res/output/datav1_7_onlytops_1112_20231113_cl_cateall_latops_20231113_0238/20231113_cl_cateall_latops_20231113_0238_label_res_t.csv'
    data = pandas.read_csv(filepath)
    res = label_distribution_all(data)
    # save
    with open(outpath, 'w') as f:
        json.dump(res, f)
