import copy
import json
import os

import cv2
import pandas as pd

# import log
from log_config import get_logger
# from tagging import InitQwen
from tagging_llava import InitLLA
from utils import load_config, find_element_in_list, res_post_process, find_eles_in_list

logger = get_logger()


class Service:
    def __init__(self, questionjson):
        # self.initqw = InitQwen(iftest=False)
        self.initqw = InitLLA(iftest=False, )
        self.question = None
        self.category = None
        self.tag = None
        self.question = self.load_configs(questionjson)["qs"]
        self.utilquestion = self.load_configs(questionjson.replace('question', 'utils_question'))["Normalization"]
        self.q1_info = self.question[0]["first question"]
        self.version = None
        self.label_explain = pd.read_csv(questionjson.replace('question_bryce.json', 'label_question.csv'), header=0)
        print('self.label_explain', self.label_explain.columns.tolist())
        self.about_category = None
        self.about_label = None
        self.about_option = None
        self.if_multi = None

    def load_configs(self, questionjson):
        # load question.json
        with open(questionjson, 'r') as f:
            question = json.load(f)
        f.close()
        return question

    def load_label(self, version, categorycsv='category', tagcsv='tag'):

        if version == self.version:
            # load category and tag
            if self.category is None:
                self.category = load_config(version, categorycsv)
            if self.tag is None:
                self.tag = load_config(version, tagcsv)
            if self.main_item_tag is None:
                # self.main_item_tag = load_config(version,'main_item_tag')
                self.main_item_tag = {"item_main_key": {"cate_key": "subcategory", "label_key": "top key"}}
            if self.cate_key is None:
                self.cate_key = self.main_item_tag['item_main_key']['cate_key']
            if self.label_key is None:
                self.label_key = self.main_item_tag['item_main_key']['label_key']
        else:
            # load category and tag
            self.category = load_config(version, categorycsv)
            self.tag = load_config(version, tagcsv)
            # self.main_item_tag = load_config(version,'item_main_key')
            self.main_item_tag = {"item_main_key": {"cate_key": "subcategory", "label_key": "top key"}}
            self.cate_key = self.main_item_tag['item_main_key']['cate_key']
            self.label_key = self.main_item_tag['item_main_key']['label_key']
            self.version = version

        # if self.about_category is  None :
        #     self.about_category = pd.read_csv('/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/configs/label_question/about_category2.csv',skipinitialspace=True)
        # if self.about_label is None :
        #     self.about_label = pd.read_csv('/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/configs/label_question/about_label.csv',skipinitialspace=True)
        # if self.about_option is None :
        #     self.about_option =pd.read_csv('/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/configs/label_question/about_label.csv',skipinitialspace=True)

        # load the known knowledge about(first category, second category and all tags[common tags and specific tags])
        # the description about first category
        if self.about_category is None:
            self.about_category = pd.read_csv(
                '/root/autodl-tmp/autotagging/data_utils/definition/first_category.csv',
                skipinitialspace=True)
        # the description about all tags todo need to be updated
        if self.about_label is None:
            self.about_label = pd.read_csv(
                '/root/autodl-tmp/autotagging/data_utils/definition/categories.csv',
                skipinitialspace=True)
        # the description about second category
        if self.about_option is None:
            self.about_option = pd.read_csv(
                '/root/autodl-tmp/autotagging/data_utils/definition/second_category.csv',
                skipinitialspace=True)
        # the description about if the category is single or multi choice FIXME why not get from the phased tag url
        if self.if_multi is None:
            self.if_multi = pd.read_csv(
                '/root/autodl-tmp/autotagging/data_utils/definition/if_multi.csv',
                skipinitialspace=True)
            self.if_multi = self.if_multi[self.if_multi["is_multi"] == True]
            # logger.info(f'self.if_multi:{self.if_multi["label"].tolist()}')

        # print('============================self.category', self.category)

    def single_com(self, imagedir, info, pre_category_tag=True):
        # start handle img
        # start from top category
        q1_info = copy.deepcopy(self.q1_info)

        tag_res = []

        # ask first quesion 
        stepstr = q1_info["steps"].replace("refer_infomation", f'refer info: {info}')
        q1 = stepstr + q1_info["question"]
        # check imagedir
        imgs = os.listdir(imagedir)
        to_del = []
        if imgs != []:
            for img in imgs:
                img_res = cv2.imread(os.path.join(imagedir, img))
                if img_res is None:
                    to_del.append(os.path.join(imagedir, img))
            img_res = None
            for i in to_del:
                os.remove(i)

        res = self.initqw.tag_main(imagedir, q1)
        # get categorys
        main_key = ''  # main_key used as the known info(second category) while classify category tags
        curtag = ''

        logger.info('---------------------Start to predict first category and second category!------------------------')
        for t_c_key in self.category.keys():  # predict first category and second category
            logger.info(f'predict tag: {t_c_key}  tag options: {self.category[t_c_key]}')

            if isinstance((self.category[t_c_key][0]), str):  # predict first category
                curtag = self.single_label(t_c_key, curtag, self.category[t_c_key])
            elif isinstance((self.category[t_c_key][0]), list):
                curtag = self.single_label(t_c_key, curtag, self.category[t_c_key][curtag])
            elif isinstance((self.category[t_c_key][0]), dict):  # predict second category, 输入信息有冗余？
                top_cs = [list(i.keys())[0] for i in self.category[t_c_key]]
                if curtag in top_cs:
                    curtag = self.single_label(t_c_key, curtag, self.category[t_c_key][top_cs.index(curtag)][curtag])
                # curtag = self.single_label(t_c_key,curtag,self.category[t_c_key][curtag])

            tag_res.append({"label": t_c_key, "value": curtag})
            # print('tag_res',tag_res)
            logger.info(f'known information after predict: {tag_res}\n')

            # label_key_lowers = [i.lower() for i in self.tag[self.label_key]]
            # print('[self.tag] type', type(self.tag))
            # print('self.tag[self.label_key]', self.tag[self.label_key])

            for ll_label in self.tag[self.label_key]:

                if curtag.lower() == ll_label.lower():
                    main_key = ll_label
                    break

            # if curtag.lower() in  label_key_lowers:
            #     # print('curtag found for the current category',curtag)
            #     logger.info(f'curtag found for the current category:{curtag}')
            #     main_key = curtag
            #     main_key =self.tag[label_key_lowers.index(curtag.lower())]
        # get label
        if pre_category_tag:
            if main_key == '':
                # TODO if no features found for the current category, search all label
                tag_res.append({"label": 'eror happend', "value": 'No features found for the current category'})

                return tag_res

            curtag = main_key

            top_ls = [list(i.keys())[0] for i in self.tag['type']]
            if curtag in top_ls:
                l_index = top_ls.index(curtag)
            label_options = self.tag['type'][top_ls.index(curtag)][curtag]

            logger.info('---------------------Start to predict all category label!------------------------')
            for t_l_index, t_l_key_option in enumerate(label_options):  # predict common label and category label
                logger.info(f'predict tag and option choices: {t_l_key_option}')

                if isinstance(t_l_key_option, dict):
                    t_l_key = list(t_l_key_option.keys())[0]
                    # print('t_l_keyt_l_keyt_l_keyt_l_keyt_l_keyt_l_key',t_l_key)
                    if isinstance((t_l_key_option[t_l_key]), list):
                        curtag = self.single_label(t_l_key, main_key, t_l_key_option[t_l_key])

                    tag_res.append({"label": t_l_key, "value": curtag})

        return tag_res

    def check_about(self, t_key, curtag):
        t_key_desc = ''
        # print('t_keyt_keyt_keyt_keyt_key', t_key)
        if t_key in self.about_label["label"].tolist():
            print('t_key in self.about_label["label"].tolist():', self.about_label.columns.tolist())

            # label_desc = self.about_label[self.about_label["label"]==t_key]["explain"].dropna().tolist()

            # if label_desc != []:
            #     t_key_desc = t_key+" means "+ label_desc[0]
            label_desc = self.about_label[self.about_label["label"] == t_key]
            if label_desc.shape[0] != 0:
                for index, row in label_desc.iterrows():
                    logger.info('get row["options"]', row["options"], 'row["explain"]', row["explain"])
                    t_key_desc += str(row["options"]) + " means " + str(row["explain"]) + "\n"

        elif t_key == 'first category':
            category_desc = self.about_category
            # print("category_desc", self.about_category.shape)
            if category_desc.shape[0] != 0:
                for index, row in self.about_category.iterrows():
                    # print('row["category"]', row["category"])
                    t_key_desc += row["explain"] + "\n"
        elif t_key == 'subcategory':  # 需要使预测的tag能匹配到描述里的tag，tag得统一
            # print('t_key  in self.option["label"].tolist()',self.about_option.columns.tolist())
            all_attr = self.about_option[self.about_option["label"] == curtag]
            if all_attr.shape[0] != 0:
                for index, row in all_attr.iterrows():
                    t_key_desc += row["explain"] + "\n"
        return t_key_desc

    def single_label(self, t_key, curtag, options):
        # 在已知标签curtag的情况下，使用大模型在options选择需要预测的tag
        question_list = [copy.deepcopy(j) for j in self.question][1:]
        label_res = 'none'
        # we have multi question for one tag, if the easy question answered the question,
        # the process continue the rest process. if not, not_pre_num add 1 and asking the harder question
        not_pre_num = 0

        for question_i in question_list:
            lb = t_key + str(not_pre_num)
            question = list(question_i.values())[0]

            # t_key_ex = self.label_explain[self.label_explain["label"]==t_key][" explain"].dropna().tolist()
            # if t_key_ex != []:
            #     t_key_ex = t_key_ex[0]
            # else:
            #     t_key_ex = ''
            # t_key = t_key_ex if t_key_ex != '' else t_key

            # print('t_key',t_key)
            t_key_desc = ''

            t_key_desc = self.check_about(t_key, curtag)  # 生成当前已知tag下，需要生成tag的描述 似乎只有预测一级和二级标签使用

            if t_key_desc != "":
                qinfo = question["known_infomation"].replace("known_infomation", t_key_desc)
                qinfo += question["question"].replace("to_determin_attribute", t_key)
            else:
                qinfo = question["question"].replace("to_determin_attribute", t_key)
            if curtag != '':
                qinfo = qinfo.replace("merchandise", curtag.lower())

            qinfo = qinfo.replace("options", f"Options: {str(options).lower()}")
            qinfo = qinfo + question["constrains"]

            if t_key in self.if_multi["label"].tolist():  # single choose or multi choose

                qinfo = qinfo.replace("if_multi", "appropriate options")
                qinfo = qinfo.replace("an answer", "one or more answer you think is correct")
            else:
                qinfo = qinfo.replace("if_multi", "one option")

            tmpres = self.initqw.tag_main(lb, qinfo)
            tmpres = res_post_process(tmpres)
            if t_key in self.if_multi["label"].tolist():  # maybe the Ai answer is not in option, check and revise it
                label_res = find_eles_in_list(tmpres, options)
            else:
                label_res = find_element_in_list(tmpres, options)

            logger.info(f'tag: {t_key}  predict result: {tmpres}\n')
            # logger.info(f'all available tag: {label_res}\n\n')
            if label_res:
                break
            else:  # predict fail and then predict one more time in quick qa way
                qa = copy.deepcopy(self.utilquestion).replace("to_determain_sentence", tmpres)
                qa = qa.replace("to_chose_options", f'options:{str(options).lower()}')
                label_res = self.initqw.quick_qa(qa)  # todo，How it works, improve it
                print('label_res', label_res)
                label_res = res_post_process(label_res)

                if t_key in self.if_multi["label"].tolist():
                    label_res2 = find_eles_in_list(label_res, options)
                else:
                    label_res2 = find_element_in_list(label_res, options)

                print('label_res2', label_res2)
                logger.info('---------------------------')
                logger.info(f'label_res:{label_res}')
                logger.info(f'label_res2:{label_res2}')
                logger.info('---------------------------')
                if label_res2:
                    label_res = label_res2
                    break
                else:
                    not_pre_num += 1
                    if not_pre_num >= len(question_list):
                        label_res = ' '  # If the tag can not be predicted, return ' '
        return label_res

    def tag_main(self, imagedirs, product_info, version, categorycsv='category', tagcsv='label', pre_category_tag=True):

        try:
            # load category and tag
            self.load_label(version, categorycsv, tagcsv)   # FIXME repeat operation for different skc
            # print('=======================================start labeling==============================================')
            logger.info(
                '=======================================start labeling==============================================')
            # get tag
            # print('imgdir', imagedirs)
            logger.info(f'img dir:{imagedirs}')
            logger.info(f'input data: {product_info}')
            # if imagedirs  no img 
            tag = []
            if os.listdir(imagedirs) == []:
                logger.warning(f'no image found in {imagedirs}')
                tag = []
                return tag
            else:

                tag = self.single_com(imagedirs, product_info, pre_category_tag=pre_category_tag)  # predict all tags

                if type(tag) == str:
                    tag = []
                if 'eror happend' in [i['label'] for i in tag]:
                    tag = []

            return tag
        except Exception as e:
            # print('error',e)
            logger.info(f'error:{e}')
            logger.info(f'{e.__traceback__.tb_frame.f_globals["__file__"]}')
            logger.info(f'{e.__traceback__.tb_lineno}')
            return []
