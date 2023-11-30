import requests


def get_product_infp(tagurl, pageno, pagesize, ):
    prouct_infos = []
    try:
        print('tagurl', tagurl)
        # response = requests.get(tagurl)
        request_data = {
            "pageNo": pageno,
            "pageSize": pagesize
        }

        headers = {
            "accept": "*/*",
            "Content-Type": "application/json"
        }

        response = requests.post(tagurl, json=request_data, headers=headers)

        if response.status_code == 200:
            if response.code == 200:
                datas = response.json()
                print('datas', datas)
                total_skc = datas['total']


    except Exception as e:
        print('get_tags error', e)
    return prouct_infos
