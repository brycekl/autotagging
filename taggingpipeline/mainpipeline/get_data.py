import os
import time

import pandas
import requests


# input_data_q = Queue()

def read_database(data_path, outputtopdir, input_data_q):
    # if data_path is xlsx or csv，use pandas to read,if data_path is url ,use requests to read
    if data_path.endswith('xlsx') or data_path.endswith('csv'):
        datares = pandas.read_csv(data_path, header=[0, 1])
        datares = datares['t_product'][['id', 'title', 'imgs', 'desc', 'features', 'category', 'link']]
        for index, row in datares.iterrows():
            outputdir = os.path.join(outputtopdir, f'{row["id"]}_{time.strftime("%H_%M_%S")}')
            product_info = []
            imgs = []
            product_id = row['id']
            # dowload  imgs
            if row['imgs'] == '':
                imgs = []
            elif type(row['imgs']) == str:
                imgs = row['imgs'].split(',')
            elif type(row['imgs']) == list:
                imgs = row['imgs']
            imgs = download_data(imgs, outputdir)

            product_info = row[['title', 'desc', 'features', 'link']].to_dict()
            # convert product_info to str 

            input_data = {"id": product_id, "imgs": imgs, "info": product_info}
            input_data_q.put(input_data)

    # TODO if data_path is url ,use requests to read
    # else:
    #     data = requests.get(data_path)


def download_data(imgurl, outputdir):
    # download imgurl to outputdir
    imgs = []
    for img in imgurl:
        imgname = img.split('/')[-1]
        imgpath = os.path.join(outputdir, imgname)
        imgs.append(imgpath)
        if not os.path.exists(imgpath):
            with open(imgpath, 'wb') as f:
                f.write(requests.get(img, timeout=3).content)
            f.close()
    return imgs
