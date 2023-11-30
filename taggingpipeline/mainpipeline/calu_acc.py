import argparse
import json
import os

import pandas as pd


# from loguru import logger
# from log_config import get_logger


def calculate_accuracy(truth_data, pred_data):
    res = {}
    print('truth_data', truth_data)
    # 读取真值和预测值的数据
    if type(truth_data) == str:
        truth_df = pd.read_csv(truth_data)
        truth_df['product_id'] = truth_df['id'].astype(str)
    else:
        truth_df = truth_data
    print('truth_df', truth_df.shape)
    # truth_df.fillna('', inplace=True)

    if type(pred_data) == str:
        pred_df = pd.read_csv(pred_data)
    else:
        pred_df = pred_data
    print('pred_df', pred_df.shape)
    # pred_df.fillna('', inplace=True)

    # 确保商品ID是字符串，避免数值匹配问题
    truth_df['product_id'] = truth_df['id'].astype(str)
    truth_df.drop(['id'], axis=1, inplace=True)

    res['all truth'] = truth_df.shape[0]

    truth_cols = truth_df.columns

    pred_df['product_id'] = pred_df['product_id'].astype(str)
    pred_df.drop(['subcategory', 'idindex'], axis=1, inplace=True)
    pred_df['subcategory'] = pred_df['first category'].astype(str)

    pred_df.drop(['first category'], axis=1, inplace=True)
    pred_df['first category'] = pred_df['top category'].astype(str)
    pred_df.drop(['top category', 'CUT'], axis=1, inplace=True)
    pred_df.rename(columns={'product_url': 'link', 'Cut': 'CUT'}, inplace=True)
    # pred_df.drop(['top category'], axis=1, inplace=True)
    # pred_df.rename(columns={'product_url':'link'}, inplace = True)

    # print('pred_df.columns.tolist()',pred_df.columns.tolist())

    res['all pred'] = pred_df.shape[0]

    # 合并两个数据集

    merged_df = pd.merge(truth_df, pred_df, on='product_id', suffixes=('_truth', '_pred'), how='inner')

    # merged_df = merged_df[['title','error happend','LENGTH_truth','BACK_truth','link_truth', 'first category_truth', 'subcategory_truth', 'product_id','BACK_pred', 'LENGTH_pred']]
    # convert all to lower
    for col in merged_df.columns.tolist():
        if (col != 'product_id') and (col != 'link') and (col != 'title'):
            merged_df[col] = merged_df[col].str.lower().replace('-', '')

    print('merged_df', merged_df.columns.tolist())

    print('merged_df.shape', merged_df.shape)

    res['all merged'] = merged_df.shape[0]

    # 找到标注失败的列
    columns1 = set(truth_cols)
    columns2 = set(pred_df.columns)

    # 找出不同的列名
    di = columns1.symmetric_difference(columns2)
    print('di', di)
    different_columns = ['error happend', 'current category']
    # different_columns = ['error happend']

    # print('different_columns',different_columns)
    res['failed'] = {'failed account': len(different_columns)}
    # 找到 different_columns 列不为空的所有行
    failed_rows = merged_df[merged_df[different_columns].notnull().any(axis=1)]

    # 找到 failed_rows 中的id 
    failed_ids = failed_rows['product_id'].tolist()
    # print('failed_ids',failed_ids)
    res['failed']['failed ids'] = failed_ids
    # 在 merged_df 中删除 failed_rows
    merged_df = merged_df[~merged_df['product_id'].isin(failed_ids)]
    print('merged_df shape', merged_df.shape)

    # 计算每件衣服的准确率
    individual_accuracy = {}
    category_accuracy = {}
    category_recall = {}
    category_recall_single = {}
    category_recall_multie = {}
    category_p = {}
    error_res = {}
    category_accurac_fp = {}
    total_res = {}

    # 遍历每件商品
    for index, row in merged_df.iterrows():
        product_id = row['product_id']
        error_res[product_id] = {}
        # print('row',row)
        # print('product_id',product_id)
        correct_count = 0
        total_tags = 0

        # truth_cols = ['BACK','LENGTH']

        # print('truth_cols',truth_cols)

        # 对每个标签进行准确率检查
        for col in truth_cols:
            if (col != 'product_id') and (col != 'link') and (col != 'title'):  # 忽略商品ID列
                # print('colcol',col)
                truth_value = row[col + '_truth']
                pred_value = row[col + '_pred']
                # print('truth_value:',truth_value,'pred_value:',pred_value)

                if not pd.isna(truth_value):
                    total_tags += 1
                    if (not pd.isna(pred_value)):
                        if pred_value.lower() == truth_value.lower():
                            # print('got id',product_id,'truth_value',truth_value,'pred_value',pred_value)
                            correct_count += 1
                            category_recall[col] = category_recall.get(col, 0) + 1
                            category_recall_single[col] = category_recall_single.get(col, 0) + 1
                            category_accuracy[col] = category_accuracy.get(col, 0) + 1
                            category_p[col] = category_recall.get(col, 0) + 1
                        elif len(truth_value.split(',')) >= 2:
                            tt_values = list(set([i.lower() for i in truth_value.split(',')]))
                            for tt_value in tt_values:
                                if pred_value.lower() == tt_value:
                                    # print('got id mlti',product_id,'truth_value',truth_value,'pred_value',pred_value)
                                    correct_count += 1
                                    category_recall[col] = category_recall.get(col, 0) + 1
                                    category_recall_multie[col] = category_recall_multie.get(col, 0) + 1
                                    category_accuracy[col] = category_accuracy.get(col, 0) + 1
                                    category_p[col] = category_recall.get(col, 0) + 1
                                    break
                        else:
                            # error_res[product_id][col] = {'true':truth_value,'pred_value:':pred_value}
                            error_res[product_id][col] = {'true': truth_value, 'pred_value:': pred_value}
                            error_res[product_id]['first category value '] = {'true': row['first category_truth'],
                                                                              'pred_value:': row['first category_pred']}
                            error_res[product_id]['subcategory value'] = {'true': row['subcategory_truth'],
                                                                          'pred_value:': row['subcategory_pred']}

                    else:
                        error_res[product_id][col] = {'true': truth_value, 'pred_value:': pred_value, }
                        error_res[product_id]['first category value'] = {'true': row['first category_truth'],
                                                                         'pred_value:': row['first category_pred']}
                        error_res[product_id]['subcategory value'] = {'true': row['subcategory_truth'],
                                                                      'pred_value:': row['subcategory_pred']}



                else:
                    if pd.isna(pred_value):
                        correct_count += 1
                        # category_recall[col] = category_recall.get(col, 0) + 1
                        category_p[col] = category_recall.get(col, 0) + 1
                        category_accuracy[col] = category_accuracy.get(col, 0) + 1
                    else:
                        category_accurac_fp[col] = category_accurac_fp.get(col, 0) + 1

        individual_accuracy[product_id] = correct_count / total_tags if total_tags > 0 else None

    # 计算每个类别召回率 tp/(tp+fn)
    for category in category_recall:

        category_p = merged_df[category + '_truth'].count()  # 只计算非NaN的值 # tp+fn
        print('category', category, 'category_p', category_p)
        # category_p = merged_df[category + '_truth'].count()  # 只计算非NaN的值 # tp+fn
        # category_p = merged_df.shape[0]
        # print('all',f'category_recall[{category}]:',category_recall[category],f'category_p[{category}]:',category_p[category])
        # category_recall[category] = category_recall[category] / category_p[category]
        # if category in category_recall_multie:
        #     category_recall_multie[category] = category_recall_multie[category] / category_p[category]
        # if category in category_recall_single:
        #     category_recall_single[category] = category_recall_single[category] / category_p[category]
        category_recall[category] = category_recall[category] / category_p
        if category in category_recall_multie:
            category_recall_multie[category] = category_recall_multie[category] / category_p
        if category in category_recall_single:
            category_recall_single[category] = category_recall_single[category] / category_p

    # 计算每个类别准确率 (tp+tn)/(tp+fn+fp+fn)

    for category in category_accuracy:

        # 计算包括none 的值
        # category_pn = merged_df[merged_df[category + '_truth']]
        # # 计算包括none 的行数
        # print('category_pn',category_pn.shape)
        # category_pn = merged_df.shape[0]

        category_pn = merged_df[category + '_truth'].count()
        if category in category_accurac_fp:
            category_pn += category_accurac_fp[category]

        category_accuracy[category] = category_accuracy[category] / category_pn

    # res['individual_accuracy'] = individual_accuracy
    res['category_accuracy'] = category_accuracy
    res['category_recall'] = category_recall
    res['category_recall_single'] = category_recall_single
    res['category_recall_multie'] = category_recall_multie

    # res['error'] = error_res

    return failed_rows, merged_df, res, individual_accuracy, error_res


def merge_truth_pred(truth_data, pred_data):
    res = {}
    print('truth_data', truth_data)
    # 读取真值和预测值的数据
    if type(truth_data) == str:
        truth_df = pd.read_csv(truth_data)
        truth_df['product_id'] = truth_df['id'].astype(str)
    else:
        truth_df = truth_data
    print('truth_df', truth_df.shape)
    # truth_df.fillna('', inplace=True)

    if type(pred_data) == str:
        pred_df = pd.read_csv(pred_data)
    else:
        pred_df = pred_data
    print('pred_df', pred_df.shape)
    # pred_df.fillna('', inplace=True)

    # 确保商品ID是字符串，避免数值匹配问题
    truth_df['product_id'] = truth_df['id'].astype(str)
    truth_df.drop(['id'], axis=1, inplace=True)

    res['all truth'] = truth_df.shape[0]

    truth_cols = truth_df.columns

    pred_df['product_id'] = pred_df['product_id'].astype(str)
    pred_df.drop(['subcategory', 'idindex'], axis=1, inplace=True)
    pred_df['subcategory'] = pred_df['first category'].astype(str)

    pred_df.drop(['first category'], axis=1, inplace=True)
    pred_df['first category'] = pred_df['top category'].astype(str)
    pred_df.drop(['top category', 'CUT'], axis=1, inplace=True)
    pred_df.rename(columns={'product_url': 'link', 'Cut': 'CUT'}, inplace=True)
    # pred_df.drop(['top category'], axis=1, inplace=True)
    # pred_df.rename(columns={'product_url':'link'}, inplace = True)

    # print('pred_df.columns.tolist()',pred_df.columns.tolist())
    res['all pred'] = pred_df.shape[0]

    # 合并两个数据集

    merged_df = pd.merge(truth_df, pred_df, on='product_id', suffixes=('_truth', '_pred'), how='inner')

    # merged_df = merged_df[['title','error happend','LENGTH_truth','BACK_truth','link_truth', 'first category_truth', 'subcategory_truth', 'product_id','BACK_pred', 'LENGTH_pred']]

    print('merged_df', merged_df.columns.tolist())
    print('merged_df.shape', merged_df.shape)
    # convert all to lower
    for col in merged_df.columns.tolist():
        if (col != 'product_id') and (col != 'link') and (col != 'title'):
            merged_df[col] = merged_df[col].str.lower().replace('-', '')

    return merged_df, truth_cols, pred_df


def find_label_error(merged_df):
    # 找到标注失败的列
    different_columns = ['error happend', 'current category']
    # different_columns = ['error happend']

    # print('different_columns',different_columns)
    res['failed'] = {'failed account': len(different_columns)}
    # 找到 different_columns 列不为空的所有行
    failed_rows = merged_df[merged_df[different_columns].notnull().any(axis=1)]

    # 找到 failed_rows 中的id 
    failed_ids = failed_rows['product_id'].tolist()
    # print('failed_ids',failed_ids)
    res['failed']['failed ids'] = failed_ids
    return failed_rows, merged_df, failed_ids


# def calculate_recall_prestion(truth_data, pred_data):

#     merged_df,truth_cols,pred_df = merge_truth_pred(truth_data, pred_data)
#     res['all merged'] = merged_df.shape[0]
#     failed_rows,merged_df,failed_ids = find_label_error(merged_df)

#     # 在 merged_df 中删除 failed_rows
#     merged_df = merged_df[~merged_df['product_id'].isin(failed_ids)]
#     print('merged_df shape',merged_df.shape)

#     # 计算每件衣服的准确率
#     individual_accuracy = {}
#     category_accuracy = {}
#     category_recall = {}
#     category_recall_single = {}
#     category_recall_multie = {}
#     category_p ={}
#     error_res = {}
#     category_accurac_fp ={}
#     total_res = {}

#     presipion_res = {}
#     recall_res = {}
#     f1_res = {}
#     common_res = {}
#     cls_res = {}

#     common_label_res = {}
#     cls_res_label_re = {}

#     cate_data = json.load(open('/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/configs/20231103_cl/category.json','r'))


#     # get  top category 
#     # total_res['top category'] ={}
#     # 对每个分类进行准确率检查
#     # for col in truth_cols:
#     #     if (col != 'product_id') and  (col != 'link')  and (col != 'title'):  # 忽略商品ID列
#     #         tmp_df = merged_df[merged_df[col + '_truth'].notnull()]
#     #         if tmp_df.shape[0] > 0:
#     #             truth_value = tmp_df[col + '_truth'].tolist()
#     #             pred_value = tmp_df[col + '_pred'].tolist()
#     #             common_res[col] = confusion_matrix(truth_value, pred_value)
#     #             cls_res[col] = classification_report(truth_value, pred_value)
#     #     if col in ['top category','subcategory']:
#     #         all_cates = cate_data[col]
#     #         for cate in all_cates:
#     #             tmp_df = merged_df[merged_df[col] == cate]
#     #             if tmp_df.shape[0] > 0:
#     #                 truth_value = [i.tmp_df[col+ '_truth'].tolist()]
#     #                 pred_value = tmp_df[col+ '_pred'].tolist()
#     #                 common_label_res[col] = confusion_matrix(truth_value, pred_value)
#     #                 cls_res_label_re[col] = classification_report(truth_value, pred_value)


#     # 遍历每件商品
#     for index, row in merged_df.iterrows():
#         product_id = row['product_id']
#         error_res[product_id] ={}
#         correct_count = 0
#         total_tags = 0

#         # 对每个标签进行准确率检查
#         for col in truth_cols:
#             if (col != 'product_id') and  (col != 'link')  and (col != 'title'):  # 忽略商品ID列
#                 total_res[col] ={}
#                 truth_value = row[col + '_truth']
#                 pred_value = row[col + '_pred']
#                 total_res[row['top category_truth']]= total_res.get(row['top category_truth'],{})
#                 if not pd.isna(truth_value) :
#                     truth_vs = truth_value.split(',')
#                     # truth_vs = [i.lower().replace('-','') for i in truth_vs]

#                     # get p
#                     for truth_v in truth_vs:
#                         if col == 'top category':
#                             total_res[col][truth_v]['t'] = total_res[col][truth_v].get('t', 0) + 1
#                         else:
#                             total_res[row['top category_truth']][truth_v]['t'] = total_res[row['top category_truth']][truth_v].get('t', 0) + 1

#                     total_tags += 1
#                     if (not pd.isna(pred_value)) : 
#                         pred_vs = pred_value.split(',')
#                         # pred_vs = [i.lower().replace('-','') for i in pred_vs]

#                         for pred_v in pred_vs:
#                             if col == 'top category':
#                                 total_res[col][truth_v]['p'] = total_res[col][truth_v].get('p', 0) + 1
#                             else:
#                                 total_res[row['top category_pred']][truth_v]['p'] = total_res[row['top category_pred']][truth_v].get('p', 0) + 1

#                             if  pred_v in truth_vs:
#                                 correct_count += 1
#                                 # get tp
#                                 if col == 'top category':
#                                     total_res[col][truth_v]['tp'] = total_res[col][truth_v].get('tp', 0) + 1
#                                 else:
#                                     if row['top category_pred']in row['top category_truth'].split(','):
#                                     # compare top category
#                                         total_res[row['top category_truth']][truth_v]['tp'] = total_res[row['top category_truth']][truth_v].get('tp', 0) + 1
#                             else:
#                                 # get fp
#                                 if col == 'top category':
#                                     total_res[col][truth_v]['fn'] = total_res[col][truth_v].get('fn', 0) + 1
#                                 else:
#                                     if row['top category_pred']in row['top category_truth'].split(','):
#                                         total_res[row['top category_truth']][truth_v]['fn'] = total_res[row['top category_truth']][truth_v].get('fn', 0) + 1

#                                 error_res[product_id][col] = {'true':truth_value,'pred_value:':pred_value}


#         # get each f and n
#         for key1 in total_res.keys():


#                 # else:
#                 #     if pd.isna(pred_value):
#                 #         correct_count += 1
#                 #         # category_recall[col] = category_recall.get(col, 0) + 1
#                 #         category_p[col] = category_recall.get(col, 0) + 1
#                 #         category_accuracy[col] = category_accuracy.get(col, 0) + 1
#                 #     else:
#                 #         category_accurac_fp[col] = category_accurac_fp.get(col, 0) + 1


#         individual_accuracy[product_id] = correct_count / total_tags if total_tags > 0 else None


#     # 计算每个类别召回率 tp/(tp+fn)
#     for category in category_recall:

#         category_p = merged_df[category + '_truth'].count()  # 只计算非NaN的值 # tp+fn
#         print('category',category,'category_p',category_p)
#         # category_p = merged_df[category + '_truth'].count()  # 只计算非NaN的值 # tp+fn
#         # category_p = merged_df.shape[0]
#         # print('all',f'category_recall[{category}]:',category_recall[category],f'category_p[{category}]:',category_p[category])
#         # category_recall[category] = category_recall[category] / category_p[category]
#         # if category in category_recall_multie:
#         #     category_recall_multie[category] = category_recall_multie[category] / category_p[category]
#         # if category in category_recall_single:
#         #     category_recall_single[category] = category_recall_single[category] / category_p[category]
#         category_recall[category] = category_recall[category] / category_p
#         if category in category_recall_multie:
#             category_recall_multie[category] = category_recall_multie[category] / category_p
#         if category in category_recall_single:
#             category_recall_single[category] = category_recall_single[category] / category_p


#     # 计算每个类别准确率 (tp+tn)/(tp+fn+fp+fn)

#     for category in category_accuracy:

#         # 计算包括none 的值
#         # category_pn = merged_df[merged_df[category + '_truth']]
#         # # 计算包括none 的行数
#         # print('category_pn',category_pn.shape)
#         # category_pn = merged_df.shape[0]

#         category_pn = merged_df[category + '_truth'].count()
#         if category in category_accurac_fp:
#             category_pn += category_accurac_fp[category]


#         category_accuracy[category] = category_accuracy[category] / category_pn


#     # res['individual_accuracy'] = individual_accuracy
#     res['category_accuracy'] = category_accuracy
#     res['category_recall'] = category_recall
#     res['category_recall_single'] = category_recall_single
#     res['category_recall_multie'] = category_recall_multie


#     # res['error'] = error_res


#     return failed_rows,merged_df,res,individual_accuracy,error_res

def merge_dataframes_with_suffix(df1, df2, key_column, suffixes=('_1', '_2'), how='outer'):
    """
    合并两个DataFrame，基于指定的列名，并为重复的列名添加后缀。
    
    :param df1: 第一个DataFrame
    :param df2: 第二个DataFrame
    :param key_column: 用作合并基础的列名
    :param suffixes: 重复列名的后缀元组，默认为('_x', '_y')
    :param how: 合并的方式，默认为'outer'，可选'left', 'right', 'inner', 'outer'
    :return: 合并后的DataFrame，包含后缀处理过的重复列名
    """
    # 使用指定的列名、后缀和合并方法来合并两个DataFrame
    merged_df = pd.merge(df1, df2, on=key_column, how=how, suffixes=suffixes)

    # 将结果中的NaN替换为空字符串表示空白
    # merged_df.fillna('', inplace=True)

    return merged_df


def merge_columns(df, name_1, name_2, new_column):
    if name_1 in df.columns and name_2 in df.columns:
        df[new_column] = df[name_1]
        df[new_column] = df[new_column].str.cat(df[name_2], sep=',')
    # 将结果中的NaN替换为空字符串表示空白
    # merged_df.fillna('', inplace=True)

    return df


def merge_and_unique_columns(df, col1, col2, separator=','):
    # Merge the columns with the separator and then apply a set on the split to remove duplicates
    return df.apply(lambda row: separator.join(set(str(row[col1]).split(separator) + str(row[col2]).split(separator))),
                    axis=1)


def getmergedf(resoutput_dir):
    # 合并 spu_1和spu_2
    data1 = '/root/autodl-tmp/autotagging/taggingpipeline/test/SPU_1_2.csv'
    data2 = '/root/autodl-tmp/autotagging/taggingpipeline/test/SPU_2_2.csv'

    # 转换成DataFrame
    df1 = pd.read_csv(data1)
    # df1.columns = df1.iloc[0]

    print(df1.columns)
    # 删掉指定列
    df1['id'] = df1['id'].astype('str')
    df1.drop(['title', 'cn_name', 'en_name'], axis=1, inplace=True)
    # print(df1.columns)
    df2 = pd.read_csv(data2)
    # df2.columns = df2.iloc[0]
    df2['id'] = df2['id'].astype('str')
    df2.drop(['title', 'cn_name', 'en_name'], axis=1, inplace=True)

    linkcol = df1['link (双击单元格可以将纯文本转成可以点击跳转的链接)']
    df1.drop(['link (双击单元格可以将纯文本转成可以点击跳转的链接)'], axis=1, inplace=True)
    df2.drop(['link (双击单元格可以将纯文本转成可以点击跳转的链接)'], axis=1, inplace=True)
    key_column = 'id'

    # 合并DataFrame，指定合并列和重复列名的后缀
    merged_df = merge_dataframes_with_suffix(df1, df2, key_column)
    merged_df['link'] = linkcol
    # print(merged_df.columns)
    # merged_df = merge_columns(merged_df, 'first category_1','first category_2', new_column='first category')
    # merged_df = merge_columns(merged_df, 'subcategory_1','subcategory_2', new_column='subcategory')

    merged_df['first category'] = merge_and_unique_columns(merged_df, 'first category_1', 'first category_2')
    merged_df['subcategory'] = merge_and_unique_columns(merged_df, 'subcategory_1', 'subcategory_2')

    merged_df.drop(['first category_1', 'first category_2', 'subcategory_1', 'subcategory_2', 'title.1_2'], axis=1,
                   inplace=True)
    # 去掉列名为空的列
    merged_df = merged_df.dropna(axis=1, how='all')
    merged_df.rename(columns={'Season': 'SEASON', 'Cut': 'CUT', 'BACK STYLE': 'BACK', 'title.1_1': 'title'},
                     inplace=True)
    # 删掉第一行
    merged_df.drop([0], inplace=True)
    # print(merged_df.columns.tolist())

    merged_df.to_csv(os.path.join(resoutput_dir, 'merge_all.csv'), index=False)

    return merged_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--truth_path', type=str,
                        default='/root/autodl-tmp/autotagging/taggingpipeline/data/data_1/datav1_5_cloth.csv',
                        help='url')
    parser.add_argument('--prediction_path', type=str,
                        default='/root/autodl-tmp/tmp_res/tag_res/output/data1_6_1106_20231103_cl_20231109_0024/20231103_cl_20231109_0024_label_res_t.csv',
                        help='res_dir')
    # parser.add_argument('--prediction_path', type=str, default='/root/autodl-tmp/tmp_res/tag_res/output/data1_6_1106_20231103_cl_20231108_1023/20231103_cl_20231108_1023_label_res_t.csv', help='res_dir')
    parser.add_argument('--resoutput_dir', type=str,
                        default='/root/autodl-tmp/autotagging/taggingpipeline/test/acc/1109_1347', help='res_dir')

    args = parser.parse_args()

    if not os.path.exists(args.resoutput_dir):
        os.makedirs(args.resoutput_dir)

    merged_df = getmergedf(args.resoutput_dir)

    # merged_df = '/root/autodl-tmp/autotagging/taggingpipeline/test/acc/merge_all.csv'
    merged_df.to_csv(os.path.join(args.resoutput_dir, 'merged_df.csv'), index=False)

    # pred1 = pd.read_csv(args.prediction_path)
    # # pred1.columns = pred1.iloc[0]
    # print('pred1.columns',pred1.columns)
    # # 删掉指定列
    # pred1['product_id'] = pred1['product_id'].astype('str')

    # pred2 = pd.read_csv('/root/autodl-tmp/autotagging/taggingpipeline/output/data1_6_1106_part2_20231103_cl_20231106_1921/20231103_cl_20231106_1921_label_res_t.csv')
    # # pred1.columns = pred1.iloc[0]
    # print('pred2.columns',pred2.columns)
    # # 删掉指定列
    # pred2['product_id'] = pred2['product_id'].astype('str')

    # common_rows = pred1.merge(pred2, on='product_id', how='inner')

    # 如果存在公共行，则从df1中删除它们
    # if not common_rows.empty:
    #     # 使用merge的indicator参数来找出df1独有的行
    #     # pred1 = pred1.merge(pred2.drop_duplicates(), on='product_id', how='left', indicator=True).loc[lambda x: x['_merge'] == 'left_only']
    #     # pred1 = pred1.drop(columns=['_merge'])  # 删除辅助列
    #     print('============',pred1.columns)

    #     #
    #     idds = pred2['product_id'].tolist()
    #     print('idds',idds)
    #     # for idddd in idds:
    #     # pred1 = pred1.drop(pred1[pred1['product_id']] in idds )
    #     pred1 = pred1.loc[~pred1['product_id'].isin(idds)]

    # print('============',pred1.shape)

    # 将df2追加到df1后
    # pred1 = pred1.append(pred2, ignore_index=True)
    # result_df = pd.concat([pred1, pred2], ignore_index=True,axis=0 )

    # 保存结果
    # result_df.to_csv(os.path.join(args.resoutput_dir,'merge_predddd.csv'),index=False)

    # 调用函数计算准确率
    # failed_rows,merged_df,res = calculate_accuracy(merged_df,os.path.join(args.resoutput_dir,'merge_predddd.csv'))
    failed_rows, mergedd_df, res, individual_accuracy, error_res = calculate_accuracy(merged_df, args.prediction_path)

    # save failed_rows
    failed_rows.to_csv(os.path.join(args.resoutput_dir, 'failed_rows.csv'), index=False)
    # save merged_df
    mergedd_df.to_csv(os.path.join(args.resoutput_dir, 'mergees_label_val.csv'), index=False)
    # save res
    with open(os.path.join(args.resoutput_dir, 'res.json'), 'w') as f:
        f.write(json.dumps(res))

    with open(os.path.join(args.resoutput_dir, 'individual_accuracy.json'), 'w') as f:
        f.write(json.dumps(individual_accuracy))

    with open(os.path.join(args.resoutput_dir, 'error_res.json'), 'w') as f:
        f.write(json.dumps(error_res))
