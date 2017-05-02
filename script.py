#!/usr/bin/env python
# -*- coding: utf-8 -*-

# =============== Imports ==============
from nltk.tokenize import sent_tokenize
from nltk import corpus
import requests
import json
from subprocess import call
from time import time
import copy
import string
import mysql.connector as mariadb

# =========== Globals & Costants =============

# ========== Read/Write File Calls ===========


def readfile(file_name, folder_location):
    '''
    Reads the file and returns a single
    string.
    '''
    try:
        with open(folder_location + file_name, encoding='utf-8') as f:
            data = f.read().rstrip()
        return data
    except IOError:
        print('No File Found.')


def dump(data, file_name, folder_location):
    '''
    Dump a string to a file
    '''
    try:
        with open(folder_location + file_name, 'w', encoding='utf-8') as f:
            f.write(data)
    except IOError:
        log_it('Error Dumping File')


def dump_json(data, file_name, folder_location):
    '''
    Dumps a JSON string to a file
    '''
    try:
        with open(folder_location + file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except IOError:
        log_it('Error Dumping File')

def read_config(file_name='config.json', folder_location='./'):
	'''
	Read config from config.json
	'''
	data = ''
	with open(folder_location + file_name) as f:
		data = json.loads(f)
	return data

def log_it(text, file_name='output.log', folder_location='./'):
    '''
    Logs output to output.log
    '''
    try:
        with open(folder_location + file_name, 'a', encoding='utf-8') as f:
            f.write(text + '\n')
    except:
        print('Error')

# ================== Manipulate Information ==============

# ================= Resolve Anaphora =====================


def sentencify(data):
    '''
    Take the data and sentencify it.
    '''
    sentence_list = []
    data = data['sentences']
    for each_item in data:
        tokens = each_item['tokens']
        word_list = []
        for each_word in tokens:
            if (len(word_list) > 0 and each_word['word'] in string.punctuation):
                word_list[-1] = word_list[-1] + each_word['word']
            else:
                word_list.append(each_word['word'])
        sentence_list.append(' '.join(word_list))
    return sentence_list


def resolve_anaphoras(data):
    '''
    Extract all the anaphoras.
    '''
    refs = {}
    data = data['corefs']
    for ref in data:
        # Non representatives are items which itself do not represent
        # an entity, but are linked.
        refs[ref] = {}
        for sub_ref in data[ref]:
            if (sub_ref['isRepresentativeMention']):
                refs[ref]['keymention'] = sub_ref['text']
            else:
                if (sub_ref['text'] in refs[ref]):
                    non_reps = refs[ref][sub_ref['text']]
                    non_reps.append(
                        ((int(sub_ref['sentNum'] - 1), int(sub_ref['startIndex'] - 1))))
                else:
                    refs[ref][sub_ref['text']] = [
                        (int(sub_ref['sentNum'] - 1), int(sub_ref['startIndex'] - 1))]
    return refs


def update_anaphoras(file_data, data):
    '''
    Generates a new interim file,
    with resolved anaphora.
    '''
    count2 = 0
    count1 = 0
    for anaphora in data:
        if ('keymention' in data[anaphora]):
            word = data[anaphora]['keymention']
            del data[anaphora]['keymention']

            for dependencies in data[anaphora]:

                for each_dep in data[anaphora][dependencies]:
                    flag = True
                    if (each_dep[0] > 0 and each_dep[0] < len(file_data)):
                        sentence = file_data[each_dep[0]].split()
                        word_idx = each_dep[1]

                        if (word_idx < len(sentence) and sentence[word_idx] == dependencies):
                            sentence[word_idx] = word

                        elif (word_idx - 1 >= 0 and word_idx < len(sentence) and sentence[word_idx - 1] == dependencies):
                            sentence[word_idx - 1] = word

                        elif (word_idx + 1 < len(sentence) and word_idx < len(sentence) and sentence[word_idx + 1] == dependencies):
                            sentence[word_idx + 1] = word

                        else:
                            count2 += 1
                            flag = False

                        if (flag):
                            count1 += 1
                            joined_s = ' '.join(sentence)
                            file_data[each_dep[0]] = joined_s
                    else:
                        count2 += 1

    log_it(str(count1) + '/' + str(count2) + ' Anaphoras were resolved.')
    return ' '.join(file_data)

# ======================= Database Calls =================


def push_data(data):
    '''
    Push Data to SQL DB
    '''
    try:
        mariadb_connection, cursor = init_database()
        truncate_if_exists(cursor)
        insert_list_to_db(data, cursor)
        mariadb_connection.commit()
        log_it('Committed Changes to Database Successfully.')
        mariadb_connection.close()
        log_it('Connection to Database Closed.')

    except Exception as error:
        log_it('Database is in a broken state.\nError: {}'.format(error))


def init_database():
    '''
    Initiates Database.
    '''
    cfg = read_config()
    try:
        mariadb_connection = mariadb.connect(
            user=cfg['user'], password=cfg['password'], database=cfg['database'])
        cursor = mariadb_connection.cursor(buffered=True)
        log_it('Database Connection Successful.')
        return mariadb_connection, cursor
    except:
        log_it('Connection to db Failed')


def insert_list_to_db(data, cursor, database='data_store', properties=['predicate', 'subj', 'obj']):
    '''
    Given a list of tuples to db
    properties[0], properties[1], properties[2],
    '''
    try:
        for each_item in data:
            cursor.execute('INSERT INTO data_store (predicate,subj,obj) VALUES (%s, %s, %s)', (each_item[
                           0], each_item[1], each_item[2]))
        log_it('Data was inserted.')
    except mariadb.Error as error:
        log_it('Failed to Insert Data.\nError: {}'.format(error))


def truncate_if_exists(cursor):
    try:
        cursor.execute("TRUNCATE TABLE data_store")
        log_it('Truncation Successful.')
    except:
        log_it('Could not truncate table.')


def print_cursor(cursor):
    '''
    Print cursor
    '''
    print(cursor)

# ================= Dependency Resolution ================


def extract_information(data):
    '''
    Pivot function to extract information.
    '''
    relations = extract_sentence(data['sentences'])
    return relations


def extract_sentence(data):
    '''
    Extracting relevant dependencies
    Format : (sentence_number, relation_number, dsubj/nsubj, predicate, dobj/nobj)
    '''
    relations = []
    for each_sentence in data:
        idx = each_sentence['index']
        dependencies = each_sentence['enhancedPlusPlusDependencies']
        # print(dependencies)
        roots, ccomp = extract_roots(dependencies)
        for root in roots:
            relations.append(extract_subjs_objs(dependencies, root))
    return relations


def extract_subjs_objs(dependencies, root):
    '''
    Extract all the objects for that ROOT
    '''
    subj_obj = [None, root, None]
    for each_dep in dependencies:
        if (each_dep['governorGloss'] == root):
            if ('sub' in each_dep['dep']):
                subj_obj[0] = each_dep['dependentGloss']
            elif ('obj' in each_dep['dep']):
                subj_obj[2] = each_dep['dependentGloss']
    return subj_obj


def extract_roots(data):
    '''
    Returns a list of roots in a given sentence.
    '''
    roots = []
    ccomp = []
    for each_dep in data:
        # print(each_dep['dep'])
        if (each_dep['dep'].upper() == 'ROOT'):
            roots.append(each_dep['dependentGloss'])
        if (each_dep['dep'].lower() == 'ccomp'):
            ccomp.append(each_dep['dependentGloss'])
    return roots, ccomp

# ============= Main Call ==============


def main():
    '''
    Main Calls the rolling function
    '''
    file_data = readfile('input.txt', folder_location='./input/')
    # file_data = corpus.gutenberg.raw('austen-emma.txt').rstrip()
    # dump(file_data, 'jane-austenn-emma.txt', './input/')

    if (file_data != None):
        start = time()

        # First Break down into sentences and rebuild them
        sentences = (
            ('properties', '{"timeout":50000, "annotators":"ssplit","outputFormat":"json"}'),)
        response = requests.post(
            'http://localhost:8081/', params=sentences, data=file_data)
        data = json.loads(response.text)
        sentence_list = sentencify(data)
        # dump_json(data, 'intermediate.txt.json', './output/')

        # Resolve Anaphora
        anaphoras = (
            ('properties', '{"timeout":50000, "annotators":"coref","outputFormat":"json"}'),)
        response = requests.post(
            'http://localhost:8081/', params=anaphoras, data=file_data)
        data = json.loads(response.text)
        # dump_json(data, 'intermediate.txt.json', './output/')
        extracted_anaphoras = resolve_anaphoras(data)
        sent_tokenize_list = sent_tokenize(file_data)
        update_input = update_anaphoras(
            sent_tokenize_list, extracted_anaphoras)
        # dump(update_input, 'intermediate.txt', './output/')

        # Parse all the sentences and extract triples
        params = (
            ('properties', '{"timeout":50000, "annotators":"tokenize,ssplit,lemma,depparse,mention","outputFormat":"json"}'),)
        response = requests.post(
            'http://localhost:8081/', params=params, data=update_input)
        data = json.loads(response.text)
        dump_json(data, 'output.txt.json', './output/')
        triples = extract_information(data)

        # Store them in MySQL now
        push_data(triples)

        end = time()
        log_it(str(end - start) + ' seconds to complete the summarization.')

# ========= Boiler Plate Code ==========
if __name__ == '__main__':
    main()
