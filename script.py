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
import sys
import nltk
from random import randint

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
    try:
        with open(folder_location + file_name) as f:
            data = json.load(f)
        return data
        log_it('Successfully Loaded Configuration.')
    except Exception as error:
        log_it('Error Loading Configuration.\n Error: {}'.format(error))


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


def handle_analyze_data(data):
    '''
    Handle and Analyze with SQL DB
    '''
    try:
        # Store Data
        mariadb_connection, cursor = init_database()
        truncate_if_exists(cursor)
        insert_list_to_db(data, cursor)
        mariadb_connection.commit()
        log_it('Committed Changes to Database Successfully.')

        # Analyze Data
        return stats(cursor)

        # Close Connections
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
            user=cfg['user'], password=cfg['password'], database=cfg['database'], use_unicode=True, charset="utf8")
        # mariadb.set_character_set('utf8')
        cursor = mariadb_connection.cursor(buffered=True)
        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
        log_it('Database Connection Successful.')
        return mariadb_connection, cursor
    except Exception as error:
        log_it('Connection to Database Failed.\nError: {}'.format(error))


def insert_list_to_db(data, cursor, database='data_store', properties=['predicate', 'subj', 'obj']):
    '''
    Given a list of tuples to db
    properties[0], properties[1], properties[2],
    '''
    ignore = set('``')
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


# ===================== Stats Calculation ================

def stats(cursor):
    '''
    Return a few stats about the paragraph text
    '''
    try:
        best_indi = best_subj_obj(cursor)
        relevant_concept = best_relevant_concept(cursor, best_indi[0])
        term_best_concept = best_concept(cursor)
        return [best_indi, relevant_concept, term_best_concept]

    except Exception as error:
        # exc_type, exc_obj, exc_tb = sys.exc_info()
        # print(exc_tb.tb_lineno)
        log_it('{}'.format(error))


def best_subj_obj(cursor):
    '''
    Fetches the best subject, object and predicate.
    '''
    try:
        # Extract the most important predicate
        predicates = {}
        cursor.execute(
            'SELECT `predicate`, COUNT(*) FROM data_store GROUP BY `predicate` ORDER BY COUNT(*) DESC LIMIT 10')
        for predicate, count in cursor:
            predicates[predicate] = count
        log_it('Extracted Best Predicates.')
    except mariadb.Error as error:
        log_it('Could Not Extract Best Predicates')

    try:
        # Extract the most important predicate
        subjects = {}
        cursor.execute(
            'SELECT `subj`, COUNT(*) FROM data_store GROUP BY `subj` ORDER BY COUNT(*) DESC LIMIT 10')
        for subject, count in cursor:
            subjects[subject] = count
        log_it('Extracted Best Subjects.')
    except mariadb.Error as error:
        log_it('Could Not Extract Best Subjects.')

    try:
        # Extract the most important predicate
        objects = {}
        cursor.execute(
            'SELECT `obj`, COUNT(*) FROM data_store GROUP BY `obj` ORDER BY COUNT(*) DESC LIMIT 10')
        for obj, count in cursor:
            objects[obj] = count
        log_it('Extracted Best Objects.')
    except mariadb.Error as error:
        log_it('Could Not Extract Best Objects.')

    all_terms = set(list(predicates.keys()) +
                    list(subjects.keys()) + list(objects.keys()))
    all_terms.remove(None)
    best_indi = []
    stop = set(nltk.corpus.stopwords.words('english'))
    best_term_count = -sys.maxsize
    best_term = ''
    try:
        for each_item in all_terms:
            current = 0
            if (each_item in predicates):
                current += predicates[each_item]
            if (each_item in subjects):
                current += subjects[each_item]
            if (each_item in objects):
                current += objects[each_item]

            tag = nltk.pos_tag([each_item])
            if (current > best_term_count and len(each_item) > 2 and each_item not in stop and tag[0][1].startswith('N')):
                best_term = each_item
                best_term_count = current

        best_indi = [best_term, best_term_count,
                     predicates, subjects, objects, all_terms]
        log_it('Extracted Best of All Successfully.')
    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(exc_tb.tb_lineno)
        log_it('Failed to Extract Best of All\n Error: {}'.format(error))
    return best_indi


def best_relevant_concept(cursor, relation, count=100):
    '''
    Extract Best Concept in Relations
    '''
    try:
        concepts = {}
        cursor.execute(
            'SELECT predicate, subj, obj, COUNT(*) FROM data_store WHERE predicate = %s OR subj = %s OR obj = %s GROUP BY predicate, subj, obj ORDER BY COUNT(*) DESC LIMIT %s', (relation, relation, relation, count))
        for predicate, subj, obj, count in cursor:
            key = ''
            if (predicate):
                key += predicate + ':'
            if (subj):
                key += subj + ':'
            if (obj):
                key += obj
            if (key):
                if (key[-1] == ':'):
                    key = key[:-1]
                if (key in concepts):
                    concepts[key] = concepts[key] + count
                else:
                    concepts[key] = count
        log_it('Extracted Best Concept')
        return concepts
    except mariadb.Error as error:
        log_it('Could Not Extract Best Concept')


def best_concept(cursor, count=100):
    '''
    It extracts the most important and meaningful concept
    '''
    try:
        concepts = {}
        cursor.execute(
            'SELECT `predicate`, `subj`, `obj`, COUNT(*) FROM data_store GROUP BY `predicate`, `subj`, `obj` ORDER BY COUNT(*) DESC LIMIT %s', (count,))
        for predicate, subj, obj, count in cursor:
            key = ''
            if (predicate):
                key += predicate + ':'
            if (subj):
                key += subj + ':'
            if (obj):
                key += obj
            if (key):
                if (key[-1] == ':'):
                    key = key[:-1]
                if (key in concepts):
                    concepts[key] = concepts[key] + count
                else:
                    concepts[key] = count
        log_it('Extracted Best Concept')
        return concepts
    except Exception as error:
        log_it('Could Not Extract Best Concept')
        print('{} '.format(error))

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
    subj_obj = [root, None, None]
    for each_dep in dependencies:
        if (each_dep['governorGloss'] == root):
            if ('sub' in each_dep['dep']):
                subj_obj[1] = each_dep['dependentGloss']
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


# =============== Templating =================

def templating(stats, data):
    '''
    Template Functions
    '''
    decision = elect_template(stats, data)
    display_template(stats, data, decision)


def is_person(data):
    '''
    Recognises whether if this a person or not.
    '''
    if (data != None):
        sentences = (
            ('properties', '{"timeout":70000, "annotators":"ner","outputFormat":"json"}'),)
        response = requests.post(
                'http://localhost:8081/', params=sentences, data=data)
        recognition = json.loads(response.text)
        recognition = recognition['sentences'][0]['tokens'][0]['ner']
        if (recognition != None and recognition.lower() == 'person'):
            return True
        else: return False

def elect_property(terms, ignore):
    '''
    Elect the highest concentration of person
    '''
    for each_item in terms:
        if (each_item != None and is_person(each_item) and each_item != ignore):
            return each_item

def display_template(stats, data, decision):
    '''
    Displays the elected template.
    '''
    file_data = readfile('template.json', './template/')
    data = json.loads(file_data)
    idx = randint(0, 1)
    if (decision.lower() == 'person'):
        data = data['person'][str(idx)]
    else:
        data = data['others'][str(idx)]

    term_best_concept = stats[2]
    relevant_concept = stats[1]
    best_indi = stats[0]

    other_people = set()
    other_people.add(elect_property(best_indi[2], stats[0][0]))
    other_people.add(elect_property(best_indi[3], stats[0][0]))
    other_people.add(elect_property(best_indi[4], stats[0][0]))
    other_people.remove(None)
    other_people = list(other_people)

    print(data % (stats[0][0], other_people[0]))

    if (len(other_people) > 1):
        print('This para additionally talks about %s but with a lower degree as compared to the above mentioned entities or conecpts.' % (other_people[1]))


def elect_template(stats, data):
    '''
    Elect the template based on stats and best concept.
    '''
    try:
        sentences = (
            ('properties', '{"timeout":70000, "annotators":"ner","outputFormat":"json"}'),)
        response = requests.post(
            'http://localhost:8081/', params=sentences, data=stats[0][0])
        recognition = json.loads(response.text)
        recognition = recognition['sentences'][0]['tokens'][0]['ner']
        log_it('Successfully Recognised the Type of Template')
        return recognition
        # dump_json(recognition, 'recognition.txt.json', './output/')
    except Exception as error:
        log_it('{}'.format(error))

# ============= Main Call ==============


def main():
    '''
    Main Calls the rolling function
    '''
    file_data = readfile('input4.txt', folder_location='./input/')
    # file_data = corpus.gutenberg.raw('austen-emma.txt').rstrip()
    # dump(file_data, 'jane-austenn-emma.txt', './input/')

    if (file_data != None):
        start = time()

        # First Break down into sentences and rebuild them
        sentences = (
            ('properties', '{"timeout":70000, "annotators":"ssplit","outputFormat":"json"}'),)
        response = requests.post(
            'http://localhost:8081/', params=sentences, data=file_data)
        data = json.loads(response.text)
        sentence_list = sentencify(data)
        # dump_json(data, 'intermediate.txt.json', './output/')

        # Resolve Anaphora
        anaphoras = (
            ('properties', '{"timeout":70000, "annotators":"coref","outputFormat":"json"}'),)
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
            ('properties', '{"timeout":70000, "annotators":"tokenize,ssplit,lemma,depparse,mention,ner","outputFormat":"json"}'),)
        response = requests.post(
            'http://localhost:8081/', params=params, data=update_input)
        data = json.loads(response.text)
        dump_json(data, 'output.txt.json', './output/')
        triples = extract_information(data)

        # Store them in MySQL now
        stats = handle_analyze_data(triples)

        # Just display the Template
        templating(stats, data)

        end = time()
        log_it(str(end - start) + ' seconds to complete the summarization.')

# ========= Boiler Plate Code ==========
if __name__ == '__main__':
    main()
