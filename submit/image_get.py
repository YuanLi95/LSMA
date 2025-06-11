from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import base64
import time
import os
import re
from utils import *
import replicate
import random
import time
import requests
def decode_img(encoded_imgs):
    decoded_imgs = []
    for img in encoded_imgs:
        try:
            re_str = re.search('data.+?;base64,',img)
            re_str = re_str.group() if re_str else ''
            img = img.replace(re_str,'')
            missing_padding = 4-len(img)%4
            if missing_padding < 4:
                img += '=' * missing_padding
            decoded_img = base64.b64decode(img)
            decoded_imgs.append(decoded_img)
            return decoded_imgs
        except Exception as e:
            #print('decoded get a wrong:',e)
            continue
        #return decoded_imgs
    return decoded_imgs

def get_rephrase_images(input_path,image_input_dir,image_output_dir,output_path):
    data=getDictFromJsonl(input_path)
    for item in data:
        if item['type']!='rephrase':
            continue

        image_origin=image_input_dir+item['image_id']
        image_output=image_output_dir+item['image_id']
        if os.path.exists(image_output):
            append_to_jsonl(output_path,[item])
            continue
        if os.path.exists(image_origin):
            try:
                image = Image.open(image_origin).convert('RGB')
                image.save(image_output)
                append_to_jsonl(output_path,[item])
                print('rephrase image saved')
            except Exception as e:
                print('rephrase image save error:',e)
                continue


def getTempImgBySelenium(content,image_dir,driver):
    

    global need_quit
    # for filename in os.listdir('./temp_images/'):
    #     file_path = os.path.join('./temp_images/', filename)
    #     os.remove(file_path)
    # if not os.path.exists('./temp_images'):
    #     os.mkdir('./temp_images')
        
    if os.path.exists(image_dir)==False:
        os.mkdir(image_dir)

    # driver = webdriver.Chrome(ChromeDriverManager().install())
    # driver.maximize_window()
    url = "https://www.google.com/search?q="+content+"&source=lnms&tbm=isch"
    driver.get(url)
    time.sleep(0.5)
    count = 3
    try:
        # res = try_click(driver)
        # if res == False:
            # need_quit = True
        driver.switch_to.frame(driver.find_element('xpath','//iframe[@title="reCAPTCHA"]'))
        driver.find_element('xpath','//span[@id="recaptcha-anchor"]')
        need_quit = True
    except:
        pass
    imges = driver.find_elements('xpath','//g-img/img')
    #imges = driver.find_elements(By.TAG_NAME, 'img')
    result=[]
    # for img in imges[:1]:
    #     result.append(img.get_attribute('src'))
    for img in imges[:10]:
        result.append(img.get_attribute('src'))

    image_id='error' 
    image_path='error'
    result = decode_img(result)
    for i,img in enumerate(result):
        id=random.randint(1,99999999)
        image_id = str(id) + '.jpg'
        image_path= image_dir+image_id
        with open(image_dir+image_id,'wb') as f:
            f.write(img)
            f.close()

    return image_id, image_path
    
def getTempImgBySelenium2(content, image_dir, driver):
    global need_quit

    # # 清理旧的临时图片
    # temp_images_dir = './temp_images/'
    # if os.path.exists(temp_images_dir):
    #     for filename in os.listdir(temp_images_dir):
    #         file_path = os.path.join(temp_images_dir, filename)
    #         os.remove(file_path)
    # else:
    #     os.mkdir(temp_images_dir)

    # 创建目标目录
    if not os.path.exists(image_dir):
        os.mkdir(image_dir)

    # 打开 Google 图片搜索页面
    url = f"https://www.google.com/search?q={content}&source=lnms&tbm=isch"
    driver.get(url)

    try:
        # 等待缩略图加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//img[contains(@class, "rg_i") and @src]'))
        )
    except Exception as e:
        print(f"Error loading images: {e}")
        return 'error', 'error'

    # 获取所有缩略图元素
    thumbnails = driver.find_elements(By.XPATH, '//img[contains(@class, "rg_i") and @src]')
    if not thumbnails:
        print("No thumbnails found.")
        return 'error', 'error'

    # 点击第一个缩略图
    thumbnails[0].click()

    try:
        # 等待高分辨率图片加载完成
        full_image = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//img[@class="n3VNCb" and contains(@src, "http")]'))
        )
    except Exception as e:
        print(f"Error loading full image: {e}")
        return 'error', 'error'

    # 获取高分辨率图片的 src 属性
    image_url = full_image.get_attribute('src')
    if not image_url:
        print("High-resolution image URL not found.")
        return 'error', 'error'

    # 下载图片
    result = [image_url]
    decoded_images = decode_img(result)
    if not decoded_images:
        print("Failed to decode images.")
        return 'error', 'error'

    for i, img in enumerate(decoded_images):
        unique_id = random.randint(1, 99999999)
        image_id = f"{unique_id}.jpg"
        image_path = os.path.join(image_dir, image_id)
        with open(image_path, 'wb') as f:
            f.write(img)

    return image_id, image_path

def getImage(text,image_dir,driver):
    getTempImgBySelenium(text.replace('#',''),image_dir,driver)
    

def getAllImage(input_path,output_path,image_dir,driver):
    data=getDictFromJsonl(input_path)
    dataed=getDictFromJsonl(output_path)
    image_final=None
    if dataed!=[]:
        image_final=dataed[-1]['sentence']

    begin=0
    if image_final!=None:
        for idx,item in enumerate(data):
            if item['sentence']==image_final:
                begin=idx
                break

    for idx, item in enumerate(data):
        if idx<=begin or item['type']=='rephrase':
            continue
        print(idx)
        if (idx+1)%10==0:
            time.sleep(random.uniform(5, 6))
        
        item['sentence'].replace('#','')
        id,path=getTempImgBySelenium(item['sentence'],image_dir,driver)
        if id!='error' and path!='error':
            data[idx]['image_id']=id
            data[idx]['image_path']='/images/train/'+id
            #这一步防止图片爬到一半前工尽弃
            append_to_jsonl(output_path,[data[idx]])
        else :
            #爬不到图片的甚至不用保留
            print('未爬取')
            data[idx]['retain']=0

        wait_time = random.uniform(0.5, 1.0)
        time.sleep(wait_time)
        

    # data=delete_unretain(data)
    # #增加了image_id和image_path
    # with open(output_path,'w',encoding='utf-8') as f:
    #     for item in data:
    #         f.write(json.dumps(item,ensure_ascii=False)+'\n')


def main(input_path,image_origin_dir,output_dir):


    output_path=output_dir+'add_image.jsonl'
    image_dir = output_dir+'image/'
    if os.path.exists(image_dir)==False:
        os.mkdir(image_dir)        
    #get_rephrase_images(input_path,image_origin_dir,image_dir,output_path)
    driver = webdriver.Chrome()
    getAllImage(input_path,output_path,image_dir,driver)
    

if __name__ == '__main__':
    input_path = 'output/twitter_2015/13/after_filter.jsonl'
    image_origin_dir = 'data/twitter_2015/twitter2015_images/'
    output_dir = 'output/twitter_2015/13/'
    main(input_path,image_origin_dir,output_dir)
    # input_path='output/twitter_2015/13/muti_level/add_image.jsonl'
    # data=getDictFromJsonl(input_path)
    # for idx,item in enumerate(data):
    #     data[idx]['image_path']='/images/train/'+item['image_id']
    # os.remove(input_path)
    # append_to_jsonl(input_path,data)
    

