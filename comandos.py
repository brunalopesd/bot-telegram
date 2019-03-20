# This Python file uses the following encoding: utf-8

# Bucket
import os
import cloudstorage as gcs
from google.appengine.api import app_identity

import StringIO
import json
import logging
import random
import urllib
import urllib2
import locale
import sys
import unicodedata
import config

def get_bucket_name():
    bucket_name = os.environ.get('BUCKET_NAME',
                                    app_identity.get_default_gcs_bucket_name())
    return bucket_name

file_path = '/' + get_bucket_name() + '/'
arquivo_chamada = file_path + 'chamada.txt'
chat_id = ''
BASE_URL = ''

#Envia o texto de resposta para o chat
def reply(base_url,chat_id, msg=None, img=None):    
    if msg:
        if msg.startswith('sti'):
            sti = msg.split(':', 1)[1]

            resp = urllib2.urlopen(
                BASE_URL + 'sendSticker', urllib.urlencode({
                            'chat_id': str(chat_id),
                            'sticker': sti.encode('utf-8'),
                            ##'reply_to_message_id': str(message_id),
            })).read()
        else:
            resp = urllib2.urlopen(
                base_url + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                })
            ).read()
    elif img:
        #TODO
        logging.error('img not yet supported')
        resp = None    
    else:
        logging.error('no msg specified')
        resp = None
    
    logging.info('send response:')
    logging.info(resp)

def reply_forced(base_url,chat_id, msg=None):
    if msg:
        resp = urllib2.urlopen(
            base_url + 'sendMessage', urllib.urlencode({
                'chat_id': str(chat_id),
                'text': msg.encode('utf-8'),
                'reply_markup': json.dumps({'force_reply': True, 'selective': True}),
            })
        ).read()
    else:
        logging.error('no msg specified')
        resp = None
    
    logging.info('send response:')
    logging.info(resp)

def inicializa(baseurl, chatid):
    set_chat_id(chatid)
    set_base_url(baseurl)

def set_base_url(baseurl):
    global BASE_URL
    BASE_URL = baseurl

def set_chat_id(chatid):
    global chat_id
    chat_id = str(chatid)
    set_arquivo_chamada()

def set_arquivo_chamada():
    global arquivo_chamada
    global chat_id
    arquivo_chamada = file_path + chat_id + '/chamada.txt'

def get_datafilename(pessoa):
            
    if pessoa == 'chamada':
        return arquivo_chamada
    else:
        return file_path + chat_id + '/data_' + pessoa + '.txt'

def file_exists(gcs_file):
    try:
        gcs.stat(gcs_file)
        logging.info('arquivo existe')
        return True
    except Exception as e:
        logging.info('arquivo nao existe')
        return False

def cria_arquivo(filepath, content=None):
    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    with gcs.open(filepath, 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
        if content == None:
            content = ''
        write_to_file.write(content)

def cria_chamada(chat_id=None):
    
    filepath = arquivo_chamada
    chamada = []
    try:
        if not file_exists(filepath):
            write_retry_params = gcs.RetryParams(backoff_factor=1.1)
            with gcs.open(filepath, 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
                write_to_file.write('')
            
            logging.info('Chamada criada')
            reply(BASE_URL, chat_id,'Chamada criada')
            return True
        else:
            logging.info('Chamada ja existe')
            with gcs.open(filepath) as opened_file:
                for line in opened_file:
                    line = line.decode('utf-8')
                    chamada.append(line.rstrip())
            return True         
    except Exception as e:
        logging.exception(e)
        return False

def verifica_pessoa(pessoa):
    chamada = abre_data('chamada')
    if pessoa in chamada:
        return True
    elif pessoa == 'chamada':
        return True
    else:
        return False

def add_pessoa(text):
    pessoa = text.split(' ', 1)[1]

    chamada = abre_data('chamada')
    logging.info('Adicionando nova pessoa: ' + pessoa)
    if len(pessoa) >= 1 and not verifica_pessoa(pessoa):
        #adiciona
        chamada.append(pessoa)
        try:
            write_retry_params = gcs.RetryParams(backoff_factor=1.1)
            with gcs.open(arquivo_chamada, 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
                for line in chamada:
                    write_to_file.write("%s\n" % (line.encode('utf-8')))

            with gcs.open(get_datafilename(pessoa), 'w', content_type='text/plain', retry_params=write_retry_params) as novo:
                novo.write('')
            
            return pessoa + ' adicionadx com sucesso!'

        except Exception as e:
            logging.exception(e)
            return 'Deu um pau no seu programinha, bro'
    else:
        return 'Pessoa ja existe ou nome invalido'

def abre_data(pessoa):
    retorno = []
    with gcs.open(get_datafilename(pessoa)) as open_file:
        for line in open_file:
            line = line.decode('utf-8')
            retorno.append(line.rstrip())
    return retorno

def add_frase(text):
    pessoa = text.split('_', 1)[0]
    if not verifica_pessoa(pessoa):
        return 'Pessoa nao existe'
    data = abre_data(pessoa)

    if not ' ' in text:
        return 'Escreva uma frase poxa'
    texto = text.split(' ', 1)[1]

    if texto == 'sticker':
        add_sticker_reply(text)
    else:    
        data.append(texto)
        try:
            write_retry_params = gcs.RetryParams(backoff_factor=1.1)
            with gcs.open(get_datafilename(pessoa), 'w', content_type='text/plain', retry_params=write_retry_params) as write_to_file:
                for line in data:
                    write_to_file.write("%s\n" % (line.encode('utf-8')))
            #reply('Agora eu sei falar isso seu otario')
            return 'Agora eu sei falar isso seu otario'
        except Exception as e:
            logging.exception(e)
            #reply('\n\nDeu um pau no seu programinha, bro')
            return '\n\nDeu um pau no seu programinha, bro'

def add_sticker_reply(text):
    txt = '' + text + ' = ' + 'Responda essa msg com o sticker'
    reply_forced(BASE_URL,chat_id,txt)

def add_sticker(sticker,text):
    sticker_id = sticker
    if '_' in text:
        pessoa = text.split('_', 1)[0]
    else:
        pessoa = 'erro'
    txt = pessoa + '_add sti:' + sticker_id
    return add_frase(txt)

def get_frase_numero(text):
    pessoa, numero = text.split(' ', 1)
    if not verifica_pessoa(pessoa):
        return 'Pessoa nao existe'

    data = abre_data(pessoa)                
    tam = len(data)
    i = int(numero) - 1
    if 0 <= i < tam:
        return data[i]
    else:
        return 'Tente outro numero amg'

def get_frase_random(text):
    pessoa = text.lower().split("@")[0]
    if not verifica_pessoa(pessoa):
        return 'Pessoa nao existe'

    data = abre_data(pessoa)            
    tam = len(data)
    base = random.randint(0, tam - 1)
    return data[base]

def get_vomit(text):
    if '_' in text:
        pessoa = text.split('_', 1)[0]
    else:
        pessoa = text

    if not verifica_pessoa(pessoa):
        return 'Pessoa nao existe'

    data = abre_data(pessoa)
    r = map(unicode, data)
    en_r = [unicode(r.index(x) + 1) + ': ' + x for x in r]
    vomit = '\n'.join(en_r)
    return vomit

def get_hype(text):
    chamada = abre_data('chamada')

    if ' ' in text:
        pessoa = text.split(' ', 1)[1]
    else:
        pessoa = 'random'

    if pessoa == 'random':       
        tam_chamada = len(chamada)
        rand_chamada = random.randint(0, tam_chamada)
        pessoa = chamada[rand_chamada]
    elif not verifica_pessoa(pessoa):
        return 'Pessoa nao existe'

    data = abre_data(pessoa)
    tam_frases = len(data)
    rand_frase = random.randint(0, tam_frases)
    frase = data[rand_frase]

    frase_hype = ' '.join(list(frase))
    return frase_hype

def get_comando(texto):
    comando = ''

    if texto == 'start':
        comando = 'start'
    elif texto == 'stop':
        comando = 'stop'
    elif texto.startswith('add_pessoa '):
        comando = 'add_pessoa'
    elif texto == 'add_sticker':
        comando = 'add_sticker'
    elif '_' in texto:
        subcomando = texto.split('_', 1)[1]
        if subcomando.startswith('add'):                 
            comando = 'add_frase'
        elif subcomando.startswith('vomit'):
            comando = 'vomit'
        elif subcomando.startswith('del'):
            comando = 'del_frase'
    elif texto.startswith('hype'):
        comando = 'hype'
    elif ' ' in texto:
        comando = 'get_frase_numero'    
    elif texto == 'chamada':
        comando = 'chamada'
    else:
        comando = 'random'
    
    return comando

def verifica_chamada(base_url=None, chat_id=None):
    #verifica a necessidade de criar uma nova chamada
    check1 = check2 = ''

    if not cria_chamada(chat_id):
        check1 = 'Erro ao criar ou abrir a chamada'
        if chat_id == None:
            return check1
        else:
            reply(base_url, chat_id, check1)
    if len(abre_data('chamada')) == 0:
        check2 = 'Cadastrar alguem na chamada'
        if chat_id == None:
            return check2
        else:
            reply(base_url, chat_id, check2)
    else:
        return get_vomit('chamada')

def del_frase(text):
    # Ex: "pessoa_del 9"    
    pessoa = text.split('_', 1)[0]
    if not verifica_pessoa(pessoa):
        return 'Pessoa nao existe'
    data = abre_data(pessoa)

    if not ' ' in text:
        return 'Escolha um numero poxa vida'
    numero = text.split(' ', 1)[1]

    data = abre_data(pessoa)                
    tam = len(data)
    i = int(numero) - 1
    if 0 <= i < tam:
        deletada = data.pop(i)
        return '[' + deletada + ']' + ' excluida'
    else:
        return 'Tente outro numero amg'

def extrai_texto(message):
    try:        
        text = message.get('text')
        user = message['from']
        user_id = user['id']
        chat = message['chat']
        chat_id = chat['id']
    except KeyError as e:
        logging.error(e)
        logging.error('erro na chave da mensagem')
    return text, chat_id

def extrai_reply(message):
    try:
        if 'reply_to_message' in message:
            reply_to_message = message.get('reply_to_message')
            reply_msg_txt = reply_to_message['text']
            logging.info('encontrou reply_to_message: ' + reply_msg_txt)
            if 'sticker' in message:
                add_sticker = True
                sticker = message['sticker']
                sticker_id = sticker['file_id']
                logging.info('encontrou sticker: ' + sticker_id)
        return '/add_sticker', reply_msg_txt, sticker_id
        # if '_' in reply_msg_txt:
        #     pessoa = reply_msg_txt.split('_', 1)[0]
        # return '/add_sticker ' + reply_msg_txt + sticker_id
    except Exception as e:
        logging.info('not reply')
        return '','false', 'false'