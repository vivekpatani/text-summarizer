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
            print('File Dumping Successful')
    except IOError:
        print('Error Dumping File')


def dump_json(data, file_name, folder_location):
    '''
    Dumps a JSON string to a file
    '''
    try:
        with open(folder_location + file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            print('JSON File Dumping Successful')
    except IOError:
        print('Error Dumping File')

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
        # refs[ref]['value'] = non_reps
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

    logit = str(count1) + "/" + str(count2) + " Anaphoras were resolved."
    dump(logit, 'output.log', './')
    return ' '.join(file_data)

# ================= Dependency Resolution ================


def extract_information(data):
    '''
    Pivot function to extract information.
    '''
    tags = extract_sentence(data['sentences'])
    # print(tags)


def extract_sentence(data):
    '''
    Extracting relevant dependencies
    Format : (sentence_number, relation_number, dsubj/nsubj, predicate, dobj/nobj)
    '''
    for each_sentence in data:
        idx = each_sentence['index']
        dependencies = each_sentence['enhancedPlusPlusDependencies']
        # print(dependencies)
        roots, ccomp = extract_roots(dependencies)


# def extract_subjs_objs()


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
        dump(update_input, 'intermediate.txt', './output/')

        # Store Dependencies in SQL
        params = (
            ('properties', '{"timeout":50000, "annotators":"tokenize,ssplit,lemma,depparse,mention","outputFormat":"json"}'),)
        response = requests.post(
            'http://localhost:8081/', params=params, data=update_input)
        data = json.loads(response.text)
        dump_json(data, 'output.txt.json', './output/')
        extract_information(data)
        end = time()
        print(end - start)

# ========= Boiler Plate Code ==========
if __name__ == '__main__':
    main()
