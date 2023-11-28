import pandas


def read_xlx():
    xlx_path = '/root/autodl-tmp/autotagging/SPU_2.xlsx'
    data = pandas.read_excel(xlx_path, sheet_name='Sheet1').dropna(how='all')

    print(data.columns.tolist(),data.shape)
    half = int(data.shape[0]/2)+1
    print(half)


    return data['spu'].tolist()[101:]


# if __name__ == '__main__':
#     read_xlx()