import copy
import json
import os

import cv2
import pandas as pd

# import log
from log_config import get_logger
# from tagging import InitQwen
from tagging_llava import InitLLA
from utils import load_config, find_element_in_list, res_post_process, find_eles_in_list, load_all_tags_map

logger = get_logger()
with open('data_utils/definition/add_def.json') as reader:
    revised_info = json.load(reader)


class Service:
    def __init__(self, questionjson):
        # self.initqw = InitQwen(iftest=False)
        self.initqw = InitLLA(iftest=False, )

        self.question = self.load_configs(questionjson)["qs"]
        self.utilquestion = self.load_configs(questionjson.replace('question', 'utils_question'))["Normalization"]
        self.q1_info = self.question[0]["first question"]
        self.label_explain = pd.read_csv(questionjson.replace('question_bryce.json', 'label_question.csv'), header=0)
        print('self.label_explain', self.label_explain.columns.tolist())
        self.version = None
        self.category_map = None
        self.common_tag_map = None
        self.category_tag_map = None
        self.choose_item_map = None
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

    def load_label(self, version):

        if self.version is None:
            # load category and tag
            # self.category = load_config(version, categorycsv)
            # self.tag = load_config(version, tagcsv)
            category_map, common_tag_map, category_tag_map, choose_item_map = load_all_tags_map(version)
            self.category_map = category_map
            self.common_tag_map = common_tag_map
            self.category_tag_map = category_tag_map
            self.choose_item_map = choose_item_map
            self.version = version

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
            self.if_multi = []
            for attr, choose in self.choose_item_map.items():
                if choose == 'multi':
                    self.if_multi.append(attr)

        # print('============================self.category', self.category)

    def single_com(self, imagedir, info, item_gt=None, pre_common_tag=True, pre_category_tag=True):
        # start handle img
        # start from top category
        q1_info = copy.deepcopy(self.q1_info)

        tag_res = {}

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

        # get the overall information about this item
        res = self.initqw.tag_main(imagedir, q1)

        logger.info('---------------------Start to predict first category and second category!------------------------')
        first_category_options = list(self.category_map.keys())[::-1]
        first_category = self.single_label('first category', '', first_category_options, tag_res, item_gt)

        subcategory_options = self.category_map[first_category]
        subcategory = self.single_label('subcategory', first_category, subcategory_options, tag_res, item_gt)

        if pre_common_tag:
            logger.info('---------------------Start to predict common tag!------------------------')
            for pre_attr, options in self.common_tag_map.items():
                self.single_label(pre_attr, subcategory, options, tag_res, item_gt)

        if pre_category_tag and len(self.category_tag_map[subcategory]) != 0:
            logger.info('---------------------Start to predict category tag!------------------------')
            for pre_attr, options in self.category_tag_map[subcategory].items():
                self.single_label(pre_attr, subcategory, options, tag_res, item_gt)

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

    def single_label(self, t_key, curtag, options, predict_result, item_gt=None):
        # 如果预测标签不是一类、二类标签或通用标签且一类/二类预测出错，品类标签直接返回nan
        if (t_key not in ['first category', 'subcategory'] + list(self.common_tag_map.keys()) and
                (item_gt['first category'] != predict_result['first category'] or
                 item_gt['subcategory'] != predict_result['subcategory'])):
            predict_result[t_key] = 'nan'
            return 'nan'
        # 在已知标签curtag的情况下，使用大模型在options选择需要预测的tag
        question_list = [copy.deepcopy(j) for j in self.question][1:]
        label_res = 'none'

        # we have multi question for one tag, if the easy question answered the question,
        # the process continue the rest process. if not, not_pre_num add 1 and asking the harder question
        not_pre_num = 0
        for question_i in question_list:
            lb = t_key + str(not_pre_num)
            question = list(question_i.values())[0]

            t_key_desc = self.check_about(t_key, curtag)  # 生成当前已知tag下，需要生成tag的描述 似乎只有预测一级和二级标签使用

            if t_key_desc != "":
                qinfo = question["known_infomation"].replace("known_infomation", t_key_desc)
                qinfo += question["question"].replace("to_determin_attribute", t_key)
            else:
                qinfo = question["question"].replace("to_determin_attribute", t_key)
            if curtag != '' and curtag != 'nan':
                qinfo = qinfo.replace("merchandise", curtag.lower())

            qinfo = qinfo.replace("options", f"Options: {str(options).lower()}")
            qinfo = qinfo + question["constrains"]

            if t_key in self.if_multi:  # single choose or multi choose Fixme

                qinfo = qinfo.replace("if_multi", "appropriate options")
                qinfo = qinfo.replace("an answer", "one or more answer you think is correct")
            else:
                qinfo = qinfo.replace("if_multi", "one option")

            if t_key in revised_info:
                qinfo = revised_info[t_key]
            if curtag in revised_info:
                qinfo = revised_info[curtag]

            # predict
            tmpres = self.initqw.tag_main(lb, qinfo)
            tmpres = res_post_process(tmpres)

            # find the suitable label from options
            if t_key in self.if_multi:
                label_res = find_eles_in_list(tmpres, options)
            else:
                label_res = find_element_in_list(tmpres, options)
            predict_logger = f'tag: {t_key}  predict result: {label_res}'
            predict_logger = predict_logger + f'  gt result: {item_gt[t_key]}' if item_gt else predict_logger
            logger.info(predict_logger)

            # logger.info(f'all available tag: {label_res}\n\n')
            if label_res:
                break
            else:  # predict fail and then predict one more time in quick qa way
                qa = copy.deepcopy(self.utilquestion).replace("to_determain_sentence", tmpres)
                qa = qa.replace("to_chose_options", f'options:{str(options).lower()}')
                label_res = self.initqw.quick_qa(qa)  # todo，How it works, improve it
                label_res = res_post_process(label_res)

                if t_key in self.if_multi:
                    label_res2 = find_eles_in_list(label_res, options)
                else:
                    label_res2 = find_element_in_list(label_res, options)

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
                        label_res = 'nan'  # If the tag can not be predicted, return ' '

        predict_result[t_key] = label_res
        return label_res

    def tag_main(self, imagedirs, product_info, version, item_gt=None, pre_common_tag=True, pre_category_tag=True):
        try:
            # load category and tag
            self.load_label(version)
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
                tag = self.single_com(imagedirs, product_info, item_gt=item_gt,
                                      pre_common_tag=pre_common_tag, pre_category_tag=pre_category_tag)

            return tag
        except Exception as e:
            # print('error',e)
            logger.info(f'error:{e}')
            logger.info(f'{e.__traceback__.tb_frame.f_globals["__file__"]}')
            logger.info(f'{e.__traceback__.tb_lineno}')
            return []
