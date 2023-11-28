import pandas as pd
import numpy as np
import os
import sys
import json



def get_img(imgdir,csvpath,new_csvpath):
    # put imge path into csv file
    # imgdir: image directory
    # csvpath: csv file path
    # return: csv file path
    # read csv
    pddata = pd.read_csv(csvpath)

    print(pddata.columns.values)
    print(pddata['name'].values)

    for root, dirs, files in os.walk(imgdir):
        for file in files:
            if file.endswith('.png'):
                imgpath = os.path.join(root, file)
                filename = file.split('.')[0]
                # if  filename is in csv name, then add imgpath to csv image
                if filename in pddata['name'].values:
                    pddata.loc[pddata['name'] == filename, '图片'] = imgpath

    # save csv
    pddata.to_csv(new_csvpath)



if __name__ == "__main__":  
    imgdir = '/root/autodl-tmp/autotagging/taggingpipeline/test_data/tag_test'
    csvpath = '/root/autodl-tmp/autotagging/taggingpipeline/test_data/testdata.csv'
    new_csvpath = '/root/autodl-tmp/autotagging/taggingpipeline/test_data/testdata_new.csv'
    get_img(imgdir,csvpath,new_csvpath)

