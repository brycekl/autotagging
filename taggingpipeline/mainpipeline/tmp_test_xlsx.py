import pandas


def read_xlx(spu_path='/root/autodl-tmp/autotagging/test.xlsx'):
    data = pandas.read_excel(spu_path, sheet_name='Sheet1').dropna(how='all')

    return data['spu'].tolist()

# if __name__ == '__main__':
#     read_xlx()
