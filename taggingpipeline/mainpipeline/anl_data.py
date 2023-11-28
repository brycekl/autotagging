import pandas as pd


def data_analysis(csvpath,outpath):
    # 读取CSV文件
    df = pd.read_csv(csvpath)  # 把 'your_file.csv' 替换成你的CSV文件名
    print(df.columns)
    # delete the first row
    # df = df.drop([0])
    # set the first row as the column name
    df.columns = df.iloc[0]
    print(df.columns)

    # delete the first row
    df = df.drop([0])
    print(df.columns)
    # 指定列名a
    col_a = 'title'  # 把 'a' 替换成你的实际列名
    # 查看指定列名a的列有多少个元素
    count_a = df[col_a].count()
    # 不重复项有多少个
    unique_count_a = df[col_a].nunique()
    print(f'商品数:{count_a}')
    print(f'spu :{unique_count_a}')

    # 指定列名b
    col_b = 'first category'  # 把 'b' 替换成你的实际列名

    # 查看指定列名b的列有多少个元素
    count_b = df[col_b].count()
    print(f"列 '{col_b}' 有 {count_b} 个元素")

    # 元素可能由逗号分隔，需要拆开，并获取每个元素有多少个
    # 首先，将所有元素合并成一个长字符串，然后用split方法分割
    all_elements = df[col_b].str.cat(sep=',')
    # 分割后的元素为字符串，这里需要转换为列表
    elements_list = all_elements.split(',')

    # 将elements_list转换为Series，以便于计数
    elements_series = pd.Series(elements_list)

    # 获取每个元素的计数
    element_counts = elements_series.value_counts()

    # 计算总元素数量，以便计算比例
    total_elements = len(elements_list)

    # 打印每个元素的数量和比例
    print(f"列 '{col_b}' 分割后的每个元素的数量和比例:")
    for element, count in element_counts.items():
        ratio = count / total_elements
        print(f"{element}: 数量 = {count}, 占比 = {ratio:.2%}")

    # 指定列名b
    col_b = 'subcategory'  # 把 'b' 替换成你的实际列名

    # 查看指定列名b的列有多少个元素
    count_b = df[col_b].count()
    print(f"列 '{col_b}' 有 {count_b} 个元素")

    # 元素可能由逗号分隔，需要拆开，并获取每个元素有多少个
    # 首先，将所有元素合并成一个长字符串，然后用split方法分割
    all_elements = df[col_b].str.cat(sep=',')
    # 分割后的元素为字符串，这里需要转换为列表
    elements_list = all_elements.split(',')

    # 将elements_list转换为Series，以便于计数
    elements_series = pd.Series(elements_list)

    # 获取每个元素的计数
    element_counts = elements_series.value_counts()

    # 计算总元素数量，以便计算比例
    total_elements = len(elements_list)

    # 打印每个元素的数量和比例
    print(f"列 '{col_b}' 分割后的每个元素的数量和比例:")
    for element, count in element_counts.items():
        ratio = count / total_elements
        print(f"{element}: 数量 = {count}, 占比 = {ratio:.2%}")


csvpath ='/root/autodl-tmp/autotagging/taggingpipeline/test_data/待标注数据_filter - SPU_1.csv'
outpath = '/root/autodl-tmp/autotagging/taggingpipeline/test_data/待标注数据_filter - SPU_1.csv'
data_analysis(csvpath,outpath)
