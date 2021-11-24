# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 01:41:06 2020

@author: vinic
"""
#%%IMPORTAÇÃO DE PACOTES

from userinfo.Credentials import u_login, u_password
from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
from time import sleep, strftime
from random import randint
import pandas as pd
from matplotlib import pyplot as plt
from mtcnn.mtcnn import MTCNN
from urllib.request import urlretrieve
import os
from plotly.offline import init_notebook_mode, iplot, plot
from plotly import graph_objs as go
init_notebook_mode(connected = True)

#%% DEFINIR LOCAL DO CHROME WEBDRIVER E VARIÁVEIS PARA AS FUNÇÕES DO ROBÔ

chromedriver_path = 'C:/Users/vinic/dev/Instabot/chromedriver.exe'
hashtags = ['finance', 'math', 'trading']
targets = ['profilex','profiley']
our_profilename = 'myprofile'

#OPÇÕES DE VISUALIZAÇÃO DO PANDAS
pd.set_option('display.max_columns', None)


#%% CLASSE INSTABOT

class Instabot():
    
    detector = MTCNN()
        
    def __init__(self, driver_path = chromedriver_path):
        self.driver_path = driver_path
    
    def start (self):
        self.driver = webdriver.Chrome(executable_path=self.driver_path)
        
    def login (self, user_login = u_login, user_password = u_password, login_url = 'https://www.instagram.com/accounts/login/?source=auth_switcher'):
        self.user_login = user_login
        self.user_password = user_password
        self.login_url = login_url
        self.driver.get(self.login_url)
        sleep(4)
        username = self.driver.find_element_by_name('username')
        username.send_keys(self.user_login)
        password = self.driver.find_element_by_name('password')
        password.send_keys(self.user_password)

        button_login = self.driver.find_element_by_css_selector('#loginForm > div > div:nth-child(3) > button')
        button_login.click()
        sleep(4)

        button_nao_salvar = self.driver.find_element_by_css_selector('#react-root > section > main > div > div > div > div > button')
        button_nao_salvar.click()
        sleep(4)

        button_nao_notif = self.driver.find_element_by_css_selector('body > div.RnEpo.Yx5HN > div > div > div > div.mt3GC > button.aOOlW.HoLwm')                                                           
        button_nao_notif.click()
        sleep(4)
        
    def get_likers(self, own_username = our_profilename, qtde_posts = 15):
        self.own_username = own_username
        self.qtde_posts = qtde_posts
        self.driver.get('https://www.instagram.com/' + self.own_username)
        sleep(2)
        recent_post = self.driver.find_element_by_xpath('/html/body/div[1]/section/main/div/div[3]/article/div/div/div/div[1]/a/div[1]/div[2]')
        recent_post.click()
        sleep(2)
        js_element_to_scroll = 'document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.Igw0E.Xy04 > div")'
        likers = pd.DataFrame()
        for i in range(self.qtde_posts):
            likers_list = self.driver.find_element_by_xpath('//button[@class="sqdOP_8A6y5"]')
            likers_list.click()
            sleep(2)
            #Pegar scroll top
            last_top = self.driver.execute_script('return {}.scrollTop'.format(js_element_to_scroll))
            while True:
                for j in range (1,20):
                    try:
                        nome_curtidor = self.driver.find_element_by_xpath('//div[@role="dialog"]/div[1]/div[2]/div[1]/div[1]/div['+ str(j) +']/div[2]/div[1]/div[1]').text
                        print(nome_curtidor)
                        status_botao = self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[2]/div/div/div['+ str(j) +']/div[3]/button').text
                        print(status_botao)
                        imagem_perfil = self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[2]/div/div/div['+ str(j) +']/div[1]/div/div/a/img').get_attribute('src')
                        print(imagem_perfil)
                        likers = likers.append({'curtidor': nome_curtidor, 'status_botao': status_botao, 'postagem': self.driver.current_url, 'imagem_perfil': imagem_perfil, 'date': strftime('%Y-%m-%d')}, ignore_index=True) 
                        print(likers)
                    except Exception as e:
                        print(e)
                        continue
                # Scroll incremental
                self.driver.execute_script('{}.scrollTo(0, {});'.format(js_element_to_scroll, str(int(last_top) + 100)))
                sleep(2)
                # Calcular novo scroll top e comparar com o último scroll top
                new_top = self.driver.execute_script('return {}.scrollTop'.format(js_element_to_scroll))
                if new_top == last_top:
                    # Se os scroll tops forem os mesmos, sai do while, pois já chegou ao final da rolagem
                    break
                last_top = new_top
            print('Quantidade de curtidas distintas recuperadas: ' + str(len(likers.drop_duplicates())))
            # Botão de Fechar a caixa de diálogo das curtidas
            self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[1]/div/div[2]/button').click()
            # Passar para a próxima postagem
            try:
                self.driver.find_element_by_link_text('Próximo').click()
            except:
                print('Não há mais publicações disponíveis')
                likers = likers.drop_duplicates().reset_index(drop=True)
            sleep(randint(2,6))
        self.all_likers = likers.drop_duplicates().reset_index(drop=True)
        return self.all_likers
        
    def hashtags(self, htaglist = hashtags, num_iteracoes = 20, htaglogpath = './logs/hashtags/last_log.txt'):
        self.htaglist = htaglist
        self.num_iteracoes = num_iteracoes
        self.htaglogpath = htaglogpath
        if isinstance(self.htaglist, list):
            print('Recuperando último log de hashtags...')
            with open(self.htaglogpath, 'r') as l:
                htaglast_log = l.read()
            htaglog_anterior = pd.DataFrame() if htaglast_log == '' else pd.read_csv(htaglast_log, delimiter = ',', index_col=0, parse_dates=['date'])
            htaglog_atual = pd.DataFrame()
            print('Log recuperado!')
            new_followed = []
            tag = -1
            followed = 0
            likes = 0
            comments = 0
            qt_iteracoes = self.num_iteracoes

            for hashtag in self.htaglist:
                tag += 1
                self.driver.get('https://www.instagram.com/explore/tags/'+ self.htaglist[tag] + '/')
                sleep(5)
                first_thumbnail = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[1]/div/div/div[1]/div[1]/a/div')
                first_thumbnail.click()
                sleep(randint(1,2))    
                try:        
                    for x in range(1, qt_iteracoes + 1):
                        print('Iteração de número {} da hashtag {}'.format(x, hashtag))
                        username = self.driver.find_element_by_xpath('/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[1]/span/a').text
                        print(username + ' encontrado')
                        
                        if username not in list(htaglog_anterior['user']) and username != our_profilename:
                            # Se já seguimos, não deixamos de seguir
                            if self.driver.find_element_by_xpath('/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[2]/button').text == 'Seguir':
                                print('Passaremos a seguir ' + username)
                                self.driver.find_element_by_xpath('/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[2]/button').click()
                                new_followed.append(username)
                                followed += 1
                                # Gravando no log
                                htaglog_atual = htaglog_atual.append({'user': username, 'hashtag': hashtag, 'postagem': self.driver.current_url , 'date':strftime('%Y-%m-%d %H:%M:%S')}, ignore_index=True)            
                                # Curtindo a foto
                                button_like = self.driver.find_element_by_xpath('/html/body/div[4]/div[2]/div/article/div[3]/section[1]/span[1]/button')                       
                                button_like.click()
                                likes += 1
                                sleep(randint(18,25))            
                            # Próxima foto
                            self.driver.find_element_by_link_text('Próximo').click()
                            sleep(randint(17,29))
                        else:
                            print('Já seguimos ' + username)
                            self.driver.find_element_by_link_text('Próximo').click()
                            sleep(randint(10,25))
                # Algumas hashtags não atualizam a foto. Seguir em diante...
                except:
                    continue
            print('Gravando log atualizado...')
            htagupdated_log = htaglog_anterior.append((htaglog_atual), ignore_index=True, sort=True)
            htagupdated_file_path = './logs/hashtags/{}_hashtags.csv'.format(strftime("%Y%m%d-%H%M%S"))
            htagupdated_log.to_csv(htagupdated_file_path)
            with open(self.htaglogpath, 'w') as f:
                f.write(htagupdated_file_path)
            print('Log gravado com sucesso!')
            print('Curtimos {} fotos.'.format(likes))
            print('Comentamos {} fotos.'.format(comments))
            print('Seguimos {} novos usuários.'.format(followed))
            print('Passamos a seguir:')
            print(new_followed)
        else:
            raise TypeError('htaglist must be a list')
        
    def targets(self, user_targets = targets, qt_seguidas = 40, targetlogpath = './logs/user_targets/last_log.txt'):
        self.user_targets = user_targets
        self.qt_seguidas = qt_seguidas
        self.targetlogpath = targetlogpath
        if isinstance (self.user_targets, list):
            print('Recuperando último log de targets...')
            with open(self.targetlogpath, 'r') as l:
                targetlast_log = l.read()
            targetlog_anterior = pd.DataFrame() if targetlast_log == '' else pd.read_csv(targetlast_log, delimiter = ',', index_col=0, parse_dates=['date'])
            targetlog_atual = pd.DataFrame()
            print('Log recuperado!')
            user_t = -1
            for target in self.user_targets:
                user_t += 1
                self.driver.get('https://www.instagram.com/'+ self.user_targets[user_t] + '/')
                sleep(5)
                followers = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a')
                followers.click()
                sleep(randint(1,2))
                ## SCROLL ##
                scroll_pause_time = 2
                # Get scroll height
                last_height = self.driver.execute_script('return document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.isgrP").scrollHeight')
                while True:
                    # Scroll down to bottom
                    self.driver.execute_script('document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.isgrP").scrollTo(0, document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.isgrP").scrollHeight);')
                    # Wait to load page
                    sleep(scroll_pause_time)
                    # Calculate new scroll height and compare with last scroll height
                    new_height = self.driver.execute_script('return document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.isgrP").scrollHeight')
                    if new_height == last_height:
                        # If heights are the same it will exit the function
                        break
                    last_height = new_height
                ## END SCROLL ##
                qt_seguidores = len(self.driver.find_elements_by_xpath('/html/body/div[4]/div/div/div[2]/ul/div/li'))
                print(target + ' tem ' + str(qt_seguidores) + ' seguidores.')
                count = 0
                for i in range(1, qt_seguidores+1):
                    if count < self.qt_seguidas:
                        try:
                            print('Iteração de número {} do alvo {}.'.format(count+1, target))
                            nome_seguidor = self.driver.find_element_by_xpath('/html/body/div[4]/div/div/div[2]/ul/div/li[{}]/div/div[1]/div[2]/div[1]/span/a'.format(i)).text
                            print(nome_seguidor)
                            botao_seguir = self.driver.find_element_by_xpath('/html/body/div[4]/div/div/div[2]/ul/div/li[{}]/div/div[2]/button'.format(i))
                            status_botao = botao_seguir.text
                            print(status_botao)
                            if status_botao == "Seguir":
                                botao_seguir.click()
                                targetlog_atual = targetlog_atual.append({'target': target, 'seguidor': nome_seguidor, 'date':strftime('%Y-%m-%d %H:%M:%S')}, ignore_index=True)
                                count += 1
                                sleep(randint(18,25))
                            else:
                                print('Já seguimos {}'.format(nome_seguidor))
                                continue
                        except Exception as e:
                            print('Erro encontrado!')
                            print(e)
                            count += 1
                            continue
                    else:
                        continue
            print('Gravando log atualizado...')
            targetupdated_log = targetlog_anterior.append((targetlog_atual), ignore_index=True, sort=True)
            targetupdated_file_path = './logs/user_targets/{}_user_targets.csv'.format(strftime("%Y%m%d-%H%M%S"))
            targetupdated_log.to_csv(targetupdated_file_path)
            with open(self.targetlogpath, 'w') as f:
                f.write(targetupdated_file_path)
            print('Log gravado com sucesso!')
        else:
            raise TypeError('user_targets must be a list')
    
    def likes (self, own_username = our_profilename, qtde_posts = 3, likeslogpath = './logs/likes/last_log.txt'):
        self.own_username = own_username
        self.qtde_posts = qtde_posts
        self.likeslogpath = likeslogpath
        print('Recuperando último log de likes...')
        with open(self.likeslogpath, 'r') as l:
            likeslast_log = l.read()
        likeslog_anterior = pd.DataFrame() if likeslast_log == '' else pd.read_csv(likeslast_log, delimiter = ',', index_col=0, parse_dates=['date'])
        likeslog_atual = pd.DataFrame()
        print('Log recuperado!')
        ### GET LIKERS ###
        likers = self.get_likers(own_username = self.own_username, qtde_posts = self.qtde_posts)
        likers = likers.drop_duplicates(subset='curtidor').reset_index(drop=True)
        to_follow = likers[likers['status_botao'] == 'Seguir'].reset_index(drop=True)
        for curtidor in list(to_follow['curtidor']):
            self.driver.get('https://www.instagram.com/' + curtidor)
            sleep(2)
            try:
                botao_seguir = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/div[1]/div[1]//button')
                print(curtidor)
                print(botao_seguir.text)
                if botao_seguir.text == 'Seguir':
                    botao_seguir.click()
                    likeslog_atual = likeslog_atual.append({'nosso_curtidor': curtidor, 'postagem': to_follow['postagem'][to_follow['curtidor'] == curtidor].iloc[0], 'date': strftime('%Y-%m-%d %H:%M:%S')}, ignore_index=True)
                    print(likeslog_atual)
                    sleep(randint(2,4))
                else:
                    print('Não interessa seguir ' + curtidor)
                    sleep(randint(3,5))
            except:
                print('Erro ao localizar botão')
                sleep(2)
                continue
        print('O resultado final de likeslog_atual é:')
        print(likeslog_atual)
        print('Gravando log atualizado...')
        likesupdated_log = likeslog_anterior.append((likeslog_atual), ignore_index=True, sort=True)
        likesupdated_file_path = './logs/likes/{}_likes.csv'.format(strftime("%Y%m%d-%H%M%S"))
        likesupdated_log.to_csv(likesupdated_file_path)
        with open(self.likeslogpath, 'w') as f:
            f.write(likesupdated_file_path)
        print('Log gravado com sucesso!')
        
    def our_likers (self, own_username = our_profilename, qtde_posts = 15, likerslogpath = './logs/likers/last_log.txt'):
        self.own_username = own_username
        self.qtde_posts = qtde_posts
        self.likerslogpath = likerslogpath
        print('Recuperando último log de curtidores...')
        with open(self.likerslogpath, 'r') as l:
            likerslast_log = l.read()
        likerslog_anterior = pd.DataFrame() if likerslast_log == '' else pd.read_csv(likerslast_log, delimiter = ',', index_col=0, parse_dates=['date'])
        likerslog_atual = pd.DataFrame()
        print('Log recuperado!')
        ########## GET LIKERS ##############
        likerslog_atual = self.get_likers(own_username = self.own_username, qtde_posts = self.qtde_posts)
        ########## DETECT ACCOUNT TYPE ####
        self.detect_account_type(df=likerslog_atual, col_target_username = 'curtidor',  col_target_profile_image = 'imagem_perfil')
        ######### UPDATE LOG ###############
        print(likerslog_atual)
        print('Gravando log atualizado...')
        likersupdated_log = likerslog_anterior.append((likerslog_atual), ignore_index=True, sort=True)
        likersupdated_file_path = './logs/likers/{}_likers.csv'.format(strftime("%Y%m%d-%H%M%S"))
        likersupdated_log.to_csv(likersupdated_file_path)
        with open(self.likerslogpath, 'w') as f:
            f.write(likersupdated_file_path)
        print('Log gravado com sucesso!')
    
    def our_followers (self, followerslogpath = './logs/nossos_seguidores/last_log.txt'):
        self.followerslogpath = followerslogpath
        print('Recuperando último log de seguidores...')
        with open(self.followerslogpath, 'r') as l:
            followerslast_log = l.read()
        followerslog_anterior = pd.DataFrame() if followerslast_log == '' else pd.read_csv(followerslast_log, delimiter = ',', index_col=0, parse_dates=['date'])
        followerslog_atual = pd.DataFrame()
        print('Log recuperado!')
        self.driver.get('https://www.instagram.com/myprofile/')
        sleep(5)
        followers = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a')
        followers.click()
        sleep(randint(1,2))
        ## START SCROLL
        scroll_pause_time = 2
        # Get scroll height
        last_height = self.driver.execute_script('return document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.isgrP").scrollHeight')
        while True:
            # Scroll down to bottom
            self.driver.execute_script('document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.isgrP").scrollTo(0, document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.isgrP").scrollHeight);')
            # Wait to load page
            sleep(scroll_pause_time)    
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script('return document.querySelector("body > div.RnEpo.Yx5HN > div > div > div.isgrP").scrollHeight')
            if new_height == last_height:
                # If heights are the same it will exit the function
                break
            last_height = new_height
        ## END SCROLL
        qt_seguidores = len(self.driver.find_elements_by_xpath('/html/body/div[4]/div/div/div[2]/ul/div/li'))
        print('Hoje, temos ' + str(qt_seguidores) + ' seguidores.')
        for i in range(1, qt_seguidores+1):
            nome_seguidor = self.driver.find_element_by_xpath('/html/body/div[4]/div/div/div[2]/ul/div/li[{}]/div/div[1]/div[2]/div[1]/span/a'.format(i)).text
            print(nome_seguidor)
            botao_seguir = self.driver.find_element_by_xpath('/html/body/div[4]/div/div/div[2]/ul/div/li[{}]/div/div[2]/button'.format(i))
            status_botao = botao_seguir.text
            print(status_botao)
            imagem = self.driver.find_element_by_xpath('/html/body/div[4]/div/div/div[2]/ul/div/li[{}]/div/div[1]//img'.format(i)).get_attribute('src')
            followerslog_atual = followerslog_atual.append({'nosso_seguidor': nome_seguidor, 'status': status_botao, 'date':strftime('%Y-%m-%d'), 'imagem_perfil': imagem, 'tipo_conta': 'N/A'}, ignore_index=True)
        #### DETECT ACCOUNT TYPE ####
        self.detect_account_type(df = followerslog_atual, col_target_username = 'nosso_seguidor', col_target_profile_image = 'imagem_perfil')
        ### END DETECT ACCOUNT TYPE ###
        print(followerslog_atual)
        print('Gravando log atualizado...')
        followersupdated_log = followerslog_anterior.append((followerslog_atual), ignore_index=True, sort=True)
        followersupdated_file_path = './logs/nossos_seguidores/{}_nossos_seguidores.csv'.format(strftime("%Y%m%d-%H%M%S"))
        followersupdated_log.to_csv(followersupdated_file_path)
        with open(self.followerslogpath, 'w') as f:
            f.write(followersupdated_file_path)
        print('Log gravado com sucesso!')
    
    def has_face(self, image_url):
        #self.detector = MTCNN()
        self.image_url = image_url
        image_file = "temp_profile_pic.jpg"
        urlretrieve(self.image_url, image_file)
        pixels = plt.imread(image_file, format='jpg')
        # detect faces
        faces = Instabot.detector.detect_faces(pixels)
        if len(faces) == 0:
            os.remove(image_file)
            return False
        else:
            os.remove(image_file)
            return True
    
    def detect_account_type(self, df, col_target_username: str, col_target_profile_image: str):
        self.df = df
        self.col_target_username = col_target_username
        self.col_target_profile_image = col_target_profile_image
        self.df['tipo_conta'] = 'N/A'
        for i in range(0, len(self.df)):
            try:                
                user = self.df[self.col_target_username].iat[i]
                imagem = self.df[self.col_target_profile_image].iat[i]
                test = self.has_face(imagem)
                if not test:
                    self.df['tipo_conta'].iat[i] = 'Comercial'
                    print("{} does not have a face".format(user))
                else:
                    self.df['tipo_conta'].iat[i] = 'Pessoal'
                    print("{} has a face".format(user))
            except:
                print('Não foi possível fazer o reconhecimento de imagem.')
                continue
        
    
    def shutdown (self):
        self.driver.quit()
        
#%% GERENCIAL

class Reports():
    
    colorway = ['#ED7600', '#353745', '#DDBB4D', '#987239']
    
    def __init__(self, our_followers_last_log = './logs/nossos_seguidores/last_log.txt',
                 hashtag_last_log = './logs/hashtags/last_log.txt',
                 target_last_log = './logs/user_targets/last_log.txt',
                 likes_last_log = './logs/likes/last_log.txt',
                 likers_last_log = './logs/likers/last_log.txt'):
        self.our_followers_last_log = our_followers_last_log
        self.hashtag_last_log = hashtag_last_log
        self.target_last_log = target_last_log
        self.likes_last_log = likes_last_log
        self.likers_last_log = likers_last_log
        
        # GET OUR CURRENT FOLLOWERS LOG
        with open(self.our_followers_last_log, 'r') as f:
            f_log_path = f.read()
        followers_log = pd.read_csv(f_log_path, delimiter = ',', index_col=0, parse_dates=['date'])        
        self.current_followers = followers_log[followers_log['date'] == followers_log['date'].unique()[-1]]
        
        # GET HASHTAG LOG
        with open(self.hashtag_last_log, 'r') as h:
            h_log_path = h.read()
        hashtag_log = pd.read_csv(h_log_path, delimiter = ',', index_col=0, parse_dates=['date'])
        self.hashtag_log = hashtag_log.rename(columns={'postagem':'postagem_hashtag'})
        
        # GET TARGETS LOG
        with open(self.target_last_log, 'r') as t:
            t_log_path = t.read()
        target_log = pd.read_csv(t_log_path, delimiter = ',', index_col=0, parse_dates=['date'])
        target_log.rename(columns={'date':'date_target'}, inplace=True)
        self.target_log = target_log.drop_duplicates('seguidor')
        
        # GET LIKES LOG
        with open(self.likes_last_log, 'r') as lk:
            l_log_path = lk.read()    
        likes_log = pd.read_csv(l_log_path, delimiter = ',', index_col=0, parse_dates=['date'])
        self.likes_log = likes_log.rename(columns={'postagem':'postagem_like', 'date': 'date_like'})
        
        # GET LIKERS LOG
        with open(self.likers_last_log, 'r') as lkrs:
            lkrs_log_path = lkrs.read()
        likers_log = pd.read_csv(lkrs_log_path, delimiter = ',', index_col=0, parse_dates=['date'])        
        self.likers_log = likers_log[likers_log['date'] == likers_log['date'].unique()[-1]]
        
        #CREATE TABELAO
        tabelao = pd.merge(left=self.current_followers, right=self.hashtag_log, how='left', left_on='nosso_seguidor', right_on='user', suffixes=('_recent','_hashtag'))
        tabelao = pd.merge(left=tabelao, right=self.target_log, how='left', left_on='nosso_seguidor', right_on='seguidor')
        tabelao = pd.merge(left=tabelao, right=self.likes_log, how='left', left_on='nosso_seguidor', right_on='nosso_curtidor')        
        tabelao['origem'] = 'outros'
        tabelao.loc[tabelao['nosso_seguidor'] == tabelao['user'], 'origem'] = 'hashtag ' + tabelao['hashtag'].astype(str)
        tabelao.loc[tabelao['nosso_seguidor'] == tabelao['seguidor'], 'origem'] = 'segue ' + tabelao['target'].astype(str)
        tabelao.loc[tabelao['nosso_seguidor'] == tabelao['nosso_curtidor'], 'origem'] = 'curtiu nossa publicacao ' + tabelao['postagem_like'].astype(str)
        self.tabelao = tabelao
        
    def convertido_alcancado(self, df_alvo, coluna_groupby, coluna_seguidor, metodo):
        self.df_alvo = df_alvo
        self.coluna_groupby = coluna_groupby
        self.coluna_seguidor = coluna_seguidor
        self.metodo = metodo
        df1 = self.df_alvo[[self.coluna_groupby,self.coluna_seguidor]].groupby(self.coluna_groupby).count().rename(columns={self.coluna_seguidor:'total_alcancado_{}'.format(self.metodo)})
        df2 = self.df_alvo[[self.coluna_groupby,self.coluna_seguidor]][self.df_alvo[self.coluna_seguidor].isin(list(self.current_followers['nosso_seguidor']))].groupby(self.coluna_groupby).count().rename(columns={self.coluna_seguidor:'total_convertido_{}'.format(self.metodo)})
        df3 = pd.concat([df1,df2], axis=1, sort=True)
        df3['perc_conversao'] = df3['total_convertido_{}'.format(self.metodo)]/df3['total_alcancado_{}'.format(self.metodo)]
        return df3
    
    def report_hashtag(self, col_groupby = 'hashtag', col_seguidor = 'user', metodo = 'hashtag'):
        self.metodo = metodo
        self.df = self.hashtag_log
        self.report = self.convertido_alcancado(self.df, col_groupby, col_seguidor, metodo)
        self.chart_convertido_alcancado(self.report, self.metodo)
        return self.report
        

    def report_targets(self, col_groupby = 'target', col_seguidor = 'seguidor', metodo = 'target'):
        self.metodo = metodo
        self.df = self.target_log
        self.report = self.convertido_alcancado(self.df, col_groupby, col_seguidor, metodo)
        self.chart_convertido_alcancado(self.report, self.metodo)
        return self.report
        
    def report_likes(self, col_groupby = 'postagem_like', col_seguidor = 'nosso_curtidor', metodo = 'likes'):
        self.df = self.likes_log
        self.metodo = metodo
        self.report = self.convertido_alcancado(self.df, col_groupby, col_seguidor, metodo)
        self.chart_convertido_alcancado(self.report, self.metodo)
        return self.report
    
    def report_likers(self, col_groupby = ['curtidor','tipo_conta'], metodo = 'likers', top=20):
        self.df = self.likers_log
        self.col_groupby = col_groupby
        self.metodo = metodo
        self.report = self.df[col_groupby].value_counts().head(top).unstack()
        return self.report
    
    def chart_convertido_alcancado(self, report, metodo):
        self.report = report
        self.metodo = metodo
        fig = go.Figure({'data': [go.Bar(x=self.report.index, y=self.report['total_alcancado_{}'.format(self.metodo)], name='Total Alcancado', text=self.report['total_alcancado_{}'.format(metodo)], opacity = 0.8, textposition='outside'),
go.Bar(x=self.report.index, y=self.report['total_convertido_{}'.format(metodo)], name='Total Convertido', text=self.report['total_convertido_{}'.format(metodo)], opacity = 0.75, textposition='outside')],
'layout': go.Layout(barmode='overlay', title=self.metodo.title(), title_x=0.5, colorway = Reports.colorway)})
        fig.show('svg')
        
    def chart_origens(self, completo: bool = True):
        self.completo = completo
        origens = self.tabelao['origem'].value_counts() if completo == True else self.tabelao['origem'][self.tabelao['origem'] != 'outros'].value_counts()
        fig = go.Figure({'data': [go.Bar(x=origens.index, y=origens, name='Origem de Conversões', text=origens, textposition='outside')],
'layout': go.Layout(barmode='overlay', title='Origem das Conversoes', title_x=0.5, xaxis = dict(tickangle=30), colorway = Reports.colorway)})
        fig.show('png')


#%% FIM
        
print('End')