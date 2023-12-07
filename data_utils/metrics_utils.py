import os


def get_skc2img(skc2img_root, repeat_skc, img_root='/root/autodl-tmp/datas'):
    # img_root = '/root/autodl-tmp/tmp_res/tag_res/output'

    dir_names = os.listdir(img_root)
    for dir_name in dir_names:
        if os.path.isfile(os.path.join(img_root, dir_name)):
            continue
        img_path = os.path.join(img_root, dir_name, 'imgs') if dir_name != 'imgs' else os.path.join(img_root, dir_name)
        if not os.path.exists(img_path):
            os.removedirs(os.path.dirname(img_path))
            continue
        for skc_id in os.listdir(img_path):
            if skc_id in skc2img_root:
                if skc_id not in repeat_skc:
                    repeat_skc[skc_id] = [skc2img_root[skc_id]]
                repeat_skc[skc_id].append(img_path)
            skc2img_root[skc_id] = img_path


def get_multi_path_skc2img(paths=['/root/autodl-tmp/tmp_res/tag_res/output',
                                  '/root/autodl-tmp/tmp_res_zr/tag_res/output',
                                  '/root/autodl-tmp/datas']):
    """
    get the corresponding relationship of skc_id and img path, from multi paths
    """
    # paths = ['/root/autodl-tmp/tmp_res/tag_res/output', '/root/autodl-tmp/datas']
    skc2img_root, repeat_skc = {}, {}
    for path in paths:
        get_skc2img(skc2img_root, repeat_skc, path)
    return skc2img_root, repeat_skc


if __name__ == '__main__':
    skc2img_root, repeat_skc = {}, {}
    get_skc2img(skc2img_root, repeat_skc)
