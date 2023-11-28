import pandas as pd

def filter_rows_by_string(dataframe, column_name, string_to_search, case_sensitive=True
                          ):
    """
    筛选出包含指定字符串的行

    :param dataframe: 要筛选的DataFrame
    :param column_name: 需要搜索字符串的列名
    :param string_to_search: 要搜索的字符串
    :param case_sensitive: 是否区分大小写，默认为False（不区分大小写）
    :return: 筛选后的DataFrame
    """
    if case_sensitive:
        # 区分大小写
        return dataframe[dataframe[column_name].str.contains(string_to_search, na=False)]
    else:
        # 不区分大小写
        return dataframe[dataframe[column_name].str.contains(string_to_search, case=False, na=False)]


def merge_dataframes_with_suffix(df1, df2, key_column, suffixes=('_sam', '_yz'), how='outer'):
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
    merged_df.fillna('', inplace=True)
    
    return merged_df


data1 = '/root/autodl-tmp/autotagging/taggingpipeline/test/SPU_1.csv'

data2 ='/root/autodl-tmp/autotagging/taggingpipeline/test/SPU_2.csv'

# 转换成DataFrame
df1 = pd.read_csv(data1,header=1)
df1.columns = df1.iloc[0]
df1 = df1[['id','link (双击单元格可以将纯文本转成可以点击跳转的链接)','first category','subcategory']]
df1['id'] = df1['id'].astype('str')
print(df1.columns)
df2 = pd.read_csv(data2,header=1)
df2.columns = df2.iloc[0]
df2 = df2[['id','link (双击单元格可以将纯文本转成可以点击跳转的链接)','first category','subcategory']]
df2['id'] = df2['id'].astype('str')


key_column = 'id'

all_elements = df1['first category'].str.cat(sep=',')
# 分割后的元素为字符串，这里需要转换为列表
elements_list =list(set(all_elements.split(',')))

for ele in elements_list:
    print(ele)
    df11 = filter_rows_by_string(df1, 'first category', ele)
    df21 = filter_rows_by_string(df2, 'first category', ele)

    if df11.shape[0] == 0 :
        print(f'df1 is no {ele} ')
        continue
    elif df21.shape[0] == 0:
        print(f'df2 is no {ele} ')
        continue
    else:
        # 合并DataFrame，指定合并列和重复列名的后缀
        merged_df = merge_dataframes_with_suffix(df11, df21, key_column)
        # save to csv 
        if ele == 'LOUNGE/PAJAMAS':
            merged_df.to_csv(f'/root/autodl-tmp/autotagging/taggingpipeline/test/merged_lounge+pajamas.csv',index=False)
        else:
            merged_df.to_csv(f'/root/autodl-tmp/autotagging/taggingpipeline/test/merged_{ele}.csv',index=False)







print(merged_df)
